from gkeepcore.gkeep_exception import GkeepException


class GuiException(GkeepException):
    pass


class GuiFileException(GuiException):
    def set_path(self, path):
        self.path = path

    def get_path(self):
        return self.path
