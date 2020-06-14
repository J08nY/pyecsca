from configparser import ConfigParser
from io import RawIOBase, BufferedIOBase
from itertools import zip_longest
from os.path import exists, isfile, join, basename, dirname
from pathlib import Path
from typing import Union, BinaryIO

import numpy as np
from public import public

from .base import TraceSet
from ..trace import Trace


@public
class ChipWhispererTraceSet(TraceSet):
    """ChipWhisperer trace set (native) format."""

    @classmethod
    def read(cls,
             input: Union[str, Path, bytes, BinaryIO]) -> "ChipWhispererTraceSet":
        if isinstance(input, (str, Path)):
            traces, kwargs = ChipWhispererTraceSet.__read(input)
            return ChipWhispererTraceSet(*traces, **kwargs)
        else:
            raise ValueError

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, BinaryIO]) -> "ChipWhispererTraceSet":
        raise NotImplementedError

    def write(self, output: Union[str, Path, BinaryIO]):
        raise NotImplementedError

    @classmethod
    def __read(cls, full_path):
        file_name = basename(full_path)
        if not file_name.startswith("config_") or not file_name.endswith(".cfg"):
            raise ValueError
        path = dirname(full_path)
        name = file_name[7:-4]
        data = ChipWhispererTraceSet.__read_data(path, name)
        traces = []
        for samples, key, textin, textout in zip_longest(data["traces"], data["keylist"],
                                                         data["textin"], data["textout"]):
            traces.append(
                    Trace(samples, {"key": key, "textin": textin, "textout": textout}))
        del data["traces"]
        del data["keylist"]
        del data["textin"]
        del data["textout"]
        config = ChipWhispererTraceSet.__read_config(path, name)
        return traces, {**data, **config}

    @classmethod
    def __read_data(cls, path, name):
        types = {"keylist": None, "knownkey": None, "textin": None, "textout": None, "traces": None}
        for type in types.keys():
            type_path = join(path, name + type + ".npy")
            if exists(type_path) and isfile(type_path):
                types[type] = np.load(type_path, allow_pickle=True)
        return types

    @classmethod
    def __read_config(cls, path, name):
        config_path = join(path, "config_" + name + ".cfg")
        if exists(config_path) and isfile(config_path):
            config = ConfigParser()
            config.read(config_path)
            return config["Trace Config"]
        else:
            return {}

    def __repr__(self):
        return "ChipWhispererTraceSet()"
