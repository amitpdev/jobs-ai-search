import re
from typing import Optional

from pydantic import BaseModel, constr, validator


class Company(BaseModel):
    company_name: str
    company_description: Optional[str] = None


class CompanyDB(Company):
    company_id: int


class Job(BaseModel):
    job_post_id: str
    job_title: str
    job_location: str
    workplace_type: Optional[str]
    posted_date: str
    posted_timestamp: Optional[int]
    job_description: Optional[str]
    contact: Optional[str]


class JobDB(Job):
    job_id: int


class JobPost(Job, Company):
    pass


class JobResponse(JobDB, CompanyDB):
    pass


def clean_text(text):
    pattern = r"[?$%^&@!#-]"
    cleaned_text = re.sub(pattern, " ", text)
    return cleaned_text


class NLURequest(BaseModel):
    text: str

    @validator("text", pre=True)
    def clean_text(cls, text):
        return clean_text(text)


class NLUResponse(BaseModel):
    """Response from Rasa NLU server.
    https://rasa.com/docs/rasa/pages/http-api#operation/parseModelMessage
    """

    entities: Optional[list[dict]]
    intent: Optional[dict]
    intent_ranking: Optional[list[dict]]
    text: Optional[str]
    text_tokens: Optional[list]


class NLUEntity(BaseModel):
    entity: constr(regex="^(job_title|job_location|workplace_type|skills)$")
    value: str
