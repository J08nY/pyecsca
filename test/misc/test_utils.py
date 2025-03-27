
from pyecsca.misc.utils import TaskExecutor


def run(a, b):
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
