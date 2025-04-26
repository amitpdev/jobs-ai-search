FROM python:3.11.3-slim

WORKDIR /code/worker

ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PYTHONUNBUFFERED 1

COPY ./setup.py ./requirements.txt ./requirements-dev.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src src

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["celery", "-A", "src.main"]
CMD []
