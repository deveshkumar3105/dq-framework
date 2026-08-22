import logging


class ColoredFormatter(logging.Formatter):
    TEXT_COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[31m",
    }
    BG_COLORS = {
        "DEBUG": "\033[46m",
        "INFO": "\033[42m",
        "WARNING": "\033[43m",
        "ERROR": "\033[41m",
        "CRITICAL": "\033[41m",
    }
    RESET = "\033[0m"

    def format(self, record):
        text_color = self.TEXT_COLORS.get(record.levelname, "")
        bg_color = self.BG_COLORS.get(record.levelname, "")

        timestamp = self.formatTime(record, self.datefmt)
        level = f"{bg_color}{text_color}{record.levelname}{self.RESET}"
        message = record.getMessage()

        return f"{bg_color}{text_color}{timestamp}{self.RESET} {level} {message}"