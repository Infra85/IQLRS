import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass

from app.core.config import Settings, settings
from .cache import AudioCache
from .provider import INSTRUCTIONS, SpeechFailure, SpeechProvider, make_provider

logger = logging.getLogger(__name__)


@dataclass
class Pending:
    task: asyncio.Task
    waiters: int = 0


class NarrationService:
    def __init__(self, config: Settings, provider: SpeechProvider | None = None):
        self.config = config
        self.provider = provider
        self.cache = AudioCache(config.tts_cache_path, config.tts_cache_max_bytes, config.tts_cache_ttl_seconds)
        self.pending: dict[str, Pending] = {}
        self.slots = asyncio.Semaphore(config.tts_max_concurrent)
        self.requests: OrderedDict[str, list[float]] = OrderedDict()

    @property
    def version(self) -> str:
        value = f"speech-v1|{self.config.tts_provider}|{self.config.tts_model}|{self.config.tts_voice}|{INSTRUCTIONS}"
        return hashlib.sha256(value.encode()).hexdigest()[:24]

    @property
    def available(self) -> bool:
        return self.provider is not None or (self.config.tts_provider == "openai" and bool(self.config.openai_api_key))

    def rate_limit(self, client: str):
        # Do not trust client-supplied forwarded IP headers. Bound identity memory too.
        now = time.monotonic()
        recent = [t for t in self.requests.pop(client, []) if t > now - 60]
        self.requests[client] = recent
        while len(self.requests) > 4096:
            self.requests.popitem(last=False)
        if len(recent) >= self.config.tts_requests_per_minute:
            raise SpeechFailure("rate_limited")
        recent.append(now)

    async def _generate(self, key: str, text: str) -> bytes:
        async with self.slots:
            # A different worker may have filled the cache while this job waited.
            cached = await asyncio.to_thread(self.cache.get, key)
            if cached is not None:
                return cached
            allowed = await asyncio.to_thread(self.cache.reserve_characters, len(text), self.config.tts_daily_char_limit)
            if not allowed:
                raise SpeechFailure("daily_limit")
            provider = self.provider or make_provider(self.config)
            data = await provider.generate(text)
            await asyncio.to_thread(self.cache.put, key, data)
            return data

    async def generate(self, text: str, client: str) -> tuple[bytes, str]:
        if not self.available:
            raise SpeechFailure("not_configured")
        self.rate_limit(client)
        key = hashlib.sha256(f"{self.version}|{text}".encode()).hexdigest()
        try:
            cached = await asyncio.to_thread(self.cache.get, key)
            if cached is not None:
                return cached, key
            # No await between lookup and insertion: one task per key in this event loop.
            job = self.pending.get(key)
            if job is None:
                if len(self.pending) >= 32:
                    raise SpeechFailure("busy")
                job = Pending(asyncio.create_task(self._generate(key, text)))
                self.pending[key] = job
            job.waiters += 1
            try:
                return await asyncio.shield(job.task), key
            finally:
                job.waiters -= 1
                if job.waiters == 0:
                    self.pending.pop(key, None)
                    if not job.task.done():
                        job.task.cancel()
                    # Retrieve completion/cancellation even if the last caller disconnected.
                    await asyncio.gather(job.task, return_exceptions=True)
        except SpeechFailure as exc:
            logger.warning("Narration unavailable: code=%s key=%s", exc.code, key[:12])
            raise
        except Exception:
            # No exception string: provider bodies may contain account details.
            logger.error("Narration cache/service failure: key=%s", key[:12])
            raise SpeechFailure("unavailable") from None


service = NarrationService(settings)
