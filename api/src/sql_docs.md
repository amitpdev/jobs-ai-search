# SQL Docs

## MIGRATION

### 1. Enable pg_vector excension:
```sql
CREATE EXTENSION vector;
```

### 2. Enable fuzzy matching
```sql
CREATE EXTENSION fuzzystrmatch;
```

### 3. Enable pg_trgm extension
```sql
CREATE EXTENSION pg_trgm;
```

### 4. Create Companies table
```sql
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE,
    company_description TEXT
);
```

### 5. Create Jobs table
```sql
CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    job_post_id TEXT UNIQUE,
    job_title TEXT,
    job_location TEXT,
    workplace_type TEXT,
    posted_date TEXT,
    posted_timestamp INTEGER DEFAULT (extract(epoch from now())),
    job_description TEXT,
    job_description_vector vector(384),
    company_id INTEGER,
    contact TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);
```

### 6. jobs_rerank_score function
```sql
CREATE OR REPLACE FUNCTION jobs_rerank_score(
    semantic_query_score float8,
    job_title_score real,
    job_location_score real,
    workplace_type_score real
)
RETURNS float8
AS $$
BEGIN
    RETURN semantic_query_score + job_title_score + job_location_score
        * 1.1 + workplace_type_score; -- can add weights by multiplying by 1.x
END;
$$ LANGUAGE plpgsql;
```

### 7. Import data!

### 8. Index job_description_vector with Cosine similarity (Run after some data is inserted)
```sql
CREATE INDEX ON jobs USING ivfflat (job_description_vector vector_cosine_ops)
WITH (lists = 100);
```

### 9. Create pg_trgm index on job_location and workplace_type (and future fields)
```sql
CREATE INDEX job_location_trgm_idx ON jobs USING gin (job_location gin_trgm_ops);
CREATE INDEX workplace_type_trgm_idx ON jobs USING gin (workplace_type gin_trgm_ops);
```
