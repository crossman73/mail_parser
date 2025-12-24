import logging
from logging import Handler, LogRecord
from typing import Optional


class DBLogHandler(Handler):
    """Simple logging handler that writes records to src.core.log_store."""

    def __init__(self):
        super().__init__()
        try:
            from src.core import log_store
            self._store = log_store
        except Exception:
            self._store = None

    def emit(self, record: LogRecord) -> None:
        if not self._store:
            return
        try:
            msg = self.format(record)
            extra = {}
            # include positional args if present
            if record.args:
                try:
                    extra['args'] = record.args
                except Exception:
                    extra['args'] = str(record.args)
            # include exception info if present
            if record.exc_info:
                import traceback
                extra['exc_text'] = ''.join(
                    traceback.format_exception(*record.exc_info))
            self._store.write_log(record.levelname, msg, extra)
        except Exception:
            self.handleError(record)


def attach_db_handler(logger: Optional[logging.Logger] = None):
    logger = logger or logging.getLogger()
    handler = DBLogHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
