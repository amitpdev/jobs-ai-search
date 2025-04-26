import logging
from typing import Any

from src.db_pg import PostgresDB
from src.domain import JobPost, NLUEntity
from src.ai_model import embed

logger = logging.getLogger('uvicorn')


class DBService:
    @staticmethod
    def compile_hybrid_query(entities: list[NLUEntity]) -> tuple[str, list[Any]]:
        """
        Take each given entity and use its value for either semantic search
        (using pg_vector cosine similarity <=>) or fuzzy keyword search (using SIMILARITY).
        jobs_rerank_score accepts 4 arguments, we use 0 for missing entities.

        i.e resulting SQL:

            SELECT job_id, job_post_id, job_title, job_location, workplace_type,
                posted_date, posted_timestamp, contact, company_id, companies.company_name,
                jobs_rerank_score(
                    (1 - (job_description_vector <=> %s)),
                    GREATEST(SIMILARITY(lower(job_title), lower(%s))),
                    GREATEST(SIMILARITY(lower(job_location), lower(%s)), SIMILARITY(lower(job_location), lower(%s))),
                    GREATEST(SIMILARITY(lower(workplace_type), lower(%s)))
                ) as rerank_score
            FROM jobs
            INNER JOIN companies ON jobs.company_id = companies.company_id
            ORDER BY rerank_score DESC
            LIMIT 30;
        """

        entity_dict = {}
        for entity in entities:
            if entity.entity in entity_dict:
                entity_dict[entity.entity].append(entity.value)
            else:
                entity_dict[entity.entity] = [entity.value]

        rerank_items = []
        params = []

        ### semantic search entities
        semantic_query = ''
        if 'job_title' in entity_dict:
            job_title_values = entity_dict['job_title']
            semantic_query += f"[Job Title: {', '.join(job_title_values)}] "
        if 'skills' in entity_dict:
            skills_values = entity_dict['skills']
            semantic_query += f"[Skills: {', '.join(skills_values)}] "

        if semantic_query:
            semantic_query_embedded = embed(semantic_query.strip())
            rerank_items.append("(1 - (job_description_vector <=> %s))")
            params.append(f'{semantic_query_embedded}')
        else:
            rerank_items.append('0')

        ## Fuzzy similarity entities
        for entity_type in ['job_title', 'job_location', 'workplace_type']:
            values = entity_dict.get(entity_type)
            if values:
                similarities = [f'SIMILARITY(lower({entity_type}), lower(%s))'] * len(values)
                rerank_items.append('GREATEST(' + ', '.join(similarities) + ')')
                params.extend(values)
            else:
                rerank_items.append('0')

        sql = """
        SELECT job_id, job_post_id, job_title, job_location, workplace_type,
        posted_date, posted_timestamp, contact, jobs.company_id, companies.company_name,
        jobs_rerank_score(
            {}
        ) as rerank_score
        FROM jobs
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY rerank_score DESC
        LIMIT 30;
        """.format(',\n'.join(rerank_items))

        # replace %s with $1, $2..
        sql = sql.replace("%s", "${}").format(*tuple(range(1, sql.count("%s") + 1))).strip()

        return (sql, params)


    @staticmethod
    async def save_companies_to_postgres(db: PostgresDB, job_posts: list[JobPost]):
        # Insert data into the companies table
        companies = {}
        for job_post in job_posts:
            companies[job_post.company_name] = job_post.company_description

        queries = []
        for company_name, company_description in companies.items():
            logger.debug("DBService: Inserting company {}".format(company_name))
            company_query = """
                INSERT INTO companies
                (company_name, company_description)
                VALUES ($1, $2)
                ON CONFLICT ON CONSTRAINT companies_company_name_key DO NOTHING
            """
            queries.append((company_query, company_name, company_description))

        await db.execute_transaction(queries)


    @staticmethod
    async def save_jobs_to_postgres(db: PostgresDB, job_posts: list[JobPost]):
        """ Insert data into the jobs table """

        # first, get companies
        companies = await db.fetch("SELECT company_id, company_name FROM companies")

        queries = []
        for job_post in job_posts:

            # try to find company_id from job_post.company_name
            matching_company = next((company for company in companies if company["company_name"] == job_post.company_name), None)
            if matching_company:
                company_id = matching_company['company_id']
            else:
                continue

            job_query = """
                INSERT INTO jobs (
                    job_post_id, job_title, job_location, workplace_type,
                    posted_date, posted_timestamp, job_description, company_id,
                    contact)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT ON CONSTRAINT jobs_job_post_id_key DO NOTHING
            """

            logger.debug("DBService: Inserting job %s", job_post.job_title)

            queries.append((job_query,
                            job_post.job_post_id, job_post.job_title,
                            job_post.job_location, job_post.workplace_type,
                            job_post.posted_date, job_post.posted_timestamp,
                            job_post.job_description, company_id,
                            job_post.contact))

        await db.execute_transaction(queries)


    @staticmethod
    async def embed_job_description_vector(db: PostgresDB):

        def _text_builder(job_title, job_description) -> str:
            r = f"""
Job Title: {job_title}
Job Description: {job_description}
"""
            return r

        logger.debug("DBService: Searching for jobs with job_description_vector..")

        # Retrieve job descriptions and IDs from the database
        sql = """
        SELECT job_id, job_title, job_description
        FROM jobs
        WHERE job_description_vector is NULL
        """
        jobs = await db.fetch(sql)
        if not jobs:
            logger.debug("DBService: Found 0 jobs with missing job_description_vector")
            return

        # Prepare the data for updating the job_description_vector column
        queries = []
        for job_id, job_title, job_description in jobs:
            # compile document and embed
            text_to_encode = _text_builder(job_title, job_description)
            embedding = embed(text_to_encode)
            # add to query list
            sql = """
            UPDATE jobs
            SET job_description_vector = $1
            WHERE job_id = $2
            """
            queries.append((sql, f'{embedding}', job_id))

        logger.debug(f"DBService: Updating {len(queries)} jobs with embedded job_description_vector")
        await db.execute_transaction(queries)
