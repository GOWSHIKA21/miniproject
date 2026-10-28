import re
from typing import List, Optional, Tuple, Dict, Any

# Domain synonym dictionary mapping common/colloquial terms to formal Indian patent gazette terminology
DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    "farming": ["farming", "agriculture", "agricultural", "crop", "cultivation", "harvester", "farm"],
    "agriculture": ["agriculture", "agricultural", "farming", "crop", "cultivation", "harvester", "tillage"],
    "crop cultivation": ["crop", "cultivation", "agriculture", "farming", "plant", "harvest", "seed", "tillage"],
    "agricultural machinery": ["agricultural", "machinery", "tractor", "harvester", "tiller", "mower", "farm", "plow"],
    "irrigation systems": ["irrigation", "watering", "sprinkler", "drip", "pump", "water", "supply", "drainage"],
    "irrigation": ["irrigation", "watering", "sprinkler", "drip", "pump", "water", "drainage"],
    "plant disease detection": ["plant", "disease", "detection", "crop", "pathogen", "fungal", "pest", "infestation", "agricultural"],
    "plant disease": ["plant", "disease", "crop", "pathogen", "pest", "infestation", "agricultural"],
    "renewable energy": ["renewable", "energy", "solar", "wind", "photovoltaic", "biomass", "power", "generation"],
    "solar": ["solar", "photovoltaic", "solar cell", "solar panel", "sun"],
    "machine learning": ["machine learning", "artificial intelligence", "neural network", "deep learning", "pattern recognition", "algorithm"],
    "artificial intelligence": ["artificial intelligence", "machine learning", "neural network", "deep learning"],
    "ai": ["artificial intelligence", "machine learning", "neural network"],
    "hydroponics": ["hydroponics", "controlled environment", "agriculture", "soilless", "cultivation", "nutrient"],
    "pharmaceutical": ["pharmaceutical", "drug", "medicine", "formulation", "dosage", "composition", "therapeutic", "container"],
    "battery": ["battery", "energy storage", "lithium", "cell", "electrode", "electrolyte"],
    "wind energy": ["wind", "turbine", "wind energy", "generator", "rotor", "blade"],
}

# Regex patterns for exact patent identifiers
PATENT_ID_REGEX = re.compile(r"^\s*(\d{1,5}/[A-Z]{3,5}/\d{4}|\d{4}/[A-Z]{3,5}/\d{4}|\d{12})\s*$", re.IGNORECASE)
PUB_NUM_REGEX = re.compile(r"^\s*(\d{1,4}/\d{4})\s*$", re.IGNORECASE)

# Conversational prefixes to strip for natural language questions
NL_PREFIXES = [
    r"^which patents are related to\s+",
    r"^what patents exist for\s+",
    r"^show me patents for\s+",
    r"^show me patents related to\s+",
    r"^tell me about patents for\s+",
    r"^tell me about\s+",
    r"^find patents on\s+",
    r"^find patents related to\s+",
    r"^search for patents on\s+",
    r"^search for patents related to\s+",
    r"^search for\s+",
    r"^can you show patents on\s+",
    r"^can you explain patents on\s+",
    r"^what is known about\s+",
    r"^patents related to\s+",
    r"^patents on\s+",
    r"^patents for\s+",
    r"^patents about\s+"
]

def clean_nl_query(query: str) -> str:
    """Strip conversational question prefixes to isolate technical core keywords."""
    cleaned = query.strip()
    for prefix in NL_PREFIXES:
        cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE).strip()
    # Strip trailing question mark or punctuation
    cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()
    return cleaned if cleaned else query.strip()

def detect_exact_identifier(query: str) -> Optional[Tuple[str, str]]:
    """
    Returns (identifier_type, cleaned_value) if query matches an exact patent identifier.
    identifier_type: 'patent_id' or 'publication_number'
    """
    q = query.strip()
    p_match = PATENT_ID_REGEX.match(q)
    if p_match:
        return ("patent_id", p_match.group(1).upper())
    
    pub_match = PUB_NUM_REGEX.match(q)
    if pub_match:
        return ("publication_number", pub_match.group(1))
    
    return None

def expand_query_terms(query: str) -> List[str]:
    """
    Expand a query string with domain synonyms for robust lexical/BM25 recall.
    Returns list of expanded tokens/terms.
    """
    q_lower = query.lower().strip()
    expanded_set = set(re.findall(r"\b[a-zA-Z0-9]{2,}\b", q_lower))

    # 1. Check multi-word phrase matches
    for phrase, synonyms in DOMAIN_SYNONYMS.items():
        if phrase in q_lower:
            for syn in synonyms:
                for token in re.findall(r"\b[a-zA-Z0-9]{2,}\b", syn):
                    expanded_set.add(token.lower())

    # 2. Check individual word matches
    words = q_lower.split()
    for w in words:
        if w in DOMAIN_SYNONYMS:
            for syn in DOMAIN_SYNONYMS[w]:
                for token in re.findall(r"\b[a-zA-Z0-9]{2,}\b", syn):
                    expanded_set.add(token.lower())

    return list(expanded_set)

def get_expanded_search_query(query: str) -> str:
    """Generate a combined query string suitable for vector and BM25 search."""
    cleaned_core = clean_nl_query(query)
    expanded_tokens = expand_query_terms(cleaned_core)
    
    # Keep core query prominent, append expanded tokens
    unique_tokens = []
    seen = set()
    for tok in cleaned_core.split() + expanded_tokens:
        tok_clean = tok.strip().lower()
        if tok_clean and tok_clean not in seen and len(tok_clean) > 1:
            seen.add(tok_clean)
            unique_tokens.append(tok_clean)
            
    return " ".join(unique_tokens)
