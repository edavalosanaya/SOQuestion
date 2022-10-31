import multiprocessing as mp
import sys

# Selecting method
LOGGING_METHOD = 1
START_METHOD = "spawn"
# START_METHOD = "fork"

# Imports
if LOGGING_METHOD == 1:
    import logging
    import logging.config

elif LOGGING_METHOD == 2:
    from logger_tt import setup_logging, logger

elif LOGGING_METHOD == 3:
    from loguru import logger

    # References:
    #[Loguru + mp](https://loguru.readthedocs.io/en/stable/resources/recipes.html#compatibility-with-multiprocessing-using-enqueue-argument)

def configure_logger():
    
    LOGGING_CONFIG = { 
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': { 
            'standard': { 
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': { 
            'default': { 
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',  # Default is stderr
            },
        },
        'loggers': { 
            'test': {  # root logger
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': False
            }
        } 
    }

    logging.config.dictConfig(LOGGING_CONFIG)

def configure_loguru():

    logger.remove()
    logger.add(sys.stdout, enqueue=True)

# Configure Logger only on main process
if mp.current_process().name == "MainProcess":
    
    # Main process setup
    if LOGGING_METHOD == 1:
        configure_logger()
    elif LOGGING_METHOD == 2:
        setup_logging(full_context=1, use_multiprocessing=True)
    elif LOGGING_METHOD == 3:
        configure_loguru()


# Required for method 1
if LOGGING_METHOD == 1:
    logger = logging.getLogger('test')


def target_function():

    if LOGGING_METHOD == 1:
        configure_logger()
    if LOGGING_METHOD == 2 and 'Spawn' in mp.current_process().name:
        setup_logging(full_context=1, use_multiprocessing=True)
    if LOGGING_METHOD == 3:
        configure_loguru()

    logger.info("Children Logging")


if __name__ == "__main__":

    # To do cross platform, it must work with process spawn method
    # [Multiprocessing Start Methods](https://superfastpython.com/multiprocessing-start-method/)
    ctx = mp.get_context(START_METHOD)
    
    logger.info("Parent logging")

    ps = []
    for i in range(3):
        p = ctx.Process(target=target_function)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

    logger.info("Parent logging: end")
