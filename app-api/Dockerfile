FROM python:3.10-slim

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install gsutil==5.21

# copy the pretrained huggingface tokenizer blobs
ENV APP_HOME /app
WORKDIR $APP_HOME

RUN gsutil cp gs://${_MODEL_PATH}/${_MODEL_VERSION}/best_model.pt .
RUN gsutil cp gs://${_MODEL_PATH}/${_MODEL_VERSION}/tokenizer.pt .
COPY api.py .
COPY service.py .

CMD exec uvicorn service:app --host 0.0.0.0 --port ${PORT} --workers 1
