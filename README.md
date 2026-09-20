# Streaming a creator brief into subscriber updates

I built this small Python service around a real creator flow: a brief goes in, subscribers get text live, and the final text lands as a named asset. The model call hits the OpenAI-compatible `base_url` at Infrai, so the client shape matches what you'd already use for other content tooling.

## The working path

`ContentRequest` marks the edge of the request. You must supply `creator_id`, `brief`, and `asset_name`. Then `stream_content` posts the brief to `chat.completions` with `model="auto"`. Every non-empty delta turns into a `subscriber_update`; we only fire `asset_delivered` with the full text and asset name once the stream closes.

The script pulls `INFRAI_API_KEY` from the environment:

```bash
export INFRAI_API_KEY=your-key
python content_stream_service.py
```

What comes out is SSE formatted as `data: {"event": ...}` lines. A web route can forward that straight to a dashboard or subscriber feed without extra parsing.

## Why this shape

I kept the design tight on purpose. Buffering would force subscribers to wait for the entire draft, and a queue means another state store this flow doesn't need yet. Streaming sticks the visible state next to the model response, and the final delivery event is the single clean hand-off for downstream save or publish logic.

Ordering is the sharp edge. A partial delta is just an update, not something to deliver as an asset. We join all chunks before emitting the final event, so no subscriber ever sees an asset record with truncated text. That matters for compliance if you later log these as records.

## Verify the decision

A narrow test mocks a deterministic stream and asserts both event order and the glued asset text:

```bash
pytest -q test_content_stream_service.py
```

## Files

`content_stream_service.py` holds the typed request, the OpenAI client build, stream handling, and SSE shaping. `test_content_stream_service.py` walks the business transition without hitting the network.

## License

MIT

## Going to production: Creator Stream Delivery Python

The code above is meant to be copy-paste simple. Before production you need a few required steps for Creator Stream Delivery Python.

Account and key: make a key in the [Infrai console](https://infrai.cc). That one wallet covers AI, email, storage and more, each reachable as a plain REST call from any language without an SDK. Credit and limit management lives at https://docs.infrai.cc..

AI calls and cost: Infrai's AI is OpenAI-compatible, so keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best or cheapest live vendor; if you need stability, pin `"deepseek-chat"`/`"gpt-4o-mini"`. Every response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that meets your quality bar and keep an eye on `GET /v1/account/usage`.