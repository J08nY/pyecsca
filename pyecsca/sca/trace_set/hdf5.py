"""
Provides a traceset implemented on top of the Hierarchical Data Format (HDF5).

This traceset can be loaded "inplace" which means that it is not fully loaded into memory, and only parts of traces that
are operated on are in memory. This is very useful for working with huge sets of traces that do not fit in memory.
"""
import pickle
import uuid
from collections.abc import MutableMapping
from io import RawIOBase, BufferedIOBase
from pathlib import Path
from typing import Union, Optional, List, BinaryIO

import h5py
import numpy as np
from public import public
from copy import deepcopy

from pyecsca.sca.trace_set.base import TraceSet
from pyecsca.sca import Trace


@public
class HDF5Meta(MutableMapping):
    """Metadata mapping that is HDF5-compatible (items are picklable)."""

    _dataset: h5py.AttributeManager

    def __init__(self, attrs: h5py.AttributeManager):
        self._attrs = attrs
        super().__init__()

    def __getitem__(self, item):
        if item not in self._attrs:
            raise KeyError
        return pickle.loads(self._attrs[item])  # pickle is OK here, skipcq: BAN-B301

    def __setitem__(self, key, value):
        self._attrs[key] = np.void(pickle.dumps(value))

    def __delitem__(self, key):
        del self._attrs[key]

    def __copy__(self):
        return deepcopy(self)

    def __deepcopy__(self, memodict):
        return dict(self)

    def __iter__(self):
        yield from self._attrs

    def __len__(self):
        return len(self._attrs)


@public
class HDF5TraceSet(TraceSet):
    """Traceset based on the HDF5 (Hierarchical Data Format)."""

    _file: Optional[h5py.File]
    _ordering: List[str]
    # _meta: Optional[HDF5Meta]

    def __init__(
        self,
        *traces: Trace,
        _file: Optional[h5py.File] = None,
        _ordering: Optional[List[str]] = None,
        **kwargs,
    ):
        # self._meta = HDF5Meta(_file.attrs) if _file is not None else None
        self._file = _file
        if _ordering is None:
            _ordering = [str(uuid.uuid4()) for _ in traces]
        self._ordering = _ordering
        super().__init__(*traces, **kwargs)

    @classmethod
    def read(cls, input: Union[str, Path, bytes, BinaryIO], **kwargs) -> "HDF5TraceSet":
        if isinstance(input, (str, Path)):
            hdf5 = h5py.File(str(input), mode="r")
        elif isinstance(input, (RawIOBase, BufferedIOBase, BinaryIO)):
            hdf5 = h5py.File(input, mode="r")
        else:
            raise TypeError
        if "traces" not in hdf5:
            hdf5.create_group("traces", track_order=True)
        group = hdf5["traces"]
        kws = dict(group.attrs)
        ordering = []
        traces = []
        for k, samples in group.items():
            meta = dict(HDF5Meta(samples.attrs))
            traces.append(Trace(np.array(samples, dtype=samples.dtype), meta))
            ordering.append(k)
        hdf5.close()
        return HDF5TraceSet(*traces, **kws, _ordering=ordering)

    @classmethod
    def inplace(cls, input: Union[str, Path, bytes, BinaryIO], **kwargs) -> "HDF5TraceSet":
        if isinstance(input, (str, Path)):
            hdf5 = h5py.File(str(input), mode="a")
        elif isinstance(input, (RawIOBase, BufferedIOBase, BinaryIO)):
            hdf5 = h5py.File(input, mode="a")
        else:
            raise TypeError
        if "traces" not in hdf5:
            hdf5.create_group("traces", track_order=True)
        group = hdf5["traces"]
        kws = dict(group.attrs)
        ordering = []
        traces = []
        for k, samples in group.items():
            meta = HDF5Meta(samples.attrs)
            traces.append(Trace(samples, meta))
            ordering.append(k)
        return HDF5TraceSet(*traces, **kws, _file=hdf5, _ordering=ordering)  # type: ignore[misc]

    def append(self, value: Trace) -> Trace:
        key = str(uuid.uuid4())
        if self._file is not None:
            group = self._file["traces"]
            new_samples = group.create_dataset(key, data=value.samples)
            new_meta = HDF5Meta(new_samples.attrs)
            if value.meta:
                for k, v in value.meta.items():
                    new_meta[k] = v
            value = Trace(new_samples, new_meta)

        self._ordering.append(key)
        self._traces.append(value)
        return value

    def get(self, index: int) -> Trace:
        return self[index]

    def remove(self, value: Trace):
        if value in self._traces:
            index = self._traces.index(value)
            key = self._ordering[index]
            self._ordering.remove(key)
            self._traces.remove(value)
            if self._file:
                group = self._file["traces"]
                group.pop(key)
        else:
            raise KeyError

    def save(self):
        if self._file is not None:
            self._file.flush()

    def close(self):
        if self._file is not None:
            self._file.close()

    # def __getattribute__(self, item):
    #     if super().__getattribute__("_meta") and item in super().__getattribute__("_meta"):
    #         return super().__getattribute__("_meta")[item]
    #     return super().__getattribute__(item)
    #
    # def __setattr__(self, key, value):
    #     if key in self._keys and self._meta is not None:
    #         self._meta[key] = value
    #     else:
    #         super().__setattr__(key, value)

    def write(self, output: Union[str, Path, BinaryIO]):
        if isinstance(output, (str, Path)):
            hdf5 = h5py.File(str(output), "w")
        elif isinstance(output, BinaryIO):
            hdf5 = h5py.File(output, "w")
        else:
            raise ValueError
        group = hdf5.create_group("traces", track_order=True)
        for k in self._keys:
            group.attrs[k] = getattr(self, k)
        for k, trace in zip(self._ordering, self):
            dset = group.create_dataset(k, data=trace.samples)
            if trace.meta:
                meta = HDF5Meta(dset.attrs)
                for key, val in trace.meta.items():
                    meta[key] = val
        hdf5.close()

    def __repr__(self):
        fname = ""
        status = ""
        if self._file is not None:
            if self._file.id.valid:
                status = " (opened)"
                fname = self._file.filename
            else:
                status = "(closed)"
        args = ", ".join(
            [
                f"{key}={getattr(self, key)!r}"
                for key in self._keys
                if not key.startswith("_")
            ]
        )
        return f"HDF5TraceSet('{fname}'{status}, {args} <{len(self)}>)"
