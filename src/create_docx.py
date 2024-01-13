from os import listdir
from pathlib import Path

from docx import Document


class CreateDocx:
    """Формирование документа с таблицей фотографий"""

    PHOTO_DIR_DEFAULT = Path(__file__).parents[1] / Path("photo")
    SUPPORTED_FORMATS = ["jpg", "png"]

    def __init__(self, path: Path = None, col: int = 2, output: Path = Path("demo.docx")):
        self.photo_dir = path if path else self.PHOTO_DIR_DEFAULT
        self.col = col
        self.output = output

    async def start(self):
        all_files = [i for i in listdir(self.photo_dir) if i.split(".")[-1] in self.SUPPORTED_FORMATS]
        row = len(all_files) // self.col + bool(len(all_files) % self.col)

        doc = Document()
        table = doc.add_table(row, self.col)
        img_index = 0
        for r in table.rows:
            for cell in r.cells:
                if img_index < len(all_files):
                    path_img = self.photo_dir / Path(all_files[img_index])
                    p = cell.add_paragraph()
                    r = p.add_run()
                    r.add_picture(str(path_img))
                    r.add_text(all_files[img_index])
                    img_index += 1
        doc.save(str(self.output))
