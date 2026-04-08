import logging
from pathlib import Path


def setup_logger(name: str, level: str, log_dir: Path, log_file: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.FileHandler(log_dir / log_file)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
