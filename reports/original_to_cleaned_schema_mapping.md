# PatentGraph AI — Original-to-Cleaned Schema Mapping

| Original InPASS Field | Standardized Snake-Case Field | Data Type | Transformation & Validation Logic |
| :--- | :--- | :--- | :--- |
| `APPLICATION_NUMBER` | `patent_id` | String / Inferred | strip whitespace, preserve string formatting, validate uniqueness |
| `PUBLICATION_NUMBER` | `publication_number` | String / Inferred | strip whitespace, preserve journal issue format |
| `PUBLICATION_DATE` | `publication_date` | String / Inferred | parse DD/MM/YYYY into ISO 8601 YYYY-MM-DD |
| `DATE_OF_FILING` | `filing_date` | String / Inferred | parse DD/MM/YYYY into ISO 8601 YYYY-MM-DD |
| `DATE_UPDATED_d_m_y` | `date_updated` | String / Inferred | parse DD/MM/YYYY into ISO 8601 YYYY-MM-DD |
| `TITLE_OF_INVENTION` | `title` | String / Inferred | Unicode NFKC normalization, strip outer quotes and trailing punctuation, preserve scientific symbols, collapse whitespace |
| `FIELD_OF_INVENTION` | `field_of_invention` | String / Inferred | standardize uppercase, fill missing with 'UNCATEGORIZED', set field_imputed flag |
| `IPO_LOCATION` | `ipo_location` | String / Inferred | normalize to title case ('Delhi', 'Chennai', 'Kolkata', 'Mumbai'), derive ipo_code |
| `APPLICATION_TYPE_DESC` | `application_type` | String / Inferred | title-case description, derive high-level application_category |
| `NO_OF_PAGES` | `no_of_pages` | String / Inferred | cast to nullable Int64, generate field-median imputed variant |
| `NO_OF_CLAIMS` | `no_of_claims` | String / Inferred | cast to nullable Int64, generate field-median imputed variant and claims_range |
| *(Derived)* | `title_normalized` | String | Lowercase normalized title for search indexing |
| *(Derived)* | `filing_year` | Integer | Year extracted from `DATE_OF_FILING` |
| *(Derived)* | `publication_year` | Integer | Year extracted from `PUBLICATION_DATE` |
| *(Derived)* | `pendency_days` | Integer | Grant turnaround duration in days (`publication_date - filing_date`) |
| *(Derived)* | `ipo_code` | String (3 chars) | Branch office abbreviation code (`DEL`, `CHE`, `KOL`, `MUM`) |
| *(Derived)* | `application_category` | Categorical | High-level procedure category (`PCT National Phase`, `Ordinary`, etc.) |
| *(Derived)* | `field_imputed` | Boolean | True if technology domain was missing in raw data |
| *(Derived)* | `claims_range` | Categorical | Binned claim scope tier (`1-5`, `6-15`, `16-30`, `30+`) |
| *(Derived)* | `no_of_pages_imputed` | Integer | Missing values imputed with domain median |
| *(Derived)* | `no_of_claims_imputed` | Integer | Missing values imputed with domain median |
| *(Derived)* | `jurisdiction` | String | Static jurisdiction identifier (`India`) |
| *(Derived)* | `source_file` | String | Provenance tracking raw CSV filename |
| *(Derived)* | `source_url` | String | Official IPO public search verification link |
| *(Derived)* | `search_text` | String | Multi-attribute composite text for hybrid vector and keyword retrieval |
