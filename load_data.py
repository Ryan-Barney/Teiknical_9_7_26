# Part 1
# Python script to load data into SQLite database for cell counts CSV
# Run: python load_data.py

import csv
import os
import sqlite3

DB = "Loblaw_Bio_immune_trial.db"
CSV = "cell-count.csv"

CELL_TYPES = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

#  Allow values to be stored as NULL in database if they are empty in CSV
def parse_text(value):
    value = value.strip()
    return value if value else None

# Allow values to be stored as NULL in database if they are empty in CSV
# Exception: Cell counts must be present
def parse_int(value):
    value = value.strip()
    return int(value) if value else None

# Generate the database tables for subjects, samples, and cell counts
def create_tables(cursor):
    # Create table for subjects
    cursor.execute("""
        CREATE TABLE subjects (
            subject TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            condition TEXT NOT NULL,
            age INTEGER,
            sex TEXT,
            treatment TEXT,
            response TEXT
        );
    """)

    # Create table for samples
    cursor.execute("""
        CREATE TABLE samples (
            sample TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            sample_type TEXT,
            time_from_treatment_start INTEGER,
            FOREIGN KEY (subject) REFERENCES subjects(subject)
        );
    """)

    # Create table for cell counts
    cursor.execute("""
        CREATE TABLE cell_counts (
            sample TEXT NOT NULL,
            cell_type TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (sample, cell_type),
            FOREIGN KEY (sample) REFERENCES samples(sample)
        );
    """)

# Load all data from CSV into the database
def load_csv(cursor):
    with open(CSV, "r", newline="", encoding="utf-8") as file:
        r = csv.DictReader(file)
        for row in r:
            # Insert subjects
            cursor.execute("""
                INSERT OR IGNORE INTO subjects (
                    subject,
                    project,
                    condition,
                    age,
                    sex,
                    treatment,
                    response
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                parse_text(row["subject"]),
                parse_text(row["project"]),
                parse_text(row["condition"]),
                parse_int(row["age"]),
                parse_text(row["sex"]),
                parse_text(row["treatment"]),
                parse_text(row["response"]),
            ))

            # Insert samples
            cursor.execute("""
                INSERT INTO samples (
                    sample,
                    subject,
                    sample_type,
                    time_from_treatment_start
                )
                VALUES (?, ?, ?, ?);
            """, (
                parse_text(row["sample"]),
                parse_text(row["subject"]),
                parse_text(row["sample_type"]),
                parse_int(row["time_from_treatment_start"]),
            ))

            # Insert cell counts - row per cell type
            for cell_type in CELL_TYPES:
                cursor.execute("""
                    INSERT INTO cell_counts (
                        sample,
                        cell_type,
                        count
                    )
                    VALUES (?, ?, ?);
                """, (
                    parse_text(row["sample"]),
                    cell_type,
                    int(row[cell_type]),
                ))


def main():
    # Rebuild the database each time
    if os.path.exists(DB):
        os.remove(DB)
    connection = sqlite3.connect(DB)
    try:
        cursor = connection.cursor()
        # Allow foreign key constraints to be enforced
        cursor.execute("PRAGMA foreign_keys = ON;")
        create_tables(cursor)
        load_csv(cursor)
        connection.commit()
        print(f"Database created successfully: {DB}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()