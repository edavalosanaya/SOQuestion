import logging
import logging.handlers
import logging.config
import socket
from collections import deque
import pickle
import threading
import multiprocessing as mp

import pytest
from pytest_lazyfixture import lazy_fixture


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
        "datagram": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.handlers.DatagramHandler",
            "host": "127.0.0.1",
            "port": 5555
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "subprocess": {
            "handlers": ["datagram"],
            "level": "DEBUG",
            "propagate": True
        }
    },
}

# Setup the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

@pytest.fixture
def logreceiver():

    def listener():

        # Create server and logger to relay messages
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 5555))
        logger = logging.getLogger("")

        # Continue listening until signaled to stop
        while True:

            # Listen for information
            data = s.recv(4096)
            if data == b"die":
                break

            # Dont forget to skip over the 32-bit length prepended
            logrec = pickle.loads(data[4:])
            rec = logging.LogRecord(
                name=logrec['name'],
                level=logrec['levelno'],
                pathname=logrec['pathname'],
                lineno=logrec['lineno'],
                msg=logrec['msg'],
                args=logrec['args'],
                exc_info=logrec['exc_info'],
                func=logrec['funcName'],

            )
            logger.handle(rec)

        # Safely shutdown socket
        s.close()

    # Start relaying thread
    receiver_thread = threading.Thread(target=listener)
    receiver_thread.start()

    yield

    # Shutting down thread
    t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t.sendto(b"die", ("127.0.0.1", 5555))
    receiver_thread.join()

def target_function():

    # Depending on the type of process, get the logger
    if 'Fork' in mp.current_process().name:
        logger = logging.getLogger("")
    elif "Spawn" in mp.current_process().name:
        logger = logging.getLogger("subprocess")
    else:
        raise RuntimeError("Invalid multiprocessing spawn method.")

    # Test logging
    logger.info("Children Logging")


@pytest.mark.parametrize(
    "_logreceiver, ctx",
    [
        (lazy_fixture("logreceiver"), mp.get_context("spawn")),
        (lazy_fixture("logreceiver"), mp.get_context("fork")),

    ]
    )
def test_something(_logreceiver, ctx):

    # Try different methods
    logger = logging.getLogger("")
    logger.info("Parent logging")

    ps = []
    for i in range(3):
        p = ctx.Process(target=target_function)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

    logger.info("Parent logging: end")