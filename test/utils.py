import pstats
import sys

from pathlib import Path
from subprocess import run, PIPE, DEVNULL

from pyinstrument import Profiler as PyProfiler
from cProfile import Profile as cProfiler


class Profiler:
    def __init__(self, prof_type, output_directory, benchmark_name):
        self._prof = PyProfiler() if prof_type == "py" else cProfiler()
        self._prof_type = prof_type
        self._root_frame = None
        self._state = None
        self._output_directory = output_directory
        self._benchmark_name = benchmark_name

    def __enter__(self):
        self._prof.__enter__()
        self._state = "in"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._prof.__exit__(exc_type, exc_val, exc_tb)
        if self._prof_type == "py":
            self._root_frame = self._prof.last_session.root_frame()
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
            print(self._prof.output_text(unicode=True, color=True))
        else:
            self._prof.print_stats("cumtime")

    def get_time(self) -> float:
        if self._state != "out":
            raise ValueError
        if self._prof_type == "py":
            return self._root_frame.time
        else:
            return pstats.Stats(self._prof).total_tt  # type: ignore
