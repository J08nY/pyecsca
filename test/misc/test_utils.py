import time
from pyecsca.misc.utils import TaskExecutor


def run(a, b):
    return a + b


def wait(a, b):
    time.sleep(1)
    return a + b


def test_executor():
    with TaskExecutor(max_workers=2) as pool:
        for i in range(10):
            pool.submit_task(i,
                             run,
                             i, 5)
        for i, future in pool.as_completed():
            res = future.result()
            assert res == i + 5


def test_executor_no_wait():
    with TaskExecutor(max_workers=2) as pool:
        for i in range(2):
            pool.submit_task(i,
                             wait,
                             i, 5)
        futures = list(pool.as_completed(wait=False))
        assert len(futures) == 0
