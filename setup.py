from pathlib import Path
from setuptools import Command, setup
from setuptools.command.sdist import sdist
from setuptools.command.build import build


class SubmoduleMissingException(Exception):
    pass


class CustomSubmoduleCheck(Command):
    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        efd_path = Path("pyecsca/ec/efd")
        if not list(efd_path.iterdir()):
            raise SubmoduleMissingException(
                "The EFD submodule of pyecsca is missing, did you initialize the git submodules?"
            )
        std_path = Path("pyecsca/ec/std")
        if not list(std_path.iterdir()):
            raise SubmoduleMissingException(
                "The std-curves submodule of pyecsca is missing, did you initialize the git submodules?"
            )


class CustomSdist(sdist):
    sub_commands = [("check_submodules", None)] + sdist.sub_commands


class CustomBuild(build):
    sub_commands = [("check_submodules", None)] + build.sub_commands


setup(
    cmdclass={
        "sdist": CustomSdist,
        "build": CustomBuild,
        "check_submodules": CustomSubmoduleCheck,
    }
)
