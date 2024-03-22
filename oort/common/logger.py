import os
from logging import DEBUG, FileHandler, Formatter, INFO, Logger, StreamHandler, getLogger

from .config import Config


def get_oort_logger(debug=False) -> Logger:
    suffix = '-tests' if os.environ.get('OORT_TESTS') == '1' else ''
    logger = getLogger('oort-cloud' + suffix)
    logger.setLevel(DEBUG if debug else INFO)

    if len(logger.handlers) == 0:
        formatter = Formatter('%(asctime)s - %(name)s[oort] - %(levelname)s - %(message)s')

        if os.environ.get('OORT_TESTS') != '1':
            file_handler = FileHandler(Config.log_file_path())
            file_handler.setLevel(DEBUG if debug else INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        console_handler = StreamHandler()
        console_handler.setLevel(DEBUG if debug else INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
