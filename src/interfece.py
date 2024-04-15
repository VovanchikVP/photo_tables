from queue import Queue
from tkinter import (
    END,
    NW,
    Canvas,
    Entry,
    Frame,
    Label,
    N,
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
        self._save_bt = ttk.Button(self, text="Сохранить", command=self._save)
        # self._save_bt.grid(column=3, row=1)
        self._pb_label = Label(self, text="Progress:")
        self._pb_label.grid(column=0, row=3)
        self._pb = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self._pb.grid(column=1, row=3, columnspan=2)
        self.bind_all("<BackSpace>", self._del_img)
        self.bind_all("<Delete>", self._del_img)
        self.bind_all("<r>", self._rout_img)
        self.bind_all("<Up>", self._move_img)
        self.bind_all("<Down>", self._move_img)
        self.bind_all("<Left>", self._move_img)
        self.bind_all("<Right>", self._move_img)
        # self.bind_all("<KeyPress>", lambda e: print(e))

    def _update_bar(self, pct: int):
        if pct == 100:
            self._pb["value"] = pct
            self._load_test = None
            self._submit["text"] = "Сформировать"
            self._create_canvas()
            self._save_bt.grid(column=0, columnspan=4, row=self.row_img_table + 1)
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

    def _save(self):
        """Сохранение результатов в Документе word"""

        self._save_bt["text"] = "---"
        url = filedialog.asksaveasfile(filetypes=[("Microsoft Word", "*.docx")])
        self._last_obj.run_save(self._save_finished, url)

    def _save_finished(self):
        self._save_bt["text"] = "Сохранить"

    def _create_canvas(self):
        """Формирование канваса для фото таблицы"""
        _photo_in_row = int(self._request_field.get())
        f = ScrollableFrame(self)
        f.grid(row=self.row_img_table, column=0, columnspan=4)
        f.configure(borderwidth=2, relief="raised")
        f.grid_propagate(False)
        canvas = PhotoPage(f.scrollable_frame, 210, 297)
        row = PhotoRow(_photo_in_row)
        for count in range(len(self._last_obj.files)):
            if not row.add(self._last_obj.files, count, self._callbacks()):
                if not canvas.add(row):
                    canvas = self._add_row_in_new_page(f.scrollable_frame, canvas, row)
                new_row = PhotoRow(_photo_in_row, before_row=row)
                row.next_row = new_row
                row = new_row
                row.add(self._last_obj.files, count, self._callbacks())
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
        self.all_img[tag_img].rotation(events)

    def _move_img(self, events):
        """Перемещение изображения в канвасе"""
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        num = int(tag_img.split("_")[-1])
        obj = self._last_obj.files.pop(num)
        _photo_in_row = int(self._request_field.get())
        if events.keysym == "Left":
            if not num:
                self._last_obj.files.append(obj)
            else:
                self._last_obj.files.insert(num - 1, obj)
        elif events.keysym == "Right":
            if num == len(self._last_obj.files):
                self._last_obj.files.insert(0, obj)
            else:
                self._last_obj.files.insert(num + 1, obj)
        elif events.keysym == "Up":
            new_position = num - _photo_in_row
            if new_position >= 0:
                self._last_obj.files.insert(new_position, obj)
            else:
                new_position = (new_position + 1) * -1
                if new_position:
                    self._last_obj.files.insert(len(self._last_obj.files) - new_position, obj)
                else:
                    self._last_obj.files.append(obj)
        elif events.keysym == "Down":
            new_position = num + _photo_in_row
            if new_position <= len(self._last_obj.files):
                self._last_obj.files.insert(new_position, obj)
            else:
                new_position = new_position - len(self._last_obj.files) - 1
                self._last_obj.files.insert(new_position, obj)
        self._create_canvas()

    def _del_img(self, events):
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        print(f"Вы удалили изображение №: {tag_img}")
        del self._last_obj.files[int(tag_img.split("_")[-1])]
        self._create_canvas()

    def _add_border(self, events):
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        self.all_img[tag_img].add_border(events)

    def _remove_border(self, events):
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        self.all_img[tag_img].drop_border(events)

    def _move(self, events):
        """Перемещение картинки"""
        current = events.widget.find_withtag("current")[0]
        tag_img = str(events.widget.itemconfig(current)["tags"][-1].split(" ")[0])
        self.all_img[tag_img].move(events)

    def _callbacks(self) -> dict:
        """Функции обратного вызова"""
        return {
            "<Enter>": self._add_border,
            "<Leave>": self._remove_border,
        }


class PhotoRow:
    """Строка с изображениями"""

    MAX_WIDTH_ROW = 160

    def __init__(self, length: int, before_row=None, next_row=None):
        self.before_row: Optional["PhotoRow"] = before_row
        self.next_row: Optional["PhotoRow"] = next_row
        self.row_position = None
        self.photo_page: Optional["PhotoPage"] = None
        self.length = length
        self.img_width = int(self.MAX_WIDTH_ROW / self.length)
        self.height = 0
        self.images: list[CustomImg] = []

    def add(self, img_list: list[Image], index: int, callbacks: dict) -> bool:
        """Добавление изображения в строку"""
        if len(self.images) == self.length:
            return False
        img_cast = CustomImg(img_list, self.img_width, index, callbacks)
        img_cast.photo_row = self
        self.images.append(img_cast)
        self.calculation_height()
        return True

    def add_row_in_canvas(self, photo_page: "PhotoPage" = None, row_position: int = None) -> None:
        """Добавление строки на канвас"""
        self.photo_page = photo_page if photo_page is not None else self.photo_page
        self.row_position = row_position if row_position is not None else self.row_position
        pad = int((self.photo_page.width - self.MAX_WIDTH_ROW) / 2)
        for num, img in enumerate(self.images):
            position_img_in_row = num * self.img_width + pad
            img.add_img_in_canvas(self.photo_page, position_img_in_row, self.row_position)

    def calculation_height(self) -> bool:
        new_height = max([i.all_height for i in self.images])
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
            return True
        else:
            return False


class CustomImg:
    FONT = ("Times", "8", "italic")
    IMG_PAD = 2

    def __init__(
        self,
        img_list: list[Image],
        img_width: int,
        index: int,
        callbacks: dict,
    ):
        self.img_width = img_width
        self.img_height = 0
        self.img_name_height = 20
        self.page: Optional["PhotoPage"] = None
        self.photo_row: Optional[PhotoRow] = None
        self.img_list = img_list
        self.index = index
        self.file_name = self.img_list[self.index][1]
        self.width_row = None
        self.height_row = None
        self.text_width = None
        self.border = None
        self.tag = f"img_{index}"
        self.text_item = None
        self.img_item = None
        self.callback = callbacks
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)
        self._calculation_text_obj_height()

    @property
    def all_height(self) -> int:
        return self.img_height + self.text_width + 2

    def _create_img_in_docs(self) -> Image:
        """Формирование размера фотографии"""
        wight = self.img_width - self.IMG_PAD * 2
        img = self.img_list[self.index][0]
        self.img_height = int(img.size[1] / img.size[0] * wight)
        return img.resize((wight, self.img_height))

    def _calculation_text_obj_height(self) -> None:
        """Вычисление высоты текста"""
        test_canvas = Canvas(bg="white", height=1000, width=1000)
        item = test_canvas.create_text(0, 0, text=self.file_name, width=self.img_width - 6, anchor=N, font=self.FONT)
        text_box = test_canvas.bbox(item)
        self.text_width = text_box[-1] - text_box[1]
        test_canvas.destroy()

    def rotation(self, events):
        """Поворот изображения на 90 градусов"""
        if events.keysym == "Right":
            self.img_list[self.index][0] = self.img_list[self.index][0].rotate(90, expand=1)
        elif events.keysym == "Left":
            self.img_list[self.index][0] = self.img_list[self.index][0].rotate(-90, expand=1)
        else:
            self.img_list[self.index][0] = self.img_list[self.index][0].rotate(90, expand=1)
        self.img_in_doc = self._create_img_in_docs()
        self.tk_img = ImageTk.PhotoImage(self.img_in_doc)
        if not self.photo_row.calculation_height():
            self.page.canvas.delete(self.img_item)
            self.page.canvas.delete(self.text_item)
            self.add_img_in_canvas()

    def add_border(self, events):
        """Удаление изображения"""
        self.page.canvas.focus_set()
        element_ids = self.page.canvas.find_withtag("current")
        self.page.canvas.focus(element_ids)
        x, y = self.page.canvas.coords(element_ids[0])
        self.create_border(x, y)

    def create_border(self, x: float, y: float):
        """Формирование прямоугольник"""
        if self.border is None:
            self.border = self.page.canvas.create_rectangle(
                x - 1, y - 1, x + self.img_width, y + self.img_height, outline="red"
            )
            self.page.canvas.tag_lower(self.border)

    def drop_border(self, events):
        if self.border is not None:
            self.page.canvas.delete(self.border)
            self.border = None

    def move(self, events):
        """Перемещение картинки"""
        self.page.canvas.moveto(self.img_item, events.x, events.y)
        self.page.canvas.moveto(self.text_item, events.x - 3, events.y + self.img_height)

    def add_img_in_canvas(self, page: "PhotoPage" = None, width_row: int = None, height_row: int = None):
        """Добавление изображения на канвас"""
        self.page = page if page else self.page
        self.width_row = self.width_row if width_row is None else width_row
        self.height_row = self.height_row if height_row is None else height_row
        self.img_item = self.page.canvas.create_image(
            self.width_row, self.height_row, anchor=NW, image=self.tk_img, tag=self.tag
        )
        for key, foo in self.callback.items():
            self.page.canvas.tag_bind(self.img_item, key, foo)
        self.text_item = self.page.canvas.create_text(
            self.width_row + self.img_width / 2,
            self.height_row + self.img_height,
            text=self.file_name,
            width=self.img_width - 6,
            anchor=N,
            font=self.FONT,
            fill="black",
        )


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = Canvas(self, width=300, height=600)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=5, column=0, columnspan=4)
        scrollbar.grid(row=5, column=5, sticky="ns")
        canvas.update_idletasks()


class PhotoPage:
    """Страница с фотографиями"""

    START_ROW_POSITION = 20
    BOTTOM_PAD = 20

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
        self.canvas.grid(pady=10, padx=45)
        self.rows: list[PhotoRow] = []

    def add(self, row: PhotoRow) -> bool:
        """Добавление строки"""
        if row.height + self.content_height > self.height - self.BOTTOM_PAD:
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
        height = self.START_ROW_POSITION
        for num, row in enumerate(self.rows):
            row.add_row_in_canvas(self, height)
            height += row.height
