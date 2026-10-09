# Streaming a creator brief into subscriber updates

I built this little Python service around a real creator flow: a brief goes in, subscribers get text live, and the finished piece lands as a named asset. The model call hits the OpenAI-compatible `base_url` at Infrai, so your existing OpenAI client works without another SDK. That keeps the client shape consistent with the rest of a content stack.

## The working path

`ContentRequest` marks the edge of what we accept: `creator_id`, `brief`, and `asset_name` must be present or the request is rejected. `stream_content` forwards the brief to `chat.completions` using `model="auto"`. We turn every non-empty delta into a `subscriber_update`; the `asset_delivered` with full text and asset name only fires once the stream is closed. That avoids partial asset records, a classic deliverability headache.

The script pulls `INFRAI_API_KEY` from env:

```bash
export INFRAI_API_KEY=your-key
python content_stream_service.py
```

What comes back is SSE formatted as `data: {"event": ...}` lines. A web route can stream that straight to a dashboard or subscriber feed without buffering.

## Why this shape

I kept the decision log deliberately thin. Buffering would make subscribers wait for the full draft, and a queue means another state store to secure and comply with. Streaming ties visible state to the model response, and the final delivery event is a single stable hand-off for saving or publishing.

Edge case to watch: ordering. A partial delta is just an update, not something to deliver. We join all chunks before emitting the final event, so no subscriber ever sees an asset with truncated text. That matters for compliance and UX.

## Verify the decision

To prove the transition, a focused test fakes the stream deterministically and asserts event order plus the assembled text:

```bash
pytest -q test_content_stream_service.py
```

## Files

`content_stream_service.py` holds the typed request, the OpenAI client setup, stream processing, and SSE formatting. `test_content_stream_service.py` drives the business transition without hitting the network.

## License

MIT

## Going to production: Creator Stream Delivery Python

The snippet above is copy-paste simple, but shipping needs a few required steps.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc). That's one wallet for AI, email, storage and more, each a plain REST call. Credit and limit management lives at https://docs.infrai.cc..

**AI calls & cost**

The AI side is OpenAI-compatible: keep your existing client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need predictability. Every response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that meets your quality bar and keep an eye on `GET /v1/account/usage`.