# PatentGraph AI — Data Cleaning & Standardization Log

**Execution Timestamp**: `2026-10-26T22:34:16.901560`  
**Corpus Input**: 8 Annual InPASS CSV Datasets (2016–2023)  
**Total Records Processed**: `151,439`  
**Valid Records Retained**: `151,438`  
**Corrupted / Quarantined Records**: `1`  

---

## Transformations Applied

### 1. Primary Key Identifier Normalization
- **Field**: `APPLICATION_NUMBER` -> `patent_id`.
- **Integrity Policy**: Preserved strictly as string primitives to maintain slashes, branch prefixes (`DEL`, `DELNP`, `MUM`, `MUMNP`, `CHE`, `CHENP`, `KOL`, `KOLNP`), and leading zeros.
- **Uniqueness Verification**: 100% unique primary keys across the entire 151,438 record corpus.

### 2. Title Text & Unicode Normalization
- **Field**: `TITLE_OF_INVENTION` -> `title`, `title_normalized`.
- **Unicode Handling**: Applied `unicodedata.normalize('NFKC')` to standardize all character representations.
- **Artifact Removal**: Stripped corrupt byte markers (`�`), soft hyphens (`­`), and converted non-breaking spaces (` `) to standard whitespace.
- **Quotation Stripping**: Stripped wrapping outer quotes (`"`, `'`, `“`, `”`, `‘`, `’`) that enclosed raw titles.
- **Scientific Notation Preservation**: Explicitly preserved technical symbols (`°` degrees, `±` tolerance, `µ` micro, `ß` chemical notations, dashes, and formulas).
- **Normalization**: Generated `title_normalized` in lowercase for fast tokenization.

### 3. Date Standardization & Temporal Derivations
- **Fields**: `DATE_OF_FILING`, `PUBLICATION_DATE`, `DATE_UPDATED_d_m_y` -> `filing_date`, `publication_date`, `date_updated`.
- **Format**: Transformed from Indian format (`DD/MM/YYYY`) to ISO 8601 standard (`YYYY-MM-DD`).
- **Temporal Features Derived**:
  - `filing_year`: Year of filing (1996 to 2022).
  - `publication_year`: Year of grant gazette publication (2016 to 2023).
  - `pendency_days`: Exact grant turnaround duration (`publication_date - filing_date` in days).

### 4. Jurisdiction & Categorical Classification
- **Fields**: `IPO_LOCATION`, `APPLICATION_TYPE_DESC`, `FIELD_OF_INVENTION`.
- **IPO Branches**: Standardized to title case (`Delhi`, `Chennai`, `Kolkata`, `Mumbai`) and derived 3-letter codes (`DEL`, `CHE`, `KOL`, `MUM`).
- **Application Procedure**: Standardized type description and mapped into 5 major categories: `PCT National Phase`, `Ordinary`, `Convention`, `Divisional`, `Patent of Addition`.
- **Technology Domain**: Standardized into 15 official disciplines. 225 records with missing field assigned `UNCATEGORIZED` with flag `field_imputed = True`.

### 5. Quantitative Attributes & Feature Imputation
- **Fields**: `NO_OF_PAGES`, `NO_OF_CLAIMS`.
- **Type Conversion**: Converted to integer values (`Int64`). Nulls preserved in primary columns.
- **Imputation for ML**: Created `no_of_pages_imputed` and `no_of_claims_imputed` using domain medians.
- **Scope Categorization**: Generated `claims_range` (`1-5 claims`, `6-15 claims`, `16-30 claims`, `30+ claims`).

### 6. Retrieval & Search Text Synthesis
- **Field**: `search_text`.
- Synthesized unified natural language representation containing title, domain, branch office, procedure type, claims count, and timeline for hybrid BM25 + FAISS retrieval.
