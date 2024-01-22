from queue import Queue
from tkinter import (
    NW,
    Canvas,
    Entry,
    Label,
    Tk,
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
        self._loop = loop
        self._load_test: Optional[CreateDocx] = None
        self._last_obj: Optional[CreateDocx] = None
        self.title("Формирование фототаблицы")
        self._url_label = Label(self, text="Путь:")
        self._url_label.grid(column=0, row=0)
        self._url_field = Entry(self, width=10)
        self._url_field.grid(column=1, row=0)
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

    def _update_bar(self, pct: int):
        if pct == 100:
            self._pb["value"] = pct
            self._load_test = None
            self._submit["text"] = "Сформировать"
            self._create_image_table()
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

    def _create_image_table(
        self,
    ):
        count = 0
        for row in range(self._last_obj.row):
            for col in range(self._last_obj.col):
                if count < len(self._last_obj.files):
                    img = self._last_obj.files[count]
                    size = img.size[0] // 5, img.size[1] // 5
                    img = img.resize(size)
                    setattr(self, f"img_{count}", ImageTk.PhotoImage(img))
                    canvas = Canvas(self, bg="white", height=size[1], width=size[0])
                    canvas.grid(row=row + self.row_img_table, column=col)
                    canvas.create_image(3, 3, anchor=NW, image=getattr(self, f"img_{count}"))
                    count += 1
