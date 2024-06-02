class ValidationError(Exception):
    """用於檢查資料合法性的例外。"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
