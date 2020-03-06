from copy import copy
from io import RawIOBase, BufferedIOBase, IOBase
from pathlib import Path
from typing import Union, Optional
import numpy as np
import h5py
from public import public

from .base import TraceSet
from .. import Trace


@public
class HDF5TraceSet(TraceSet):
    _file: Optional[h5py.File]

    @classmethod
    def read(cls, input: Union[str, Path, bytes, RawIOBase, BufferedIOBase]) -> "HDF5TraceSet":
        if isinstance(input, (str, Path)):
            hdf5 = h5py.File(str(input), mode="r")
        elif isinstance(input, IOBase):
            hdf5 = h5py.File(input, mode="r")
        else:
            raise ValueError
        kwargs = dict(hdf5.attrs)
        traces = []
        for k, v in hdf5.items():
            meta = dict(hdf5[k].attrs) if hdf5[k].attrs else None
            samples = hdf5[k]
            traces.append(Trace(np.array(samples, dtype=samples.dtype), None, None, meta))
        hdf5.close()
        return HDF5TraceSet(*traces, **kwargs)

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, RawIOBase, BufferedIOBase]) -> "HDF5TraceSet":
        if isinstance(input, (str, Path)):
            hdf5 = h5py.File(str(input), mode="a")
        elif isinstance(input, IOBase):
            hdf5 = h5py.File(input, mode="a")
        else:
            raise ValueError
        kwargs = dict(hdf5.attrs)
        traces = []
        for k, v in hdf5.items():
            meta = dict(hdf5[k].attrs) if hdf5[k].attrs else None
            samples = hdf5[k]
            traces.append(Trace(samples, k, None, meta))
        return HDF5TraceSet(*traces, **kwargs, _file=hdf5)

    def __setitem__(self, key, value):
        if not isinstance(value, Trace):
            raise TypeError
        if self._file is not None:
            if str(key) in self._file:
                del self._file[str(key)]
            self._file[str(key)] = value.samples
            value.samples = self._file[str(key)]
            if value.meta:
                for k, v in value.meta.items():
                    self._file[str(key)].attrs[k] = v
        super().__setitem__(key, value)

    def append(self, value: Trace):
        if self._file is not None:
            key = sorted(list(map(int, self._file.keys())))[-1] + 1 if self._file.keys() else 0
            self._file[str(key)] = value.samples
            value.samples = self._file[str(key)]
            if value.meta:
                for k, v in value.meta.items():
                    self._file[str(key)].attrs[k] = v
        self._traces.append(value)

    def save(self):
        if self._file is not None:
            self._file.flush()

    def close(self):
        if self._file is not None:
            self._file.close()

    def write(self, output: Union[str, Path, RawIOBase, BufferedIOBase]):
        if isinstance(output, (str, Path)):
            hdf5 = h5py.File(str(output), "w")
        elif isinstance(output, IOBase):
            hdf5 = h5py.File(output, "w")
        else:
            raise ValueError
        for k in self._keys:
            hdf5[k] = getattr(self, k)
        for i, trace in enumerate(self._traces):
            dset = hdf5.create_dataset(str(i), trace.samples)
            if trace.meta:
                for k, v in trace.meta.items():
                    dset.attrs[k] = v
        hdf5.close()
