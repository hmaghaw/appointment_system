# PolyLang SQL Generator

## Overview
This Python script reads all CSV files from a specified **source folder** and generates a single SQL file (`polylang.sql`) containing `INSERT` statements for the `appointment_db.translations` table.  

Each CSV file should:
- Be named `<language_code>.csv` (e.g., `en.csv`, `hi.csv`).
- Contain data in the format:

```
phrase,language_code,translated_phrase
```

Example CSV row:
```
EXAMPLES OF CONCISE RESPONSES,hi,संक्षिप्त उत्तरों के उदाहरण
```

The script processes all matching CSV files and writes a unified SQL file in the **destination folder**.

---

## Features
- **Automatic CSV discovery**: Reads all `.csv` files from the configured source directory.
- **Header detection**: Skips header rows if present.
- **Blank/invalid row skipping**: Ignores rows missing any required fields.
- **Filename vs. row language validation**: (optional) Warns if CSV file name and row `language_code` differ.
- **SQL-safe escaping**: Handles single quotes in text for safe SQL insertion.
- **Configurable paths**: Source and destination directories set via global variables.
- **Summary output**: Prints the number of processed files, rows parsed, and SQL lines written.

---

## Directory Structure
```
project/
├── source_csv/              # Folder containing language CSV files
│   ├── en.csv
│   ├── hi.csv
│   └── ar.csv
├── dist/                    # Output folder (generated if not present)
│   └── polylang.sql         # Generated SQL file
├── build_polylang_sql.py    # The Python script
└── README.md
```

---

## Configuration
In `build_polylang_sql.py`:

```python
SOURCE_DIR = Path("./source_csv")  # Source CSV folder
DEST_DIR   = Path("./dist")        # Destination folder
OUTPUT_SQL = "polylang.sql"        # Output SQL file name
```

Optional strict filename-to-row language matching:
```python
STRICT_MATCH_FILENAME_LANG = False
```

---

## Usage
1. Place your CSV files into the **source folder**.
2. Ensure each CSV is named `<language_code>.csv` and follows the required format.
3. Run the script:
```bash
python3 build_polylang_sql.py
```
4. The resulting `polylang.sql` file will be in the **destination folder**.

---

## Example Output
Given the CSV:
```csv
phrase,language_code,translated_phrase
EXAMPLES OF CONCISE RESPONSES,hi,संक्षिप्त उत्तरों के उदाहरण
```

The generated SQL will contain:
```sql
INSERT INTO appointment_db.translations (phrase, language_code, translated_phrase)
VALUES ('EXAMPLES OF CONCISE RESPONSES', 'hi', 'संक्षिप्त उत्तरों के उदाहरण');
```

---

## Validation SQL
After loading the generated SQL into your database, you can verify the number of entries per language with:

```sql
SELECT 
    language_code, 
    COUNT(*) AS occurrences
FROM 
    appointment_db.translations
GROUP BY 
    language_code
ORDER BY 
    occurrences DESC;
```

This query will list each `language_code` with the count of translations inserted.

---

## Requirements
- Python 3.7+
- UTF-8 encoded CSV files

---

## Notes
- The script automatically creates the destination folder if it does not exist.
- Rows with missing or empty values in any of the required columns are skipped.
- If `STRICT_MATCH_FILENAME_LANG` is set to `True`, the script will print warnings for mismatched languages.

---
