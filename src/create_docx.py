import asyncio
import io
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from os import listdir
from pathlib import Path
from typing import (
    Callable,
    Optional,
)

from docx import Document
from PIL import Image


class CreateDocx:
    """Формирование документа с таблицей фотографий"""

    PHOTO_DIR_DEFAULT: Path = Path(__file__).parents[1] / Path("photo")
    SUPPORTED_FORMATS: list = ["jpg", "png"]

    def __init__(
        self,
        loop: AbstractEventLoop,
        callback: Callable[[int, int], None],
        path: str = None,
        col: int = 2,
        output: Path = Path("demo.docx"),
    ):
        self._completed_files: int = 0
        self._load_test_future: Optional[Future] = None
        self._photo_dir = Path(path) if path else self.PHOTO_DIR_DEFAULT
        self._all_file_names = [i for i in listdir(self._photo_dir) if i.split(".")[-1] in self.SUPPORTED_FORMATS]
        self._all_files = len(self._all_file_names)
        self._col = col
        self._output = output
        self._loop = loop
        self._callback = callback

    def start(self):
        self._load_test_future = asyncio.run_coroutine_threadsafe(self._make_files(), self._loop)

    def cancel(self):
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)

    async def _make_files(self):
        """Открытие всех файлов"""
        files = [self._get_files(i) for i in self._all_file_names]
        row = self._all_files // self._col + bool(self._all_files % self._col)
        files = await asyncio.gather(*files)

        doc = Document()
        table = doc.add_table(row, self._col)
        img_index = 0
        for r in table.rows:
            for cell in r.cells:
                if img_index < len(files):
                    p = cell.add_paragraph()
                    r = p.add_run()
                    r.add_picture(files[img_index])
                    r.add_text(self._all_file_names[img_index])
                    img_index += 1
        doc.save(str(self._output))

    async def _get_files(self, file_name: str):
        """Открытие файла"""
        img = Image.open(self._photo_dir / Path(file_name))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=img.format)
        self._completed_files = self._completed_files + 1
        self._callback(self._completed_files, self._all_files)
        return img_byte_arr
