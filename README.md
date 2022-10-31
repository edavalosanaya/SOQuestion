# SOQuestion: A Question about PyTest, Multiprocessing, and Logging

> :warning: This question requires Linux or a system that can (preferably a combination of Windows+Linux) support "spawn" and "fork" multiprocessing contexts.

**Question: How to perform pytest live-logging when using multiprocessing in a cross-platform setting?**

Welcome! I created this GitHub repo to help communicate my [SO question](https://stackoverflow.com/questions/74258805/how-to-perform-pytest-live-logging-when-using-multiprocessing-in-a-cross-platfor). Any help is greatly appreciated! The setup is would be rather laborious compared through SO instead of a simple:

```bash
git clone https://github.com/edavalosanaya/SOQuestion
```

## Setup Environment

Install the required packages through the following:

```bash
pip install -r requirements.txt
```

My testing environment is the following:
- Python 3.9
- Ubuntu 22.04 and Windows 11

## Requirements

I am trying to make live logging with the `pytest` framework work with multiprocessing. The solution requires to function in Windows, MacOS and Linux operating systems. When developing multiprocessing, it is important considering the start process method, these are the available methods for each OS according to this [reference](https://superfastpython.com/multiprocessing-start-method/):

- Windows: `spawn`
- MacOS: `spawn`, `fork`, `forkserver` (only `spawn` is stable, therby default)
- Linux: `spawn`, `fork`, `forkserver` (default `spawn`)

Avoid (if possible) using queues, servers, and custom pytest hooks.

Logs should go to the stdout or be visible in the terminal.

## Resources

Below is a collection of 

- Looked At Websites
    - [Multiprocessing logging in Python](https://superfastpython.com/multiprocessing-logging-in-python/)
    - [SO: Python Logging with Multiprocessing in Windows](https://stackoverflow.com/questions/26167873/python-logging-with-multiprocessing-in-windows)
    - [multiprocessing-logging library, only for POSIX](https://pypi.org/project/multiprocessing-logging/)
    - [SO: Python Multiprocessing returning results within Logging and running frozen on Windows](https://stackoverflow.com/questions/64335940/python-multiprocessing-returning-results-with-logging-and-running-frozen-on-wind)
- Relevent Library Documentations Pages
    - [Logger_tt](https://github.com/Dragon2fly/logger_tt#7-logging-in-multiprocessing)
    - [Loguru](https://loguru.readthedocs.io/en/stable/)
        - [Pytest + Loguru](https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog)
        - [Multiprocessing + Loguru](https://loguru.readthedocs.io/en/stable/resources/recipes.html#compatibility-with-multiprocessing-using-enqueue-argument)
    - [Pytest](https://docs.pytest.org/en/7.1.x/how-to/logging.html)

## The Test

First, I tried to see if three logging libraries (built-in `logging`, `logger_tt`, and `loguru`) worked with just multiprocessing, as done in `mp_logging.py`. In that file, there are 2 parameters `START_METHOD` and `LOGGING_METHOD`. 

After getting the 3 libraries to work with both `fork` and `spawn` process starting methods, I tried to replicate the test within the `pytest` framework. I was not able to capture the children logging with any library when using `spawn`. Given that Windows can only use `spawn`, this is not a solution.

## Expected Output

Built-in Logging (both `spawn` and `fork`)

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ python mp_logging.py
2022-10-30 23:07:15,019 [INFO] test: Parent logging
2022-10-30 23:07:15,084 [INFO] test: Children Logging
2022-10-30 23:07:15,086 [INFO] test: Children Logging
2022-10-30 23:07:15,087 [INFO] test: Children Logging
2022-10-30 23:07:15,095 [INFO] test: Parent logging: end
```

logger_tt (`spawn`)

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ python mp_logging.py
[2022-10-30 23:08:36] INFO: Parent logging
[2022-10-30 23:08:36] INFO: SpawnProcess-1 Children Logging
[2022-10-30 23:08:36] INFO: SpawnProcess-2 Children Logging
[2022-10-30 23:08:36] INFO: SpawnProcess-3 Children Logging
[2022-10-30 23:08:36] INFO: Parent logging: end
```

logger_tt (`fork`)

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ python mp_logging.py
[2022-10-30 23:09:42] INFO: Parent logging
[2022-10-30 23:09:42] INFO: SpawnProcess-1 Children Logging
[2022-10-30 23:09:42] INFO: SpawnProcess-2 Children Logging
[2022-10-30 23:09:42] INFO: SpawnProcess-3 Children Logging
[2022-10-30 23:09:42] INFO: Parent logging: end
```

loguru (both `spawn` and `fork`)

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ python mp_logging.py
2022-10-30 23:11:07.608 | INFO     | __main__:<module>:92 - Parent logging
2022-10-30 23:11:07.712 | INFO     | __mp_main__:target_function:83 - Children Logging
2022-10-30 23:11:07.713 | INFO     | __mp_main__:target_function:83 - Children Logging
2022-10-30 23:11:07.715 | INFO     | __mp_main__:target_function:83 - Children Logging
2022-10-30 23:11:07.731 | INFO     | __main__:<module>:103 - Parent logging: end
```

## Actual Output

`logging` and `logger_tt` on `fork`: Correct output

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ pytest
======================================== test session starts ========================================
platform linux -- Python 3.8.13, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/eduardo/GitHub/SOQuestion, configfile: pyproject.toml
collected 1 item                                                                                    

test/test_logging.py::test_logging_with_multiprocessing 
------------------------------------------- live log call -------------------------------------------
Parent logging
Children Logging
Children Logging
Children Logging
Parent logging: end
PASSED                                                                                        [100%]

========================================= 1 passed in 0.02s =========================================
```

`logging` and `logger_tt` on `spawn`: Missing children output

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ pytest
======================================== test session starts ========================================
platform linux -- Python 3.8.13, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/eduardo/GitHub/SOQuestion, configfile: pyproject.toml
collected 1 item                                                                                    

test/test_logging.py::test_logging_with_multiprocessing 
------------------------------------------- live log call -------------------------------------------
Parent logging
Parent logging: end
PASSED                                                                                        [100%]

========================================= 1 passed in 0.26s =========================================
```

`loguru` for both `spawn` and `fork`: no output

```bash
(test) eduardo@avocado-XPS-13-9300:~/GitHub/SOQuestion$ pytest
======================================== test session starts ========================================
platform linux -- Python 3.8.13, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/eduardo/GitHub/SOQuestion, configfile: pyproject.toml
collected 1 item                                                                                    

test/test_logging.py::test_logging_with_multiprocessing PASSED                                [100%]

========================================= 1 passed in 0.02s =========================================
```
