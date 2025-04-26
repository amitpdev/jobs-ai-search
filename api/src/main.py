import logging
from typing import Optional

from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import httpx
from fastapi import Depends

from src import config
from src.db_pg import PostgresDB
from src.domain import CompanyDB, JobPost, JobResponse, NLURequest, NLUResponse, NLUEntity
from src.db_service import DBService


logger = logging.getLogger('uvicorn')
logger.setLevel(config.UVICORN_LOGGING_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = PostgresDB()
    await db.connect()
    app.state.database = db

    yield
    # Anything after yield is called at shutdown
    await app.state.database.disconnect()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://jobs.nester.co.il",
    "https://jobs.nester.co.il",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_database() -> PostgresDB:
    return app.state.database

@app.get("/_status/healthz")
async def root():
    return {"message": "OK"}


# Define API endpoints
@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_id(job_id: int, db: PostgresDB = Depends(get_database)):
    row = await db.fetchrow(
        """
        SELECT
            job_id, job_post_id, job_title, job_location, workplace_type,
            posted_date, posted_timestamp, job_description, jobs.company_id,
            contact, companies.company_name, companies.company_description
        FROM jobs
        INNER JOIN companies ON jobs.company_id = companies.company_id
        WHERE jobs.job_id=$1
        """,
        job_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JobResponse(**row)
    return job


@app.get("/jobs", response_model=list[JobResponse])
async def get_jobs(
    job_title: Optional[str] = None,
    job_location: Optional[str] = None,
    job_description: Optional[str] = None,
    workplace_type: Optional[str] = None,
    sort_by_posted_timestamp: Optional[bool] = False,
    db: PostgresDB = Depends(get_database)
):
    query = """
    SELECT jobs.job_id, jobs.job_post_id, jobs.job_title, jobs.job_location,
        jobs.workplace_type, jobs.posted_date, jobs.posted_timestamp,
        jobs.job_description, companies.company_id, companies.company_name,
        jobs.contact
    FROM jobs
    INNER JOIN companies ON jobs.company_id = companies.company_id
    """

    params = []
    if job_title:
        query += " WHERE jobs.job_title LIKE %s"
        params.append(f"%{job_title}%")
    if job_location:
        if not job_title:
            query += " WHERE"
        else:
            query += " AND"
        query += " jobs.job_location LIKE %s"
        params.append(f"%{job_location}%")
    if job_description:
        if not job_title and not job_location:
            query += " WHERE"
        else:
            query += " AND"
        query += " jobs.job_description LIKE %s"
        params.append(f"%{job_description}%")
    if workplace_type:
        if not job_title and not job_location and not job_description:
            query += " WHERE"
        else:
            query += " AND"
        query += " jobs.workplace_type = %s"
        params.append(workplace_type)

    if sort_by_posted_timestamp:
        query += " ORDER BY jobs.posted_timestamp DESC"

    # Convert ? placeholders to numbered placeholders ($1 $2 ..)
    query = query.replace("%s", "${}").format(*tuple(range(1, query.count("%s") + 1)))

    rows = await db.fetch(query, *params)

    jobs = []
    for row in rows:
        job = JobResponse(**row)
        jobs.append(job)

    return jobs


@app.post("/jobs", status_code=status.HTTP_201_CREATED)
async def post_job(job_posts: list[JobPost], db: PostgresDB = Depends(get_database)):
    await DBService.save_companies_to_postgres(db, job_posts)
    await DBService.save_jobs_to_postgres(db, job_posts)
    await DBService.embed_job_description_vector(db)
    return {"message": "Jobs saved successfully"}


@app.post("/query", response_model=NLUResponse)
async def post_query(query: NLURequest):
    try:
        resp = httpx.post(config.ENDPOINT_NLU, json=query.dict())
        resp.raise_for_status()
        response_data = resp.json()
        response_model = NLUResponse(**response_data)
        return response_model
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"HTTP Exception for {exc.request.url} - {exc}",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse NLU response - {exc}",
        )


@app.post("/jobs_entities", response_model=list[JobResponse])
async def get_jobs_by_entities(entities: list[NLUEntity],  db: PostgresDB = Depends(get_database)):
    sql, params = DBService.compile_hybrid_query(entities)

    rows = await db.fetch(sql, *params)
    return [JobResponse(**row) for row in rows]


@app.get("/companies/{company_id}", response_model=CompanyDB)
async def get_company_by_id(company_id: int, db: PostgresDB = Depends(get_database)):
    row = await db.fetchrow(
        """
        SELECT company_id, company_name, company_description
        FROM companies
        WHERE company_id=$1
        """,
        company_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    company = CompanyDB(**row)
    return company


@app.get("/companies", response_model=list[CompanyDB])
async def get_companies(db: PostgresDB = Depends(get_database)):
    rows = await db.fetch(
        "SELECT company_id, company_name, company_description FROM companies"
    )
    companies = [CompanyDB(**company) for company in rows]
    return companies
