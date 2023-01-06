import unicodedata

import torch

from typing import Dict, List

from dateutil import parser

from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api import get_alerts


CTA_ALERTS_URI = (
    "http://lapi.transitchicago.com/api/1.0/alerts.aspx?outputType=JSON"  # noqa
)
DURATIONS = {
    0: "less than 30 minutes",
    1: "between 30 minutes and an hour",
    2: "more than an hour",
}

app = FastAPI()

# Allow CORS so we can just use client-side js and serve the frontend as a static site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

tokenizer = torch.load("tokenizer.pt")
model = torch.load("best_model.pt", map_location="cpu")
model.eval()


# CamelCase to match the CTA API
class AlertWithDuration(BaseModel):
    ServiceName: str
    ServiceId: str
    EventStart: str
    ShortDescription: str
    FullDescription: str
    Duration: str


class Response(BaseModel):
    alerts: List[AlertWithDuration]


def _generate_text(event_start: str, full_description: str):

    # strip out HTML tags, convert unicode characters, and flatten newlines
    text = unicodedata.normalize(
        "NFKC",
        " ".join(
            BeautifulSoup(full_description, features="html.parser")
            .get_text()
            .splitlines()
        ),
    )

    # TODO: confirm that I trained the model on UTC timestamps
    start_time = parser.parse(event_start).strftime("%a %H %M %b %d %Y")

    return f"Event started at {start_time} with message {text}"


def _predict_duration(alert: Dict) -> int:

    text = _generate_text(alert["EventStart"], alert["FullDescription"])

    tokenized = tokenizer(text)

    input_ids = torch.tensor(tokenized.input_ids, dtype=torch.int).unsqueeze(0)
    attention_mask = torch.tensor(tokenized.attention_mask, dtype=torch.int).unsqueeze(
        0
    )

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

    return torch.argmax(outputs.logits, axis=-1).item()


@app.get("/alerts", response_model=Response)
async def alerts():

    cta_alerts = get_alerts()

    alert_durations = [_predict_duration(alert) for alert in cta_alerts]

    return Response(
        alerts=[
            AlertWithDuration(
                EventStart=alert["EventStart"],
                ShortDescription=alert["ShortDescription"],
                FullDescription=alert["FullDescription"],
                ServiceName=service["ServiceName"],
                ServiceId=service["ServiceId"],
                Duration=DURATIONS[duration],
            )
            for alert, duration in zip(cta_alerts, alert_durations)
            for service in alert["ImpactedService"]
            if service["ServiceType"] == "R"
        ]
    )
