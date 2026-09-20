from types import SimpleNamespace

from content_stream_service import ContentRequest, stream_content


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "auto"
        assert kwargs["stream"] is True
        return [
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hello "))]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="subscribers."))]),
        ]


class FakeClient:
    chat = SimpleNamespace(completions=FakeCompletions())


def test_delivery_waits_for_complete_stream():
    request = ContentRequest(creator_id="c-7", brief="Say hello", asset_name="hello.txt")

    events = list(stream_content(request, FakeClient()))

    assert [event["event"] for event in events] == [
        "subscriber_update",
        "subscriber_update",
        "asset_delivered",
    ]
    assert events[-1]["text"] == "Hello subscribers."
    assert events[-1]["asset_name"] == "hello.txt"
