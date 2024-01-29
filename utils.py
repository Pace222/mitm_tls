import threading


class Startable:
    def __init__(self, target, *args):
        self.target = target
        self.args = args

    def start(self):
        self.thread = threading.Thread(target=self.target, args=self.args)
        self.thread.start()

    def join(self):
        self.thread.join()


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
