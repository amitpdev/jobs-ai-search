# good resources
# https://qdrant.tech/articles/hybrid-search/
# https://www.sbert.net/examples/applications/semantic-search/README.html

import asyncio
import itertools
from pgvector.psycopg import register_vector_async, register_vector
import psycopg
from sentence_transformers import CrossEncoder, SentenceTransformer
# from src.db_pg import SQLiteDB

# establish connection
# conn = psycopg.connect(dbname='pgvector_example', autocommit=True)

# model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    'The dog is barking',
    'The cat is purring',
    'The bear is growling'
]
query = 'bark'


async def create_schema(conn):
    await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
    await register_vector_async(conn)

    await conn.execute('DROP TABLE IF EXISTS document')
    await conn.execute('CREATE TABLE document (id bigserial PRIMARY KEY, content text, embedding vector(384))')
    await conn.execute("CREATE INDEX ON document USING GIN (to_tsvector('english', content))")


async def insert_data(conn):
    model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    embeddings = model.encode(sentences)

    sql = 'INSERT INTO jobs (job_description, job_description_vector) VALUES ' + ', '.join(['(%s, %s)' for _ in embeddings])
    params = list(itertools.chain(*zip(sentences, embeddings)))
    await conn.execute(sql, params)


async def search_location(conn, query):
    embedding = model.encode(query)

    async with conn.cursor() as cur:
        sql = """
        SELECT job_id, job_location,
        (job_location_vector <=> %s) AS location_similarity
        FROM jobs
        ORDER BY location_similarity
        """
        await cur.execute(sql, (embedding,))
        return await cur.fetchall()


async def keyword_search(conn, query):
    async with conn.cursor() as cur:
        await cur.execute("SELECT id, job_description FROM jobs, plainto_tsquery('english', %s) query WHERE to_tsvector('english', job_description) @@ query ORDER BY ts_rank_cd(to_tsvector('english', job_description), query) DESC LIMIT 5", (query,))
        return await cur.fetchall()


def rerank(query, results):
    # deduplicate
    results = set(itertools.chain(*results))
    # re-rank
    encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    scores = encoder.predict([(query, item[1]) for item in results])
    return [v for _, v in sorted(zip(scores, results), reverse=True)]


def chunk_encode_sentences(sentences, chunk_size):
    model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
    embeddings = []
    # Chunk the sentences into smaller subsets
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i+chunk_size]
        # Encode the chunk of sentences
        chunk_embeddings = model.encode(chunk)
        # Append the chunk embeddings to the result list
        embeddings.extend(chunk_embeddings)
    return embeddings


def export_import():
    db = SQLiteDB('/Users/amit/Projects/linkedin_scraper/data/linkedai.db')
    cur = db.conn.cursor()

    cur.execute("SELECT * FROM companies")
    companies_data = cur.fetchall()

    # Export jobs table
    cur.execute("SELECT * FROM jobs")
    jobs_data = cur.fetchall()

    # Close SQLite connection
    db.close()

    pg_conn = psycopg.connect(
        host='localhost',
        dbname='postgres',
        user='postgres',
        password='postgres'
    )
    pg_cursor = pg_conn.cursor()

    # Import companies table
    for row in companies_data:
        pg_cursor.execute("INSERT INTO companies (company_id, company_name, company_description) VALUES (%s, %s, %s)", row)

    # Import jobs table
    for row in jobs_data:
        pg_cursor.execute("INSERT INTO jobs (job_id, job_post_id, job_title, job_location, workplace_type, posted_date, posted_timestamp, job_description, company_id, contact) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", row)

    # Commit the changes
    pg_conn.commit()

    # Close PostgreSQL connection
    pg_conn.close()


def _text_builder(job_title, job_description) -> str:

    r = f"""
Job Title: {job_title}
Job Description: {job_description}
"""
    return r


## EMBEDDING INTO DB
def embed_job_descriptions_and_save():
    # PostgreSQL connection
    pg_conn = psycopg.connect(
        host='localhost',
        dbname='postgres',
        user='postgres',
        password='postgres'
    )

    register_vector(pg_conn)


    pg_cursor = pg_conn.cursor()

    # SentenceTransformer model
    # model = SentenceTransformer('all-MiniLM-L6-v2')

    # Retrieve job descriptions and IDs from the database
    sql = """
    SELECT job_id, job_title, job_description
    FROM jobs
    WHERE job_description_vector is NULL
    """
    pg_cursor.execute(sql)

    # Prepare the data for updating the job_description_vector column
    for job_id, job_title, job_description in pg_cursor.fetchall():
        text_to_encode = _text_builder(job_title, job_description)
        embedding = model.encode(text_to_encode)

        sql = """
        UPDATE jobs
        SET job_description_vector = %s
        WHERE job_id = %s
        """

        print(f'RUNNING SQL: {sql} for JOB_ID:{job_id}')

        pg_cursor.execute(sql, (embedding, job_id))

    pg_conn.commit()
    # Close the connection
    pg_conn.close()


def embed_job_location_and_save():
    # PostgreSQL connection
    pg_conn = psycopg.connect(
        host='localhost',
        dbname='postgres',
        user='postgres',
        password='postgres'
    )

    register_vector(pg_conn)


    pg_cursor = pg_conn.cursor()

    # SentenceTransformer model
    # model = SentenceTransformer('all-MiniLM-L6-v2')

    # Retrieve job descriptions and IDs from the database
    sql = "SELECT job_id, job_location FROM jobs"
    pg_cursor.execute(sql)

    # Prepare the data for updating the job_description_vector column
    for job_id, job_location in pg_cursor.fetchall():
        text_to_encode = job_location
        embedding = model.encode(text_to_encode)

        sql = """
        UPDATE jobs
        SET job_location_vector = %s  -- Assuming pgvector column type
        WHERE job_id = %s
        """

        print(f'RUNNING SQL: {sql} for JOB_ID:{job_id}')

        pg_cursor.execute(sql, (embedding, job_id))

    pg_conn.commit()
    # Close the connection
    pg_conn.close()


## EMBEDDING
def embed(text: str) -> list[float]:

    embedding = model.encode(text)
    # convert numpy array to string array
    return embedding.astype(float).tolist()

def embedding_debug_loop():
    while True:
        query = input("query: ")
        if query:
            print(embed(query))


## SEMANTIC SEARCH


async def semantic_search(conn, job_query, job_title, location_query):

    job_query_embedded = model.encode(job_query)

    async with conn.cursor() as cur:

        # for verbosity add to select:
        # SIMILARITY(lower(job_title), lower(%s)) as title_score,
        # (1 - (job_description_vector <=> %s)) AS job_description_score,
        # SIMILARITY(lower(job_location), lower(%s)) location_score,

        sql = """
        SELECT job_id, job_title, job_location,
            jobs_rerank_score(
                SIMILARITY(lower(job_title), lower(%s)),
                (1 - (job_description_vector <=> %s)),
                SIMILARITY(lower(job_location), lower(%s))
            ) as rerank_score
        FROM jobs
        ORDER BY rerank_score DESC
        LIMIT 30;
        """


        await cur.execute(sql, (job_title, job_query_embedded,location_query,))
        return await cur.fetchall()


async def semantic_search_loop():
    conn = await psycopg.AsyncConnection.connect(
        dbname='postgres',
        host="localhost",
        user="postgres",
        password="postgres",
        autocommit=True)

    await register_vector_async(conn)

    while True:
        job_title = '' #input("job title: ")
        job_query = input("job query: ")
        location_query = input("location query: ")


        results = await semantic_search(conn, job_query, job_title, location_query)
        # results = await search_location(conn, location_query)

        for result in results:
            print(result)


async def main():

    # await create_schema(conn)
    # await insert_data(conn)
    # perform queries in parallel
    # results = await asyncio.gather(semantic_search(conn, query), keyword_search(conn, query))
    # results = rerank(query, results)
    # print(results)
    # results = await keyword_search
    # (conn, query)

    embed_job_descriptions_and_save()
    # embed_job_location_and_save()
    # export_import()

    # await semantic_search_loop()
    # await embedding_debug_loop()


asyncio.run(main())
