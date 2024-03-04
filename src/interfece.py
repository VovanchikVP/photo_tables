from queue import Queue
from tkinter import (
    END,
    NW,
    Canvas,
    Entry,
    Frame,
    Label,
    Tk,
    filedialog,
    ttk,
)
from typing import Optional

from PIL import (
    Image,
    ImageTk,
)

from src.create_docx import CreateDocx


class LoadTester(Tk):
    def __init__(self, loop, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self._queue = Queue()
        self._refresh_ms = 25
        self.row_img_table = 5
        self._width_photo = 200
        self.all_img: dict[str, CustomImg] = {}
        self._loop = loop
        self._load_test: Optional[CreateDocx] = None
        self._last_obj: Optional[CreateDocx] = None
        self.title("Формирование фототаблицы")
        self._url_label = Label(self, text="Путь:")
        self._url_label.grid(column=0, row=0)
        self._url_field = Entry(self, width=10)
        self._url_field.grid(column=1, row=0)
        self._run_ls = ttk.Button(self, text="Открыть", command=self._open_directory)
        self._run_ls.grid(column=2, row=0)
        self._request_label = Label(self, text="Количество колонок:")
        self._request_label.grid(column=0, row=1)
        self._request_field = Entry(self, width=10)
        self._request_field.grid(column=1, row=1)
        self._submit = ttk.Button(self, text="Сформировать", command=self._start)
        self._submit.grid(column=2, row=1)
        self._pb_label = Label(self, text="Progress:")
        self._pb_label.grid(column=0, row=3)
        self._pb = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self._pb.grid(column=1, row=3, columnspan=2)

    def _update_bar(self, pct: int):
        if pct == 100:
            self._pb["value"] = pct
            self._load_test = None
            self._submit["text"] = "Сформировать"
            self._create_canvas()
        else:
            self._pb["value"] = pct
            self.after(self._refresh_ms, self._poll_queue)

    def _queue_update(self, completed_requests: int, total_requests: int):
        self._queue.put(int(completed_requests / total_requests * 100))

    def _poll_queue(self):
        if not self._queue.empty():
            percent_complete = self._queue.get()
            self._update_bar(percent_complete)
        else:
            if self._load_test:
                self.after(self._refresh_ms, self._poll_queue)

    def _start(self):
        if self._load_test is None:
            self._submit["text"] = "Отмена"
            test = CreateDocx(
                self._loop,
                self._queue_update,
                self._url_field.get(),
                int(self._request_field.get()),
            )
            self._pb["value"] = 0
            self.after(self._refresh_ms, self._poll_queue)
            test.start()
            self._load_test = test
            self._last_obj = test
        else:
            self._load_test.cancel()
            self._load_test = None
            self._submit["text"] = "Сформировать"

    def _create_canvas(self):
        """Формирование канваса для фото таблицы"""
        _photo_in_row = int(self._request_field.get())
        f = ScrollableFrame(self)
        f.grid(row=self.row_img_table, column=0, columnspan=4)
        f.configure(borderwidth=2, relief="raised")
        f.grid_propagate(False)
        canvas = PhotoPage(f.scrollable_frame, 210, 297)
        row = PhotoRow(_photo_in_row)
        for count, img in enumerate(self._last_obj.files):
            if not row.add(img, count, self._rout_img):
                if not canvas.add(row):
                    canvas = self._add_row_in_new_page(f.scrollable_frame, canvas, row)
                new_row = PhotoRow(_photo_in_row, before_row=row)
                row.next_row = new_row
                row = new_row
                row.add(img, count, self._rout_img)
            self.all_img[f"img_{count}"] = row.images[-1]
        if not row.photo_page:
            if not canvas.add(row):
                canvas = self._add_row_in_new_page(f.scrollable_frame, canvas, row)
            canvas.show()

    @staticmethod
    def _add_row_in_new_page(root: Frame, canvas: "PhotoPage", row: "PhotoRow") -> "PhotoPage":
        """Добавление строки на новую страницу"""
        canvas.show()
        new_canvas = PhotoPage(root, 210, 297, before_page=canvas)
        canvas.next_page = new_canvas
        new_canvas.add(row)
        return new_canvas

    def _open_directory(self):
        f = filedialog.askdirectory()
        self._url_field.delete(0, END)
        self._url_field.insert(0, f)

    def _rout_img(self, events):
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        print(f"Вы кликнули по изображению №: {tag_img}")
        self.all_img[tag_img].rotation()


class PhotoRow:
    """Строка с изображениями"""

    MAX_WIDTH_ROW = 200

    def __init__(self, length: int, before_row=None, next_row=None):
        self.before_row: Optional["PhotoRow"] = before_row
        self.next_row: Optional["PhotoRow"] = next_row
        self.row_position = None
        self.photo_page: Optional["PhotoPage"] = None
        self.length = length
        self.img_width = int(self.MAX_WIDTH_ROW / self.length)
        self.height = 0
        self.images: list[CustomImg] = []

    def add(self, img: Image, count: int, callback) -> bool:
        """Добавление изображения в строку"""
        if len(self.images) == self.length:
            return False
        img_cast = CustomImg(img, self.img_width, count, callback)
        img_cast.photo_row = self
        self.images.append(img_cast)
        self.calculation_height()
        return True

    def add_row_in_canvas(self, photo_page: "PhotoPage" = None, row_position: int = None) -> None:
        """Добавление строки на канвас"""
        self.photo_page = photo_page if photo_page is not None else self.photo_page
        self.row_position = row_position if row_position is not None else self.row_position
        for num, img in enumerate(self.images):
            position_img_in_row = num * self.img_width
            img.add_img_in_canvas(self.photo_page, position_img_in_row, self.row_position)

    def calculation_height(self) -> None:
        new_height = max([i.img_height for i in self.images])
        if self.height != new_height:
            self.height = new_height
            if self.photo_page:
                if self.photo_page.before_page:
                    start_page = self.photo_page.before_page
                    row = self.photo_page.before_page.rows[0]
                else:
                    start_page = self.photo_page
                    row = self.photo_page.rows[0]

                page = start_page
                while page:
                    page.clear_page()
                    page = page.next_page
                start_page.change_row(row)

                page = start_page
                while page:
                    new_page = page.next_page
                    if not page.rows:
                        page.before_page.next_page = None
                        page.canvas.destroy()
                        del page
                    page = new_page


class CustomImg:
    def __init__(
        self,
        img: Image,
        img_width: int,
        count: int,
        callback,
    ):
        self.img_width = img_width
        self.img_height = 0
        self.page: Optional["PhotoPage"] = None
        self.photo_row: Optional[PhotoRow] = None
        self.img = img
        self.width_row = None
        self.height_row = None
        self.tag = f"img_{count}"
        self.callback = callback
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)

    def _create_img_in_docs(self) -> Image:
        """Формирование размера фотографии"""
        self.img_height = int(self.img.size[1] / self.img.size[0] * self.img_width)
        return self.img.resize((self.img_width, self.img_height))

    def rotation(self):
        """Поворот изображения на 90 градусов"""
        self.img = self.img.rotate(90, expand=1)
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)
        self.photo_row.calculation_height()

    def add_img_in_canvas(self, page: "PhotoPage" = None, width_row: int = None, height_row: int = None):
        """Добавление изображения на канвас"""
        self.page = page if page else self.page
        self.width_row = self.width_row if width_row is None else width_row
        self.height_row = self.height_row if height_row is None else height_row
        img_name = self.page.canvas.create_image(
            self.width_row, self.height_row, anchor=NW, image=self.tk_img, tag=self.tag
        )
        self.page.canvas.tag_bind(img_name, "<Button-1>", self.callback)


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=5, column=0, columnspan=4)
        scrollbar.grid(row=5, column=5)
        canvas.update_idletasks()


class PhotoPage:
    """Страница с фотографиями"""

    def __init__(
        self,
        root: Frame,
        width: int,
        height: int,
        before_page: Optional["PhotoPage"] = None,
        next_page: Optional["PhotoPage"] = None,
    ):
        self.width = width
        self.height = height
        self.before_page = before_page
        self.root = root
        self.next_page = next_page
        self.content_height = 0
        self.canvas = Canvas(root, bg="white", height=height, width=width)
        self.canvas.grid(pady=10, padx=10)
        self.rows: list[PhotoRow] = []

    def add(self, row: PhotoRow) -> bool:
        """Добавление строки"""
        if row.height + self.content_height > self.height:
            return False
        self.rows.append(row)
        self.content_height += row.height
        row.photo_page = self
        return True

    def change_row(self, row: Optional["PhotoRow"]):
        """Перерисовка строк"""
        while row:
            if self.add(row):
                row = row.next_row
            else:
                if self.next_page is None:
                    self.next_page = PhotoPage(self.root, self.width, self.height, before_page=self)
                self.next_page.change_row(row)
                row = None
        self.show()

    def clear_page(self):
        """Отчистка страницы"""
        self.canvas.delete("all")
        self.content_height = 0
        self.rows = []

    def show(self):
        """Отображение данных канваса"""
        height = 0
        for num, row in enumerate(self.rows):
            row.add_row_in_canvas(self, height)
            height += row.height
