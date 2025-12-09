log = None


def _log_record_exception(func):
    def _func(self):
        try:
            return func(self)
        except:
            log.exception(
                "log_exception|thread=%s:%s,file=%s:%s,func=%s:%s,log=%s",
                self.process,
                self.thread,
                self.filename,
                self.lineno,
                self.module,
                self.funcName,
                self.msg,
            )
            raise

    return _func


def append_exc(func):
    def _append_exc(*args, **kwargs):
        if "exc_info" not in kwargs:
            kwargs["exc_info"] = True
        return func(*args, **kwargs)

    return _append_exc


def init_logger(
    log_dir=None,
    sentry_dsn=None,
    environment=None,
    sentry_project_release=None,
    stdout=True,
    rollover_when="MIDNIGHT",
    rollover_backup_count=30,
):
    # pylint: disable=too-many-locals

    # if log_dir is None:
    # 	log_dir = './log'

    import os
    import sys

    error_msg = None

    handlers = {}
    if stdout:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
        }

    if log_dir:
        # write logs to file
        log_dir = os.path.abspath(log_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        handlers.update(
            {
                "file_fatal": {
                    "level": "CRITICAL",
                    "class": "dana.studio.api.core.logging_utils.loggingmp.MPTimedRotatingFileHandler",
                    "filename": os.path.join(log_dir, "fatal.log").replace("\\", "/"),
                    "when": rollover_when,
                    "backupCount": rollover_backup_count,
                    "formatter": "standard",
                },
                "file_error": {
                    "level": "WARNING",
                    "class": "dana.studio.api.core.logging_utils.loggingmp.MPTimedRotatingFileHandler",
                    "filename": os.path.join(log_dir, "error.log").replace("\\", "/"),
                    "when": rollover_when,
                    "backupCount": rollover_backup_count,
                    "formatter": "standard",
                },
                "file_info": {
                    "level": "DEBUG",
                    "class": "dana.studio.api.core.logging_utils.loggingmp.MPTimedRotatingFileHandler",
                    "filename": os.path.join(log_dir, "info.log").replace("\\", "/"),
                    "when": rollover_when,
                    "backupCount": rollover_backup_count,
                    "formatter": "short",
                },
                "file_data": {
                    "level": "DEBUG",
                    "class": "dana.studio.api.core.logging_utils.loggingmp.MPTimedRotatingFileHandler",
                    "filename": os.path.join(log_dir, "data.log").replace("\\", "/"),
                    "when": rollover_when,
                    "backupCount": rollover_backup_count,
                    "formatter": "data",
                },
            }
        )

    # Write logs to stdout
    logger_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "%(asctime)s.%(msecs)03d | %(levelname)s | %(process)d:%(thread)d %(threadName)s | %(filename)s:%(lineno)d | %(module)s.%(funcName)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "short": {
                "format": "%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "data": {
                "format": "%(asctime)s.%(msecs)03d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": handlers,
        "loggers": {
            "main": {
                "handlers": ["file_fatal", "file_error", "file_info"],
                "level": "DEBUG",
                "propagate": True,
            },
            "data": {
                "handlers": ["file_data"],
                "level": "DEBUG",
                "propagate": True,
            },
            "django.request": {
                "handlers": ["file_fatal", "file_error", "file_info"],
                "level": "ERROR",
                "propagate": True,
            },
            "tornado.access": {
                "handlers": ["file_data"],
                "level": "DEBUG",
                "propagate": True,
            },
            "tornado.application": {
                "handlers": ["file_fatal", "file_error", "file_info"],
                "level": "DEBUG",
                "propagate": True,
            },
            "tornado.general": {
                "handlers": ["file_fatal", "file_error", "file_info"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }

    is_django_app = False
    is_debug = False
    is_test = False

    if not is_django_app:
        try:
            import config

            is_debug = "DEBUG" in dir(config) and config.DEBUG
            is_test = "TEST" in dir(config) and config.TEST
        except ModuleNotFoundError as e:
            import logging

            error_msg = (
                f"{e} | Cannot found config.py in {os.getcwd()} | Use default parameters | is_debug : {is_debug} | is_test : {is_test}"
            )

    if is_debug:
        logger_config["handlers"]["file_debug"] = {
            "level": "DEBUG",
            "class": "core.logging_utils.loggingmp.MPTimedRotatingFileHandler",
            "filename": os.path.join(log_dir, "debug.log").replace("\\", "/"),
            "when": rollover_when,
            "backupCount": rollover_backup_count,
            "formatter": "standard",
        }
        # logger_config['loggers']['django.db.backends'] = {
        # 	'handlers': ['file_debug'],
        # 	'level': 'DEBUG',
        # 	'propagate': True,
        # }
    elif not is_test:
        loggers = logger_config["loggers"]
        for logger_item in loggers:
            if loggers[logger_item]["level"] == "DEBUG":
                loggers[logger_item]["level"] = "INFO"

    if not is_debug and sentry_dsn is not None:
        try:
            logger_config["handlers"]["sentry"] = {
                "level": "ERROR",
                "class": "raven.handlers.logging.SentryHandler",
                "dsn": sentry_dsn,
                # 'auto_log_stacks': True,
                "formatter": "short",
                "environment": environment,
                "release": sentry_project_release,
                "install_logging_hook": False,
                "enable_breadcrumbs": False,
                "install_sql_hook": False,
            }
            logger_config["loggers"]["django.request"]["handlers"].append("sentry")
            logger_config["loggers"]["main"]["handlers"].append("sentry")
        except Exception as _:
            pass

    if stdout:
        loggers = logger_config["loggers"]
        if not log_dir:
            for logger_item in loggers:
                loggers[logger_item]["handlers"] = ["console"]
        else:
            logger_config["loggers"]["main"]["handlers"].append("console")

    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
    recover_path = False
    if work_dir not in sys.path:
        sys.path.append(work_dir)
        recover_path = True

    import logging

    try:
        import logging.config

        logging.config.dictConfig(logger_config)
    except Exception as _:
        from . import loggerconfig

        loggerconfig.dictConfig(logger_config)

    if recover_path:
        sys.path.remove(work_dir)

    global log  # pylint: disable=global-statement
    log = logging.getLogger("main")
    log.exception = append_exc(log.error)
    log.assertion = log.critical
    log.data = logging.getLogger("data").info
    logging.LogRecord.getMessage = _log_record_exception(logging.LogRecord.getMessage)

    if error_msg is not None:
        try:
            log.error(error_msg)
        except Exception as _:
            pass


# try init log
def try_init_logger():
    try:
        import config

        init_logger(**config.LOGGER_CONFIG)
        print("Logger initialized with config :", config.LOGGER_CONFIG)
    except Exception as _:
        try:
            init_logger()
        except Exception as _:
            pass


if log is None:
    try_init_logger()

if log is None:
    import logging

    log = logging.getLogger("main")
    log.setLevel(logging.WARNING)
