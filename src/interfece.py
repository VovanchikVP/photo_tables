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

from PIL import ImageTk

from src.create_docx import CreateDocx
from src.run_process import RunProcess


class LoadTester(Tk):
    def __init__(self, loop, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self._queue = Queue()
        self._refresh_ms = 25
        self.row_img_table = 5
        self._width_photo = 200
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
        # self._canvas_table = Canvas(
        #     self, bg="white", height=700, width=210, scrollregion=(0, 0, 600, 210)
        # )
        # vbar = Scrollbar(self, orient=VERTICAL)
        # vbar.grid(row=self.row_img_table, column=5)
        # vbar.config(command=self._canvas_table.yview)
        # self._canvas_table.config(yscrollcommand=vbar.set)
        # self._canvas_table.config(width=300, height=300)
        # self._canvas_table.grid(row=self.row_img_table, column=0, columnspan=4)

        # f = Frame(self, bg="white", height=297, width=210, padx=10, pady=10, relief='raised', borderwidth=2)
        f = ScrollableFrame(self)
        f.grid(row=self.row_img_table, column=0, columnspan=4)
        f.grid_propagate(0)
        # v_scrollbar = Scrollbar(self, orient="vertical", command=c.yview)
        # c.configure(yscrollcommand=v_scrollbar.set)
        # v_scrollbar.grid(row=self.row_img_table, column=5)
        # c.grid(row=self.row_img_table, column=0, columnspan=4)
        # c.create_window(0, 0, window=f, anchor="nw")

        for i in range(1000):
            Label(f.scrollable_frame, wraplength=350, text=f"Строка №{i}").grid()
        # c.update_idletasks()
        # c.configure(scrollregion=c.bbox("all"))

    def _create_image_table(
        self,
    ):
        count = 0
        if self._canvas_table is not None:
            self._canvas_table.grid_remove()
        _width = self._width_photo * self._last_obj.col + self._last_obj.col
        self._canvas_table = Canvas(
            self, bg="white", height=_width, width=_width, scrollregion=(0, 0, _width * 2, _width * 2)
        )
        self._canvas_table.grid(row=self.row_img_table, column=0, columnspan=4)
        _height_row = 0
        _height_row_after = 0
        for row in range(self._last_obj.row):
            for col in range(self._last_obj.col):
                if count < len(self._last_obj.files):
                    img = self._last_obj.files[count]
                    size = self._width_photo, int(img.size[1] / img.size[0] * self._width_photo)
                    if _height_row_after < _height_row + size[1]:
                        _height_row_after = _height_row + size[1]
                    img = img.resize(size)
                    setattr(self, f"img_{count}", ImageTk.PhotoImage(img))
                    self._canvas_table.create_image(
                        col * size[0], _height_row, anchor=NW, image=getattr(self, f"img_{count}")
                    )
                    count += 1
            _height_row = _height_row_after

    def _open_directory(self):
        f = filedialog.askdirectory()
        self._url_field.delete(0, END)
        self._url_field.insert(0, f)


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
