import logging
import logging.config
from datetime import datetime
from pathlib import Path

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            "style": "{",
            "format": "{asctime} [{levelname}] {filename}:{lineno}: {message}",
            "datefmt": "%Y-%m-%dT%H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": logging.INFO,
            "formatter": "base",
        },
        "file_log": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": logging.DEBUG,
            "formatter": "base",
            "filename": Path(__file__, '..', '..', 'log', 'xenianalysis.log').resolve(),
            "mode": "a",
            "maxBytes": 1024 * 5
        }
    },
    "loggers": {"": {"handlers": ["console", "file_log"], "level": "DEBUG"}},
}


logging.config.dictConfig(LOGGING)


def getLogger(name, level=None):
    if name is None:
        raise ValueError('provide logger name')
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger


def log_runtime(logger, level=logging.DEBUG):
    def decorator(func):
        func_name = func.__name__

        def _calc_duration(start, error=False):
            end = datetime.now()
            dur = end - start
            status = 'failed' if error else 'successful'
            logger.log(level, f'{status} execution of {func_name} took {dur}')

        def func_timing_wrapper(*args, **kwargs):
            logger.log(level, f'starting time monitored execution of {func_name}')

            start = datetime.now()
            try:
                r =func(*args, **kwargs)
            except Exception:
                _calc_duration(start, error=True)
                raise
            _calc_duration(start)
            return r
        return func_timing_wrapper
    return decorator


def set_global_log_level_debug():
    LOGGING["handlers"]["console"]["level"] = logging.DEBUG
    logging.config.dictConfig(LOGGING)