import pstats
import sys
import time

from pathlib import Path
from subprocess import run, PIPE, DEVNULL
from typing import Union, Literal

from pyinstrument import Profiler as PyProfiler
from cProfile import Profile as cProfiler


class RawTimer:
    start: int
    end: int
    duration: float

    def __enter__(self):
        self.start = time.perf_counter_ns()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter_ns()
        self.duration = (self.end - self.start) / 1e9


class Profiler:
    def __init__(
        self,
        prof_type: Union[Literal["py"], Literal["c"], Literal["raw"]],
        output_directory: str,
        benchmark_name: str,
    ):
        self._prof: Union[PyProfiler, cProfiler, RawTimer] = {
            "py": PyProfiler,
            "c": cProfiler,
            "raw": RawTimer,
        }[prof_type]()
        self._prof_type: Union[Literal["py"], Literal["c"], Literal["raw"]] = prof_type
        self._root_frame = None
        self._state = "out"
        self._output_directory = output_directory
        self._benchmark_name = benchmark_name

    def __enter__(self):
        self._prof.__enter__()
        self._state = "in"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._prof.__exit__(exc_type, exc_val, exc_tb)
        if self._prof_type == "py":
            self._root_frame = self._prof.last_session.root_frame()  # type: ignore
        self._state = "out"
        self.output()
        self.save()

    def save(self):
        if self._state != "out":
            raise ValueError
        if self._output_directory is None or self._benchmark_name is None:
            return
        git_commit = (
            run(
                ["git", "rev-parse", "--short", "HEAD"],
                stdout=PIPE,
                stderr=DEVNULL,
                check=False,
            )
            .stdout.strip()
            .decode()
        )
        git_dirty = (
            run(
                ["git", "diff", "--quiet"], stdout=DEVNULL, stderr=DEVNULL, check=False
            ).returncode
            != 0
        )
        version = git_commit + ("-dirty" if git_dirty else "")
        output_path = Path(self._output_directory) / (self._benchmark_name + ".csv")
        with output_path.open("a") as f:
            f.write(
                f"{version},{'.'.join(map(str, sys.version_info[:3]))},{self.get_time()}\n"
            )

    def output(self):
        if self._state != "out":
            raise ValueError
        if self._prof_type == "py":
            print(self._prof.output_text(unicode=True, color=True))  # type: ignore
        elif self._prof_type == "c":
            self._prof.print_stats("cumtime")  # type: ignore
        elif self._prof_type == "raw":
            print(f"{self._prof.duration:.4} s")  # type: ignore

    def get_time(self) -> float:
        if self._state != "out":
            raise ValueError
        if self._prof_type == "py":
            return self._root_frame.time  # type: ignore
        elif self._prof_type == "c":
            return pstats.Stats(self._prof).total_tt  # type: ignore
        elif self._prof_type == "raw":
            return self._prof.duration  # type: ignore
