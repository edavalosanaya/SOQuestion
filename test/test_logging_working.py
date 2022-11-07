from typing import Literal, Optional
import logging
import logging.handlers
import logging.config
import socket
from collections import deque
import pickle
import threading
import multiprocessing as mp
import platform

import pytest
from pytest_lazyfixture import lazy_fixture

def configure_logger():

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
   
configure_logger()

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
    logger.info(f"{mp.current_process().name} - Children Logging")

# ctx = mp.get_context("spawn")
# ctx = mp
class CustomProcess(mp.Process):

    def __init__(self, context: Optional[Literal['spawn', 'fork']] = None):

        # Mapping str to class
        start_to_class_map = {
            "fork": mp.context.ForkProcess,
            "spawn": mp.context.SpawnProcess
        }

        # If no context is given, use the default 
        if not context:
            default = mp.get_start_method()
            assert isinstance(default, str)
            self.__class__.__bases__ = (start_to_class_map[default],)
            self._context = default

        else:
            if context in mp.get_all_start_methods():
                self._context = context
                self.__class__.__bases__ = (start_to_class_map[context], )
            else:
                raise RuntimeError(f"Context: `{context}` invalid in {platform.system()}")

        super().__init__(daemon=True)

    def get_logger(self) -> logging.Logger:
        
        # Depending on the type of process, get the logger
        if self._context == "spawn":
            logger = logging.getLogger("subprocess")
        elif self._context == "fork":
            logger = logging.getLogger("")
        else:
            raise RuntimeError("Invalid multiprocessing spawn method.")

        return logger

    def run(self):

        # Get the logger
        self.logger = self.get_logger()

        # Test logging
        # self.logger.info(f"{mp.current_process().name} - Children Logging")
        self.logger.info(f"{self.__class__.__bases__} - Children Logging")

# ctx = mp
fctx = mp.get_context("fork")
class CustomForkProcess(fctx.Process):

    def get_logger(self) -> logging.Logger:
        
        # Depending on the type of process, get the logger
        subclass = self.__class__.__bases__[0]
        if subclass == mp.context.ForkProcess or (subclass == mp.context.Process and platform.system() == "Linux"):
            logger = logging.getLogger("")
        elif subclass == mp.context.SpawnProcess or (subclass == mp.context.Process and platform.system() != "Linux"):
            logger = logging.getLogger("subprocess")
        else:
            raise RuntimeError("Invalid multiprocessing spawn method.")

        return logger

    def run(self):

        # Get the logger
        self.logger = self.get_logger()

        # Test logging
        self.logger.info(f"{mp.current_process().name} - Children Logging")

sctx = mp.get_context("spawn")
class CustomSpawnProcess(sctx.Process):

    def get_logger(self) -> logging.Logger:
        
        # Depending on the type of process, get the logger
        subclass = self.__class__.__bases__[0]
        if subclass == mp.context.ForkProcess or (subclass == mp.context.Process and platform.system() == "Linux"):
            logger = logging.getLogger("")
        elif subclass == mp.context.SpawnProcess or (subclass == mp.context.Process and platform.system() != "Linux"):
            logger = logging.getLogger("subprocess")
        else:
            raise RuntimeError("Invalid multiprocessing spawn method.")

        return logger

    def run(self):

        # Get the logger
        self.logger = self.get_logger()

        # Test logging
        self.logger.info(f"{mp.current_process().name} - Children Logging")


@pytest.mark.parametrize(
    "_logreceiver, ctx",
    [
        (lazy_fixture("logreceiver"), mp.get_context("spawn")),
        (lazy_fixture("logreceiver"), mp.get_context("fork")),

    ]
)
def test_target_function_in_process(_logreceiver, ctx):

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

def test_spawn_custom_process(logreceiver):

    # Try different methods
    logger = logging.getLogger("")
    logger.info("Parent logging")
    logger.info(CustomSpawnProcess.__bases__)

    ps = []
    for i in range(3):
        p = CustomSpawnProcess(target=target_function)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

    logger.info("Parent logging: end")

def test_fork_custom_process(logreceiver):

    # Try different methods
    logger = logging.getLogger("")
    logger.info("Parent logging")
    logger.info(CustomSpawnProcess.__bases__)

    ps = []
    for i in range(3):
        p = CustomForkProcess(target=target_function)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

    logger.info("Parent logging: end")

@pytest.mark.parametrize(
    "_logreceiver, ctx",
    [
        (lazy_fixture("logreceiver"), None),
        (lazy_fixture("logreceiver"), "spawn"),
        (lazy_fixture("logreceiver"), "fork"),

    ]
)
def test_change_custom_process(_logreceiver, ctx):

    # Try different methods
    logger = logging.getLogger("")
    logger.info("Parent logging")
    

    ps = []
    for i in range(3):
        p = CustomProcess(context=ctx)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

    logger.info("Parent logging: end")
