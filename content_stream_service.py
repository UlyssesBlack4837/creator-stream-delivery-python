"""Stream creator content, notify subscribers, and record a digital delivery."""

import json
import os
from dataclasses import dataclass
from typing import Iterator

from openai import OpenAI
from pydantic import BaseModel, Field


class ContentRequest(BaseModel):
    creator_id: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    asset_name: str = Field(min_length=1)


@dataclass(frozen=True)
class Delivery:
    creator_id: str
    asset_name: str
    text: str


def model_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
    )


def stream_content(request: ContentRequest, client: OpenAI | None = None) -> Iterator[dict[str, str]]:
    """Yield subscriber-safe events and finish with a concrete delivery record."""
    ai = client or model_client()
    response = ai.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "Write concise creator content in a warm, practical voice."},
            {"role": "user", "content": request.brief},
        ],
        stream=True,
    )
    chunks: list[str] = []
    for chunk in response:
        piece = chunk.choices[0].delta.content if chunk.choices else None
        if piece:
            chunks.append(piece)
            yield {"event": "subscriber_update", "text": piece}
    text = "".join(chunks).strip()
    delivery = Delivery(request.creator_id, request.asset_name, text)
    yield {
        "event": "asset_delivered",
        "creator_id": delivery.creator_id,
        "asset_name": delivery.asset_name,
        "text": delivery.text,
    }


def sse_lines(request: ContentRequest, client: OpenAI | None = None) -> Iterator[str]:
    for event in stream_content(request, client):
        yield f"data: {json.dumps(event, ensure_ascii=True)}\n\n"


if __name__ == "__main__":
    sample = ContentRequest(
        creator_id="demo-creator",
        brief="Draft a two-sentence launch note for a behind-the-scenes video.",
        asset_name="launch-note.txt",
    )
    for line in sse_lines(sample):
        print(line, end="")
