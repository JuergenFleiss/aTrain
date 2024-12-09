import sys
from threading import Thread


class StoppableThread(Thread):
    def __init__(self, target=None, args=(), kwargs=None, daemon: bool | None = None):
        Thread.__init__(self, target=target, args=args, kwargs=kwargs)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == "call":
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == "line":
                raise SystemExit()
        return self.localtrace

    def stop(self):
        self.killed = True
