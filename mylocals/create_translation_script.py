#!/usr/bin/env python3
"""
Builds a single SQL file (polylang.sql) from CSV files shaped as:
phrase, language_code, translated_phrase

- Each CSV file is named <language_code>.csv
- Source and destination folders are configured via global vars below.
- Output SQL uses: INSERT INTO appointment_db.translations (phrase, language_code, translated_phrase) VALUES (...);

Tested with UTF-8 CSVs. Escapes single quotes by doubling them for SQL literals.
"""

from pathlib import Path
import csv
import sys

# =======================
# Global configuration
# =======================
SOURCE_DIR = Path("./csv_files")        # <- change if needed
DEST_DIR   = Path("../db/init")              # <- change if needed
OUTPUT_SQL = "02-polylang.sql"

# Set to True to print a warning if row language_code != filename language
STRICT_MATCH_FILENAME_LANG = False

# =======================
# Helpers
# =======================
def sql_escape(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    if value is None:
        return ""
    return value.replace("'", "''")

def detect_and_skip_header(row: list[str]) -> bool:
    """
    Returns True if the row looks like a header (case-insensitive match on the three columns).
    Expects row length >= 3.
    """
    hdr = [c.strip().lower() for c in row[:3]]
    return hdr == ["phrase", "language_code", "translated_phrase"]

def iter_csv_files(src: Path):
    """Yield (path, lang_code_from_filename) for each <lang>.csv under src (non-recursive)."""
    for p in sorted(src.glob("*.csv")):
        lang = p.stem.strip()
        if not lang:
            continue
        yield p, lang

# =======================
# Main logic
# =======================
def main():
    if not SOURCE_DIR.exists():
        print(f"ERROR: Source folder does not exist: {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEST_DIR / OUTPUT_SQL

    total_files = 0
    total_rows = 0
    written_rows = 0

    with out_path.open("w", encoding="utf-8", newline="") as out_f:
        for csv_path, file_lang in iter_csv_files(SOURCE_DIR):
            total_files += 1
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                first_row_checked = False
                for row in reader:
                    if not row or all(not (cell or "").strip() for cell in row):
                        # skip empty row
                        continue

                    # Ensure at least 3 columns
                    if len(row) < 3:
                        # skip malformed row
                        continue

                    if not first_row_checked:
                        if detect_and_skip_header(row):
                            first_row_checked = True
                            continue
                        first_row_checked = True

                    total_rows += 1
                    phrase = (row[0] or "").strip()
                    lang   = (row[1] or "").strip()
                    trans  = (row[2] or "").strip()

                    # Optional check against filename language
                    if STRICT_MATCH_FILENAME_LANG and lang and file_lang and (lang != file_lang):
                        print(
                            f"WARNING: {csv_path.name} row language_code='{lang}' "
                            f"does not match filename language='{file_lang}'.",
                            file=sys.stderr
                        )

                    # Skip if essential fields are missing
                    if not phrase or not lang or not trans:
                        continue

                    # Escape for SQL literals
                    phrase_sql = sql_escape(phrase)
                    lang_sql   = sql_escape(lang)
                    trans_sql  = sql_escape(trans)

                    line = (
                        "INSERT INTO appointment_db.translations "
                        "(phrase, language_code, translated_phrase) "
                        f"VALUES ('{phrase_sql}', '{lang_sql}', '{trans_sql}');\n"
                    )
                    out_f.write(line)
                    written_rows += 1

    print(f"Wrote {written_rows} INSERTs from {total_rows} parsed rows across {total_files} file(s).")
    print(f"Output: {out_path.resolve()}")

if __name__ == "__main__":
    main()
