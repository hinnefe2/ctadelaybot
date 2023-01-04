FROM python:3.10-slim

COPY requirements.txt .

RUN pip install -r requirements.txt

# copy the pretrained huggingface tokenizer blobs
ENV APP_HOME /app
WORKDIR $APP_HOME

COPY .cache .cache
ENV TRANSFORMERS_CACHE=.cache
ENV HF_HOME=.cache

COPY best_model.pt .
COPY service.py .

CMD exec uvicorn service:app --host 0.0.0.0 --port ${PORT} --workers 1
