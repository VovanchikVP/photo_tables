class Configs:
    START_ROW_POSITION = 20
    BOTTOM_PAD = 20
    PAGE_HEIGHT = 297
    PAGE_WIDTH = 210
    DOCX_PAGE_HEIGHT = 10058400
    DOCX_PAGE_WIDTH = 7772400

    @classmethod
    def top_margin_docx(cls) -> int:
        return int(cls.START_ROW_POSITION / cls.PAGE_HEIGHT * cls.DOCX_PAGE_HEIGHT)

    @classmethod
    def bottom_margin_docx(cls) -> int:
        return int(cls.BOTTOM_PAD / cls.PAGE_HEIGHT * cls.DOCX_PAGE_HEIGHT)
