# PatentGraph AI — Standardized Data Dictionary

This data dictionary defines all 25 attributes present in the cleaned and standardized patent corpus (`cleaned_patents_consolidated.parquet`).

| Attribute Name | Data Type | Nullable | Description | Example Value |
| :--- | :--- | :---: | :--- | :--- |
| `patent_id` | `string` | No | Unique canonical patent application number issued by the Indian Patent Office (e.g., '10/DEL/2010', '1005/MUMNP/2007'). | `10/DEL/2010` |
| `publication_number` | `string` | Yes | InPASS gazette journal publication issue identifier (e.g., '01/2016'). | `01/2016` |
| `publication_date` | `string (ISO 8601 YYYY-MM-DD)` | No | Date on which the granted patent was published in the official patent journal. | `2016-01-01` |
| `filing_date` | `string (ISO 8601 YYYY-MM-DD)` | No | Date of formal patent application filing with the Indian Patent Office. | `2010-01-04` |
| `date_updated` | `string (ISO 8601 YYYY-MM-DD)` | Yes | Last database update timestamp recorded in InPASS. | `2023-04-19` |
| `filing_year` | `integer` | No | Calendar year derived from filing_date. | `2010` |
| `publication_year` | `integer` | No | Calendar year derived from publication_date. | `2016` |
| `pendency_days` | `integer` | Yes | Elapsed duration in days between application filing and gazette publication (grant notification). | `2188` |
| `title` | `string` | No | Cleaned invention title with normalized Unicode, outer quotes stripped, and scientific symbols preserved. | `Production of a Pharmaceutical Container from the Melt` |
| `title_normalized` | `string` | No | Lowercase normalized title optimized for search tokenization and keyword matching. | `production of a pharmaceutical container from the melt` |
| `field_of_invention` | `string (categorical)` | No | Standardized technology classification assigned by IPO (e.g., CHEMISTRY, MECHANICAL, ELECTRONICS, or UNCATEGORIZED). | `CHEMISTRY` |
| `field_imputed` | `boolean` | No | Indicator flag specifying if field_of_invention was missing in source and assigned 'UNCATEGORIZED'. | `False` |
| `ipo_location` | `string (categorical)` | No | Indian Patent Office branch jurisdiction: Delhi, Chennai, Kolkata, or Mumbai. | `Delhi` |
| `ipo_code` | `string (categorical)` | No | Standard 3-letter branch code abbreviation: DEL, CHE, KOL, or MUM. | `DEL` |
| `application_type` | `string (categorical)` | No | Title-cased official application procedure description (e.g. 'Pct National Phase Application'). | `Convention Application` |
| `application_category` | `string (categorical)` | No | High-level procedure category: 'PCT National Phase', 'Ordinary', 'Convention', 'Divisional', or 'Patent of Addition'. | `Convention` |
| `no_of_pages` | `integer (nullable)` | Yes | Exact number of pages in patent specification. Retains null if missing. | `25` |
| `no_of_claims` | `integer (nullable)` | Yes | Exact number of granted claims. Retains null if missing. | `24` |
| `no_of_pages_imputed` | `integer` | No | ML feature with missing page counts imputed using technology field median. | `25` |
| `no_of_claims_imputed` | `integer` | No | ML feature with missing claim counts imputed using technology field median. | `24` |
| `claims_range` | `string (categorical)` | No | Binned claim scope category: '1-5 claims', '6-15 claims', '16-30 claims', '30+ claims', or 'Unknown'. | `16-30 claims` |
| `jurisdiction` | `string` | No | National patent jurisdiction constant ('India'). | `India` |
| `source_file` | `string` | No | Name of the raw InPASS CSV file from which the patent record originated. | `application_details_granted_2016.csv` |
| `source_url` | `string` | No | Official verification URL for IPO public search portal. | `https://ipindiaservices.gov.in/publicsearch/` |
| `search_text` | `string` | No | Unified semantic representation combining title, field, jurisdiction, type, and timeline for hybrid retrieval. | `Production of a Pharmaceutical Container from the Melt. Technical Field: CHEMISTRY...` |
