FROM python:3.10-slim

COPY best_model.pt .
COPY tokenizer.pt .
COPY requirements.txt .

RUN pip install -r requirements.txt

# copy the pretrained huggingface tokenizer blobs
ENV APP_HOME /app
WORKDIR $APP_HOME

COPY api.py .
COPY service.py .

CMD exec uvicorn service:app --host 0.0.0.0 --port ${PORT} --workers 1
