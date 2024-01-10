import asyncio
from os import listdir
from pathlib import Path

from PIL import Image


class AllPhoto:
    """Получение всех файлов фотографий"""

    PHOTO_DIR_DEFAULT = Path(__file__).parents[1] / Path("photo")
    PHOTO_FORMATS = {"png", "jpeg"}

    def __init__(self, path: Path = None):
        self.photo_dir = path if path else self.PHOTO_DIR_DEFAULT

    async def start(self):
        """Запуск формирования списка фотографий"""
        all_photos = []
        for f in listdir(self.photo_dir):
            if f.split(".")[-1] in self.PHOTO_FORMATS:
                all_photos.append(self._load_photo(self.photo_dir / Path(f)))
        all_photos = asyncio.gather(*all_photos)

    @staticmethod
    async def _load_photo(path: Path) -> Image:
        """Загрузка фотографии"""
        return Image.open(path)
