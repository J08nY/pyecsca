import numpy as np
from .base import TraceSet
from os.path import exists, isfile, join
from configparser import ConfigParser
from public import public

from ..trace import Trace


@public
class ChipWhispererTraceSet(TraceSet):
    """ChipWhisperer trace set (native) format."""

    def __init__(self, path: str = None, name: str = None):
        if path is None and name is None:
            super().__init__()
        else:
            data = self._read_data(path, name)
            trace_data = data["traces"]
            traces = [Trace(None, None, trace_samples, trace_set=self) for trace_samples in trace_data]
            del data["traces"]
            config = self._read_config(path, name)
            super().__init__(*traces, **data, **config)

    def _read_data(self, path, name):
        types = {"keylist": None, "knownkey": None, "textin": None, "textout": None, "traces": None}
        for type in types.keys():
            type_path = join(path, name + "_" + type + ".npy")
            if exists(type_path) and isfile(type_path):
                types[type] = np.load(type_path)
        return types

    def _read_config(self, path, name):
        config_path = join(path, "config_" + name + "_.cfg")
        if exists(config_path) and isfile(config_path):
            config = ConfigParser()
            config.read(config_path)
            return config["Trace Config"]
        else:
            return {}

    def __repr__(self):
        return "ChipWhispererTraceSet()"
