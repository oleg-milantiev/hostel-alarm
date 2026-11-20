"""
Android Logcat logging handler for BeeWare/Toga + Chaquopy.
print() does not reach logcat on Android — this bridges logging to android.util.Log.
"""

import logging
import sys
import threading

from java import jclass

AndroidLog = jclass("android.util.Log")


class AndroidLogHandler(logging.Handler):
    """Writes log records to Android Logcat via android.util.Log."""

    LEVEL_MAP = {
        logging.DEBUG: AndroidLog.DEBUG,
        logging.INFO: AndroidLog.INFO,
        logging.WARNING: AndroidLog.WARN,
        logging.ERROR: AndroidLog.ERROR,
        logging.CRITICAL: AndroidLog.ASSERT,
    }

    def __init__(self, tag="HostelAlarm"):
        super().__init__()
        self.tag = tag

    def emit(self, record):
        try:
            message = self.format(record)
            priority = self.LEVEL_MAP.get(
                record.levelno,
                AndroidLog.INFO,
            )
            # Android Logcat limits message length (~4KB)
            for line in message.splitlines() or [""]:
                AndroidLog.println(priority, self.tag, line)
        except Exception:
            self.handleError(record)


def setup_logging(level=logging.DEBUG):
    """Set up logging to Android Logcat. Call once at app startup."""
    logger = logging.getLogger()
    if any(isinstance(h, AndroidLogHandler) for h in logger.handlers):
        return logger

    handler = AndroidLogHandler("HostelAlarm")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level)

    # Catch unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger = logging.getLogger("HostelAlarm")
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    def handle_thread_exception(args):
        logger = logging.getLogger("HostelAlarm")
        logger.critical(
            "Unhandled thread exception",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception

    return logger
