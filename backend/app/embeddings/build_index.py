import os
import sys
import json
import pickle
import logging
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
import faiss
from rank_bm25 import BM25Okapi

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from backend.app.config import settings
from backend.app.embeddings.embedding_model import get_embedding_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def tokenize(text: str):
    return [w.lower() for w in text.split() if len(w) > 1]

def build_indices(limit: int = 15000, batch_size: int = 256):
    data_path = settings.CLEANED_DATA_PATH
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}. Run clean_data.py first.")

    logger.info(f"Loading cleaned patents from {data_path}...")
    df = pd.read_parquet(data_path)
    total_available = len(df)
    logger.info(f"Total available patents: {total_available:,}")

    if limit and 0 < limit < total_available:
        # Balanced sampling across publication years
        df["pub_year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year.fillna(2017).astype(int)
        sampled_dfs = []
        target_per_year = limit // max(df["pub_year"].nunique(), 1)
        for yr, group in df.groupby("pub_year"):
            sampled_dfs.append(group.sample(n=min(len(group), target_per_year), random_state=42))
        indexed_df = pd.concat(sampled_dfs, ignore_index=True)
        # If slight difference due to rounding, sample remaining
        if len(indexed_df) < limit:
            remaining = df[~df["patent_id"].isin(indexed_df["patent_id"])]
            more = remaining.sample(n=min(len(remaining), limit - len(indexed_df)), random_state=42)
            indexed_df = pd.concat([indexed_df, more], ignore_index=True)
        logger.info(f"Sampled representative set of {len(indexed_df):,} patents across years ({df['pub_year'].min()}-{df['pub_year'].max()})")
    else:
        indexed_df = df
        logger.info(f"Indexing full review dataset of {len(indexed_df):,} patents")

    # Texts for embedding and BM25
    texts = indexed_df["search_text"].tolist()
    patent_ids = indexed_df["patent_id"].tolist()

    # 1. Build FAISS Index
    logger.info("Initializing Sentence Transformer model...")
    embed_model = get_embedding_model()
    dim = embed_model.dimension

    logger.info(f"Generating embeddings for {len(texts):,} patents (dim={dim}, batch_size={batch_size})...")
    embeddings = embed_model.encode(texts, batch_size=batch_size, show_progress=True)

    logger.info("Building FAISS IndexFlatIP (cosine similarity on normalized vectors)...")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    logger.info(f"FAISS index built. Total indexed vectors: {index.ntotal:,}")

    # Persist FAISS Index
    os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, settings.FAISS_INDEX_PATH)
    logger.info(f"Saved FAISS index to {settings.FAISS_INDEX_PATH}")

    # Build and persist ID map
    id_map = {
        "index_to_patent_id": {str(i): pid for i, pid in enumerate(patent_ids)},
        "patent_id_to_index": {pid: i for i, pid in enumerate(patent_ids)},
        "total": len(patent_ids),
        "created_at": datetime.now().isoformat(),
        "model": settings.EMBEDDING_MODEL_NAME,
        "dimension": dim
    }
    with open(settings.FAISS_ID_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(id_map, f, indent=2)
    logger.info(f"Saved FAISS ID map to {settings.FAISS_ID_MAP_PATH}")

    # 2. Build BM25 Keyword Index
    logger.info("Building BM25 keyword index...")
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized_corpus)

    bm25_payload = {
        "bm25": bm25,
        "patent_ids": patent_ids,
        "texts": texts,
        "created_at": datetime.now().isoformat()
    }
    with open(settings.BM25_INDEX_PATH, "wb") as f:
        pickle.dump(bm25_payload, f)
    logger.info(f"Saved BM25 index to {settings.BM25_INDEX_PATH}")

    # Configuration metadata
    config_meta = {
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "dimension": dim,
        "total_indexed": len(patent_ids),
        "index_type": "IndexFlatIP",
        "metric": "cosine_similarity",
        "faiss_file": settings.FAISS_INDEX_PATH,
        "bm25_file": settings.BM25_INDEX_PATH,
        "timestamp": datetime.now().isoformat()
    }
    config_filename = "indexing_config_2016_2018.json" if "2016_2018" in settings.FAISS_INDEX_PATH else "indexing_config.json"
    config_path = os.path.join(os.path.dirname(settings.FAISS_INDEX_PATH), config_filename)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_meta, f, indent=2)

    logger.info("Indexing completed successfully!")
    return config_meta

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Number of patents to index (0 for all 33,825 patents)")
    args = parser.parse_args()
    build_indices(limit=args.limit)
