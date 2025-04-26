api_docs = """
API documentation:
Endpoint: http://localhost:8000
GET /jobs

This API is for searching job postings.

Query jobs table:
job_title | string | job_title search term, e.g., iOS developer, python developer, devops engineer, etc... | required
job_location | string | Limit search results to a specific job location (e.g., Tel Aviv, Kfar Sava, etc). If not specified, it'll be any location. | optional
workplace_type | string | Limit search results to a specific workplace type (e.g., Hybrid, on-site, Remote). If not specified, it'll be any workplace type. | optional
skills | list | Limit search results to a specific list of skills (e.g., [python, IT expert, PostgreSQL] ). If not specified, it'll be any skill. | optional

Response schema (JSON object):
results | array[object] (Job List Result Object)

Each object in the "results" key has the following schema:
job_id | integer | required
job_post_id | string | required
job_title | string | required
job_location | string | required
workplace_type | string | optional
posted_date | string | required
posted_timestamp | int | required
job_description | string | optional
company_id | integer | required
contact | string | optional
company_name | string | required
"""
