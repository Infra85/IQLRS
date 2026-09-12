import asyncio
import logging

import httpx
import pytest

from app.api import speech
from app.core.config import Settings
from app.main import app
from app.services.speech.cache import AudioCache
from app.services.speech.provider import OpenAISpeechProvider, SpeechFailure
from app.services.speech.service import NarrationService


class FakeProvider:
    def __init__(self):
        self.calls = 0
        self.cancelled = False
        self.started = asyncio.Event()
        self.delay = 0.01

    async def generate(self, text):
        self.calls += 1
        self.started.set()
        try:
            await asyncio.sleep(self.delay)
            return b"ID3-test-audio"
        except asyncio.CancelledError:
            self.cancelled = True
            raise


def config(tmp_path, **kwargs):
    return Settings(_env_file=None, tts_cache_path=str(tmp_path / "speech.sqlite3"), **kwargs)


def test_missing_key_is_safe_and_lesson_api_remains_available(tmp_path, monkeypatch):
    monkeypatch.setattr(speech, "service", NarrationService(config(tmp_path, openai_api_key="")))
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            assert (await client.get("/api/speech/config")).json()["available"] is False
            response = await client.post("/api/speech", json={"text": "A qubit."})
            assert response.status_code == 503
            assert "key" not in response.text.lower()
            assert (await client.get("/")).status_code == 200
    asyncio.run(run())


def test_validation_does_not_call_provider(tmp_path, monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr(speech, "service", NarrationService(config(tmp_path), provider))
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            for body in [{"text": " "}, {"text": "a" * 1601}, {"text": "hi", "voice": "other"}, {"text": "\x00"}]:
                assert (await client.post("/api/speech", json=body)).status_code == 422
            response = await client.post("/api/speech", json={"text": "A qubit is a quantum bit."})
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert response.headers["x-content-type-options"] == "nosniff"
            assert response.content == b"ID3-test-audio"
            assert provider.calls == 1
    asyncio.run(run())


def test_identical_requests_share_generation_and_survive_restart(tmp_path):
    async def run():
        provider = FakeProvider()
        service = NarrationService(config(tmp_path), provider)
        values = await asyncio.gather(*(service.generate("Hadamard gate.", f"client-{i}") for i in range(8)))
        assert len({value[1] for value in values}) == 1
        assert provider.calls == 1
        again = NarrationService(config(tmp_path), provider)
        assert await again.generate("Hadamard gate.", "new-client") == values[0]
        assert provider.calls == 1
        changed = NarrationService(config(tmp_path, tts_voice="cedar"), provider)
        assert (await changed.generate("Hadamard gate.", "new-client"))[1] != values[0][1]
        assert provider.calls == 2
    asyncio.run(run())


def test_cancel_last_waiter_aborts_generation(tmp_path):
    async def run():
        provider = FakeProvider()
        provider.delay = 30
        service = NarrationService(config(tmp_path), provider)
        task = asyncio.create_task(service.generate("Quantum state.", "client"))
        await provider.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert provider.cancelled
        assert not service.pending
    asyncio.run(run())


def test_cancel_one_waiter_does_not_cancel_other_listener(tmp_path):
    async def run():
        provider = FakeProvider()
        provider.delay = 0.1
        service = NarrationService(config(tmp_path), provider)
        first = asyncio.create_task(service.generate("Entanglement.", "a"))
        second = asyncio.create_task(service.generate("Entanglement.", "b"))
        await provider.started.wait()
        while service.pending[next(iter(service.pending))].waiters != 2:
            await asyncio.sleep(0.001)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert (await second)[0] == b"ID3-test-audio"
        assert not provider.cancelled
        assert provider.calls == 1
    asyncio.run(run())


def test_budget_and_rate_limits(tmp_path):
    async def run():
        service = NarrationService(config(tmp_path, tts_daily_char_limit=12, tts_requests_per_minute=2), FakeProvider())
        await service.generate("first", "a")
        await service.generate("first", "a")  # Cached text does not spend character budget.
        with pytest.raises(SpeechFailure, match="rate_limited"):
            await service.generate("first", "a")
        await service.generate("second", "b")
        with pytest.raises(SpeechFailure, match="daily_limit"):
            await service.generate("third", "c")
    asyncio.run(run())


def test_cache_lru_ttl_and_atomic_budget(tmp_path, monkeypatch):
    cache = AudioCache(str(tmp_path / "cache.sqlite3"), 10, 60)
    cache.put("a", b"123456")
    cache.put("b", b"123456")
    assert cache.get("a") is None
    assert cache.get("b") == b"123456"
    from app.services.speech import cache as cache_module
    now = cache_module.time.time()
    monkeypatch.setattr(cache_module.time, "time", lambda: now + 61)
    assert cache.get("b") is None
    assert cache.reserve_characters(7, 10)
    assert not cache.reserve_characters(4, 10)


def test_provider_errors_are_redacted_and_retry_works(tmp_path, monkeypatch, caplog):
    class Failing:
        async def generate(self, text):
            raise RuntimeError("SECRET-UPSTREAM-ACCOUNT")
    service = NarrationService(config(tmp_path), Failing())
    monkeypatch.setattr(speech, "service", service)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/api/speech", json={"text": "Probability."})
            assert response.status_code == 503
            assert "SECRET" not in response.text
            service.provider = FakeProvider()
            assert (await client.post("/api/speech", json={"text": "Probability."})).status_code == 200
    with caplog.at_level(logging.WARNING):
        asyncio.run(run())
    assert "SECRET" not in caplog.text


def test_openai_adapter_uses_configured_neural_voice(tmp_path, monkeypatch):
    requests = []
    def respond(request):
        import json
        requests.append(json.loads(request.content))
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, content=b"ID3-audio", headers={"content-type": "audio/mpeg"})
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    provider = OpenAISpeechProvider(config(tmp_path, openai_api_key="test-key"))
    assert asyncio.run(provider.generate("Quantum computing.")) == b"ID3-audio"
    assert requests[0]["model"] == "gpt-4o-mini-tts"
    assert requests[0]["voice"] == "marin"
    assert requests[0]["response_format"] == "mp3"
    assert "Hadamard" in requests[0]["instructions"]
