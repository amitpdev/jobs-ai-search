FROM rasa/rasa:3.5.11 AS runner

WORKDIR /app
USER root

COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./actions actions
COPY ./data data
COPY ./custom custom
COPY ./*.yml ./

RUN chgrp -R 0 /app && chmod -R g=u /app && chmod o+wr /app

USER 1001

# Rasa model storage, from cloud
# https://rasa.com/docs/rasa/model-storage#load-model-from-cloud
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/gcs.json"
ENV BUCKET_NAME="jobs-nlu-models"

# Prepare a GCS service-account JSON key. Avoid escaping json.
ARG GCS_JSON_KEY
RUN printf "%s" "$GCS_JSON_KEY" > "$GOOGLE_APPLICATION_CREDENTIALS"

CMD ["run", "--remote-storage", "gcs", "--enable-api", "--cors", "*", "-vv"]
