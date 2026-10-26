# PatentGraph AI — Source Corpus Inventory & Audit Report

**Audit Execution Time**: `2026-10-26T22:33:32.417340`  
**Corpus Location**: `C:\Users\gowsh\OneDrive\Desktop\RAG\miniproject\dataset`  
**Total Source CSV Files**: `8`  
**Total Raw Records**: `151,439`  
**Valid Records Identified**: `151,438`  
**Corrupted / Quarantined Records**: `1`  

---

## 1. Source Files Overview

| Source File | File Size (Bytes) | SHA-256 Checksum (Prefix) | Raw Rows | Columns | Filing Date Span | Publication Date Span |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `application_details_granted_2016.csv` | 1,585,834 | `eee340ef7599...` | 8,064 | 11 | 01/01/2008 to 31/12/2010 | 01/01/2016 to 30/12/2016 |
| `application_details_granted_2017.csv` | 2,412,714 | `e02dfe463109...` | 12,306 | 11 | 01/01/2003 to 31/12/2012 | 01/09/2017 to 31/03/2017 |
| `application_details_granted_2018.csv` | 2,636,222 | `d55186cd2b43...` | 13,455 | 11 | 01/01/2008 to 31/12/2013 | 01/06/2018 to 31/08/2018 |
| `application_details_granted_2019.csv` | 4,425,056 | `7b606c738abd...` | 22,695 | 11 | 01/01/2008 to 31/12/2015 | 01/02/2019 to 31/05/2019 |
| `application_details_granted_2020.csv` | 4,729,189 | `b77d38bb723a...` | 24,465 | 11 | 01/01/2008 to 31/12/2018 | 01/05/2020 to 31/07/2020 |
| `application_details_granted_2021.csv` | 5,571,525 | `7acadd121f4f...` | 28,971 | 11 | 01/01/2010 to 31/12/2019 | 01/01/2021 to 31/12/2021 |
| `application_details_granted_2022.csv` | 5,848,572 | `5faf9751eb47...` | 30,499 | 11 | 01/01/2013 to 31/12/2021 | 01/04/2022 to 30/12/2022 |
| `application_details_granted_2023.csv` | 2,106,314 | `9ec4bf1da47a...` | 10,984 | 11 | 01/01/2013 to 31/12/2021 | 03/02/2023 to 31/03/2023 |

---

## 2. Source Schema (11 Official InPASS Columns)

| Index | Column Name | Raw Inferred Type | Non-Null Count | Null Count | Description |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `PUBLICATION_NUMBER` | String | 151,439 | 0 | InPASS journal issue number (e.g. `01/2016`) |
| 2 | `PUBLICATION_DATE` | Date (DD/MM/YYYY) | 151,439 | 0 | Official gazette publication date |
| 3 | `IPO_LOCATION` | String | 151,439 | 0 | Indian Patent Office jurisdiction branch |
| 4 | `APPLICATION_TYPE_DESC` | String | 151,439 | 0 | Patent application procedure type |
| 5 | `APPLICATION_NUMBER` | String (Identifier) | 151,439 | 0 | Canonical patent application reference ID |
| 6 | `DATE_OF_FILING` | Date (DD/MM/YYYY) | 151,439 | 0 | Date patent was formally lodged with IPO |
| 7 | `TITLE_OF_INVENTION` | Text | 151,438 | 1 | Formal title of the claimed invention |
| 8 | `FIELD_OF_INVENTION` | Categorical | 151,214 | 225 | Technology classification assigned by IPO |
| 9 | `NO_OF_PAGES` | Integer | 151,309 | 130 | Number of specification pages |
| 10 | `NO_OF_CLAIMS` | Integer | 151,219 | 220 | Number of granted patent claims |
| 11 | `DATE_UPDATED_d_m_y` | Date (DD/MM/YYYY) | 151,439 | 0 | InPASS database export update timestamp |

---

## 3. Data Quality & Integrity Findings

### 3.1 Uniqueness & Identifiers
- **Exact Duplicate Rows across corpus**: `0` (0 duplicate rows).
- **Duplicate `APPLICATION_NUMBER` across corpus**: `0` (Every record has an entirely unique application identifier).
- **Preservation of Leading Zeros & Slashes**: Application numbers contain essential slashes (e.g. `10/DEL/2010`) and branch tokens (`MUMNP`, `DELNP`, `CHENP`, `KOLNP`). These are strictly preserved as string primitives.

### 3.2 Quarantined Corrupted Records
Exactly `1` record was flagged as invalid and scheduled for quarantine separation:
- **Application Number**: `3568/MUMNP/2015`
  - **Source File**: `application_details_granted_2021.csv` (Row Index: 109350)
  - **Filing Date**: `15/12/2015` | **Publication Date**: `24/12/2021`
  - **Field**: `POLYMER`
  - **Title**: `nan`
  - **Reason for Quarantine**: Missing or invalid TITLE_OF_INVENTION (< 3 chars or null)

### 3.3 Date Consistency & Temporal Profile
- **Earliest Filing Date**: `1996-06-13`
- **Latest Filing Date**: `2022-09-17`
- **Earliest Gazette Publication Date**: `2016-01-01`
- **Latest Gazette Publication Date**: `2023-03-31`
- **Unparsable Filing Dates**: `0`
- **Unparsable Publication Dates**: `0`
- **Inverted Dates (Publication < Filing)**: `0` (All chronological relationships are valid).

### 3.4 Numerical Range & Outlier Profile
- **`NO_OF_PAGES`**: Min = `1.0`, Median = `29.0`, Max = `6786.0`, Missing = `130`.
- **`NO_OF_CLAIMS`**: Min = `1.0`, Median = `15.0`, Max = `407.0`, Missing = `220`.

### 3.5 Categorical Breakdown

#### IPO Jurisdiction Branch Distribution
| IPO Branch | Patent Records | Percentage |
| :--- | :---: | :---: |
| Delhi | 57,345 | 37.87% |
| Chennai | 48,987 | 32.35% |
| Kolkata | 23,368 | 15.43% |
| Mumbai | 21,739 | 14.35% |

#### Technology Domain Distribution (`FIELD_OF_INVENTION`)
| Domain Field | Record Count | Percentage |
| :--- | :---: | :---: |
| CHEMISTRY | 38,871 | 25.67% |
| MECHANICAL | 32,828 | 21.68% |
| ELECTRONICS | 14,591 | 9.63% |
| ELECTRICAL | 12,199 | 8.06% |
| COMMUNICATION | 7,972 | 5.26% |
| POLYMER | 7,853 | 5.19% |
| COMPUTER | 7,342 | 4.85% |
| PHYSICS | 7,308 | 4.83% |
| BIOTECHNOLOGY | 6,016 | 3.97% |
| BIOMEDICAL | 5,232 | 3.45% |
| METALLURGY | 3,313 | 2.19% |
| TEXTILE | 2,369 | 1.56% |
| BIOCHEMISTRY | 2,055 | 1.36% |
| CIVIL | 2,017 | 1.33% |
| FOOD | 1,248 | 0.82% |
| *MISSING / UNKNOWN* | 225 | 0.15% |

#### Application Procedure Type
| Application Type | Record Count | Percentage |
| :--- | :---: | :---: |
| PCT NATIONAL PHASE APPLICATION | 102,587 | 67.74% |
| ORDINARY APPLICATION | 30,848 | 20.37% |
| CONVENTION APPLICATION | 15,493 | 10.23% |
| DIVISIONAL PCT NATIONAL PHASE APPLICATION | 2,053 | 1.36% |
| PATENT OF ADDITION FOR ORDINARY APPLICATION | 179 | 0.12% |
| DIVISIONAL CONVENTION APPLICATION | 130 | 0.09% |
| DIVISIONAL ORDINARY APPLICATION | 127 | 0.08% |
| PATENT OF ADDITION FOR PCT NATIONAL PHASE APPLICATION | 18 | 0.01% |
| PATENT OF ADDITION FOR CONVENTION APPLICATION | 4 | 0.00% |

---

## 4. Text Encodings & Special Character Profile
Discovered **29** distinct non-ASCII characters across titles.
Crucially, genuine scientific characters such as `°` (degrees), `±` (plus-minus), `µ` (micro), and `ß` (sharp s) must be preserved rather than stripped.

| Unicode Codepoint | Glyph | Official Name | Frequency in Titles | Cleaning Strategy |
| :--- | :---: | :--- | :---: | :--- |
| `U+201C` | `“` | LEFT DOUBLE QUOTATION MARK | 4,961 | Strip when wrapping outer title; normalize |
| `U+201D` | `”` | RIGHT DOUBLE QUOTATION MARK | 4,903 | Strip when wrapping outer title; normalize |
| `U+2019` | `’` | RIGHT SINGLE QUOTATION MARK | 150 | Preserve internal apostrophe / normalize |
| `U+00DF` | `ß` | LATIN SMALL LETTER SHARP S | 99 | Preserve (Chemical / German terminology) |
| `U+2013` | `–` | EN DASH | 52 | Preserve as standard hyphen |
| `U+2018` | `‘` | LEFT SINGLE QUOTATION MARK | 46 | Strip outer / normalize |
| `U+00A0` | ` ` | NO-BREAK SPACE | 43 | Normalize to regular ASCII space |
| `U+00B0` | `°` | DEGREE SIGN | 12 | Preserve (Thermal / Angle measurements) |
| `U+00B1` | `±` | PLUS-MINUS SIGN | 6 | Preserve (Tolerance / Scientific notations) |
| `U+00B5` | `µ` | MICRO SIGN | 2 | Preserve (Micrometer / Physical quantities) |
| `U+00AD` | `·` | SOFT HYPHEN | 2 | Remove non-visible hyphenation break |
