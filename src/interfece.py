from queue import Queue
from tkinter import (
    END,
    NW,
    Canvas,
    Entry,
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
from src.run_process import RunProcess


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
        self._run_ls = ttk.Button(self, text="Run LS", command=self._start_ls)
        self._run_ls.grid(column=0, row=4)
        self._canvas_table = None

    def _update_bar(self, pct: int):
        if pct == 100:
            self._pb["value"] = pct
            self._load_test = None
            self._submit["text"] = "Сформировать"
            self._create_canvas()
            # self._create_image_table()
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

    def _start_ls(self):
        test = RunProcess(self._loop, ("ls",))
        test.start()

    def _create_canvas(self):
        """Формирование канваса для фото таблицы"""
        _height_row = 0
        _width_row = 0
        _max_height_row = 0
        f = ScrollableFrame(self)
        f.grid(row=self.row_img_table, column=0, columnspan=4)
        f.configure(borderwidth=2, relief="raised")
        f.grid_propagate(False)
        canvas = Canvas(f.scrollable_frame, bg="white", height=297, width=210)
        canvas.grid(pady=10, padx=10)
        for count, img in enumerate(self._last_obj.files):
            size = self._create_size_photo(img)
            if _width_row + size[0] > 210:
                _width_row = 0
                _height_row = _max_height_row
            if _height_row + size[1] > 297:
                _max_height_row = 0
                _width_row = 0
                _height_row = 0
                canvas = Canvas(f.scrollable_frame, bg="white", height=297, width=210)
                canvas.grid(pady=10, padx=10)
            self.all_img[f"img_{count}"] = CustomImg(
                canvas,
                img,
                self._width_photo,
                int(self._request_field.get()),
                _width_row,
                _height_row,
                count,
                self._rout_img,
            )
            _width_row, _height_row, _new_page, _new_row = self._get_coordinate_photo(_width_row, _height_row, size)
            if _max_height_row < _height_row + size[1]:
                _max_height_row = _height_row + size[1]
            if _new_row:
                _height_row = _max_height_row
            if _new_page:
                _max_height_row = 0
                canvas = Canvas(f.scrollable_frame, bg="white", height=297, width=210)
                canvas.grid(pady=10, padx=10)

    @staticmethod
    def _get_coordinate_photo(width_row, height_row, size) -> tuple:
        """Вычисление координат фотографии на канвасе"""
        _height_row = height_row
        _width_row = width_row
        _new_page = False
        _new_row = False
        if _width_row + size[0] > 210 and _width_row > 0:
            _width_row = 0
            if _height_row + size[1] > 297 and _height_row > 0:
                _height_row = 0
                _new_page = True
            else:
                _height_row = _height_row + size[1] + 10
                _new_row = True
        else:
            _width_row = _width_row + size[0]
        return _width_row, _height_row, _new_page, _new_row

    def _create_size_photo(self, img: ImageTk):
        """Формирование размера фотографии"""
        width = int(self._width_photo / int(self._request_field.get()))
        height = int(img.size[1] / img.size[0] * width)
        return width, height

    def _open_directory(self):
        f = filedialog.askdirectory()
        self._url_field.delete(0, END)
        self._url_field.insert(0, f)

    def _rout_img(self, events):
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        print(f"Вы кликнули по изображению №: {tag_img}")
        self.all_img[tag_img].rotation()


class PhotoPage:
    """Страница с фотографиями"""


class PhotoRow:
    """Строка с изображениями"""

    def __init__(self, canvas: Canvas, length: int):
        pass


class CustomImg:
    def __init__(
        self,
        canvas: Canvas,
        img: Image,
        width: int,
        max_img_in_row: int,
        width_row: int,
        height_row: int,
        count: int,
        callback,
    ):
        self.canvas = canvas
        self.img = img
        self.width = width
        self.max_img_in_row = max_img_in_row
        self.width_row = width_row
        self.height_row = height_row
        self.tag = f"img_{count}"
        self.callback = callback
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)
        self.add_img_in_canvas()

    def _create_img_in_docs(self) -> Image:
        """Формирование размера фотографии"""
        width = int(self.width / self.max_img_in_row)
        height = int(self.img.size[1] / self.img.size[0] * width)
        return self.img.resize((width, height))

    def rotation(self):
        """Поворот изображения на 90 градусов"""
        self.img = self.img.rotate(90, expand=1)
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)
        self.add_img_in_canvas()

    def add_img_in_canvas(self):
        """Добавление изображения на канвас"""
        img_name = self.canvas.create_image(self.width_row, self.height_row, anchor=NW, image=self.tk_img, tag=self.tag)
        self.canvas.tag_bind(img_name, "<Button-1>", self.callback)


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
