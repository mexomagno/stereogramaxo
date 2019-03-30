"""Logging tool."""

import logging
import sys
from logging.handlers import RotatingFileHandler


class _ColoredFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    COLORS = {
        'WARNING': YELLOW,
        'INFO': WHITE,
        'DEBUG': BLUE,
        'CRITICAL': YELLOW,
        'ERROR': RED
    }

    def __init__(self, msg, use_color=True, color_all=False, *args, **kwargs):
        """
        Constructor.

        Parameters
        ----------
        msg: str
            What to put on log
        use_color: bool
            if user wants colored output
        color_all: bool
            If true, color all characters. Else, color only the levelname

        """
        logging.Formatter.__init__(self, msg, *args, **kwargs)
        self.use_color = use_color
        self.color_all = color_all

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in _ColoredFormatter.COLORS:
            if self.color_all:
                message = logging.Formatter.format(self, record)
                message = _ColoredFormatter.COLOR_SEQ % (30 + _ColoredFormatter.COLORS[levelname]) \
                          + message + _ColoredFormatter.RESET_SEQ
                return message
            else:
                levelname_color = _ColoredFormatter.COLOR_SEQ % (30 + _ColoredFormatter.COLORS[levelname]) \
                                  + levelname + _ColoredFormatter.RESET_SEQ
                record.levelname = levelname_color
        return logging.Formatter.format(self, record)


logger = logging.getLogger('stereogramaxo')
logger.setLevel('DEBUG')
# handlers
file_formatter = _ColoredFormatter('[%(asctime)s] %(levelname)s %(message)s', color_all=True)
console_formatter = _ColoredFormatter('[%(asctime)s] %(levelname)s %(message)s', color_all=True, datefmt='%H:%M:%S')
rotating_file_handler = RotatingFileHandler('sirds.log', maxBytes=2048, backupCount=2)
console_handler = logging.StreamHandler(sys.stdout)
rotating_file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)
logger.addHandler(rotating_file_handler)
logger.addHandler(console_handler)


class Log:
    @staticmethod
    def d(s):
        logger.debug(s)

    @staticmethod
    def i(s):
        logger.info(s)

    @staticmethod
    def w(s):
        logger.warning(s)

    @staticmethod
    def e(s):
        logger.error(s)

    @staticmethod
    def c(s):
        logger.critical(s)

