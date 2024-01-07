import asyncio
from asyncio import AbstractEventLoop
from asyncio.subprocess import Process
from concurrent.futures import Future
from typing import Optional


class RunProcess:
    def __init__(
        self,
        loop: AbstractEventLoop,
        command: tuple,
    ):
        self._completed_requests: int = 0
        self._load_test_future: Optional[Future] = None
        self._loop = loop
        self._command = command

    def start(self):
        self._load_test_future = asyncio.run_coroutine_threadsafe(self._make_requests(), self._loop)

    def cancel(self):
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)

    async def _make_requests(self):
        process: Process = await asyncio.create_subprocess_exec(*self._command)
        print(f"Процесс {process.pid}")
        try:
            status_code = await asyncio.wait_for(process.wait(), timeout=3)
            print(status_code)
        except asyncio.TimeoutError:
            print("Завершилось по таймауту")
            process.terminate()
            status_code = await process.wait()
            print(status_code)
