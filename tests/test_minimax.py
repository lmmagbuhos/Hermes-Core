import httpx
import pytest

from hermes_core.llm.minimax import LlmMessage, MiniMaxClient


@pytest.mark.asyncio
async def test_minimax_client_posts_chat_completion_and_parses_response():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Hermes response",
                        }
                    }
                ],
                "id": "completion_123",
            },
        )

    transport = httpx.MockTransport(handler)
    client = MiniMaxClient(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        model="minimax-test",
        transport=transport,
    )

    response = await client.complete([LlmMessage(role="user", content="Hello")])

    assert response.content == "Hermes response"
    assert response.raw["id"] == "completion_123"
    assert len(requests) == 1
    assert requests[0].url == "https://api.example.test/v1/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert requests[0].read()


@pytest.mark.asyncio
async def test_minimax_client_rejects_response_without_content():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    client = MiniMaxClient(
        api_key="test-key",
        base_url="https://api.example.test/v1",
        model="minimax-test",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ValueError, match="MiniMax response did not include message content"):
        await client.complete([LlmMessage(role="user", content="Hello")])
