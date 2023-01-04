import unicodedata

import torch

from dateutil import parser, tz

from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = FastAPI()

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-cased", cache_dir=".cache")
model = torch.load("best_model.pt", map_location="cpu")
model.eval()

DURATIONS = {
    0: "less than 30 minutes",
    1: "between 30 minutes and an hour",
    2: "more than an hour",
}


class Request(BaseModel):
    # Note that event_start should be in America/Chicago timezone
    event_start: str
    full_description: str


class Response(BaseModel):
    duration_int: int
    duration_str: str


def _parse_alert(event_start: str, full_description: str):

    # strip out HTML tags, convert unicode characters, and flatten newlines
    text = unicodedata.normalize(
        "NFKC",
        " ".join(
            BeautifulSoup(full_description, features="html.parser")
            .get_text()
            .splitlines()
        ),
    )

    CT = tz.gettz("America/Chicago")
    UTC = tz.gettz("UTC")

    # TODO: convert to UTC
    start_time = (
        parser.parse(event_start)
        .replace(tzinfo=CT)
        .astimezone(UTC)
        .strftime("%a %H %M %b %d %Y")
    )

    return f"Event started at {start_time} with message {text}"


def _predict(request: Request) -> Response:

    text = _parse_alert(request.event_start, request.full_description)

    tokenized = tokenizer(text)

    input_ids = torch.tensor(tokenized.input_ids, dtype=torch.int).unsqueeze(0)
    attention_mask = torch.tensor(tokenized.attention_mask, dtype=torch.int).unsqueeze(
        0
    )

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

    pred = torch.argmax(outputs.logits, axis=-1).item()

    return Response(duration_int=pred, duration_str=DURATIONS[pred])


@app.post("/predict-duration", response_model=Response)
async def predict_duration(request: Request):
    return _predict(request)
