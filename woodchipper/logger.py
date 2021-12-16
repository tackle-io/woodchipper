import copy
import sys
import threading
from pickle import PicklingError
from typing import IO, Any, Dict, Optional, TextIO

from structlog._utils import until_not_interrupted

WRITE_LOCKS: Dict[IO[Any], threading.Lock] = {}


def _get_lock_for_file(file: IO[Any]) -> threading.Lock:
    global WRITE_LOCKS

    lock = WRITE_LOCKS.get(file)
    if lock is None:
        lock = threading.Lock()
        WRITE_LOCKS[file] = lock

    return lock


class SimpleLogger:
    def __init__(self, name: str = "", file: Optional[TextIO] = None):
        self.name = name
        self._file = file or sys.stdout
        self._write = self._file.write
        self._flush = self._file.flush

        self._lock = _get_lock_for_file(self._file)

    def __getstate__(self) -> str:
        if self._file is sys.stdout:
            return "stdout"

        elif self._file is sys.stderr:
            return "stderr"

        raise PicklingError("Only SimpleLogger to sys.stdout and sys.stderr can be pickled.")

    def __setstate__(self, state: Any) -> None:
        if state == "stdout":
            self._file = sys.stdout
        else:
            self._file = sys.stderr

        self._write = self._file.write
        self._flush = self._file.flush
        self._lock = _get_lock_for_file(self._file)

    def __deepcopy__(self, memodict: Dict[Any, Any] = {}) -> "SimpleLogger":
        if self._file not in (sys.stdout, sys.stderr):
            raise copy.error("Only SimpleLoggers to sys.stdout and sys.stderr " "can be deepcopied.")

        newself = self.__class__(self._file)

        newself._write = newself._file.write
        newself._flush = newself._file.flush
        newself._lock = _get_lock_for_file(newself._file)

        return newself

    def __repr__(self) -> str:
        return f"<SimpleLogger(name={self.name},file={self._file!r})>"

    def msg(self, message: str) -> None:
        """
        Print *message*.
        """
        with self._lock:
            until_not_interrupted(self._write, message + "\n")
            until_not_interrupted(self._flush)

    log = debug = info = warn = warning = error = exception = msg


class SimpleLoggerFactory:
    def __init__(self, file: Optional[TextIO] = None):
        self._file = file

    def __call__(self, name: str = "") -> SimpleLogger:
        return SimpleLogger(name, self._file)
