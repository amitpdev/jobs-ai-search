import os
import sqlite3
from pathlib import Path

from src.domain import JobPost


class SQLiteDB:
    conn: sqlite3.Connection

    def __init__(self, db_filename: str):
        # Ensure parent folder exists.
        db_dir = Path(db_filename).parent
        if not db_dir.exists():
            db_dir.mkdir(mode=0o750, parents=True)

        # Connect to database.
        db_exists = os.path.exists(db_filename)
        self.conn = sqlite3.connect(db_filename)
        self.conn.row_factory = sqlite3.Row

        # Create schema if database doesn't exist.
        if not db_exists:
            print("Database doesn't exist, creating it now...")
            self.create_tables()

    def close(self):
        self.conn.close()

    def create_tables(self):
        """Define the schema for the jobs and companies tables"""

        jobs_table_schema = """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY,
            job_post_id TEXT UNIQUE,
            job_title TEXT,
            job_location TEXT,
            workplace_type TEXT,
            posted_date TEXT,
            posted_timestamp INT DEFAULT (strftime('%s', 'now')),
            job_description TEXT,
            company_id INTEGER,
            contact TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
        """

        companies_table_schema = """
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY,
            company_name TEXT UNIQUE,
            company_description TEXT
        )
        """

        # Create the jobs and companies tables
        self.conn.execute(jobs_table_schema)
        self.conn.execute(companies_table_schema)

    def save_jobs_to_sqlite(self, jobs: list[JobPost], debug: bool):
        # Insert data into the companies table
        companies = {}
        for job in jobs:
            companies[job.company_name] = job.company_description

        for company_name, company_description in companies.items():
            if debug:
                print("sqlite: Inserting company {}".format(company_name))
            company_query = """
                INSERT OR IGNORE INTO companies
                (company_name, company_description)
                VALUES (?, ?)
            """
            try:
                self.conn.execute(
                    company_query,
                    (company_name, company_description),
                )
            except sqlite3.OperationalError as e:
                raise e

        # Insert data into the jobs table
        for job in jobs:
            company_query = (
                "SELECT company_id FROM companies WHERE company_name = ?"
            )
            try:
                company_id = self.conn.execute(
                    company_query, (job.company_name,)
                ).fetchone()[0]
            except sqlite3.OperationalError as e:
                raise e

            job_query = """
                INSERT OR IGNORE INTO jobs (
                    job_post_id, job_title, job_location, workplace_type,
                    posted_date, posted_timestamp, job_description, company_id,
                    contact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            if debug:
                print("sqlite: Inserting job {}".format(job.job_title))
            try:
                self.conn.execute(
                    job_query,
                    (
                        job.job_post_id,
                        job.job_title,
                        job.job_location,
                        job.workplace_type,
                        job.posted_date,
                        job.posted_timestamp,
                        job.job_description,
                        company_id,
                        job.contact,
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise e

        # Commit the changes
        self.conn.commit()
