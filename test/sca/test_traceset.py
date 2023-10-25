import os.path
import shutil
import tempfile

import pytest
from importlib_resources import files, as_file

import numpy as np

import test.data.sca
from pyecsca.sca import (
    TraceSet,
    InspectorTraceSet,
    ChipWhispererTraceSet,
    PickleTraceSet,
    HDF5TraceSet,
    Trace,
    SampleCoding,
)


@pytest.fixture()
def example_traces():
    return [
        Trace(np.array([20, 40, 50, 50, 10], dtype=np.dtype("i1")), {"something": 5}),
        Trace(np.array([1, 2, 3, 4, 5], dtype=np.dtype("i1"))),
        Trace(np.array([6, 7, 8, 9, 10], dtype=np.dtype("i1"))),
    ]


@pytest.fixture()
def example_kwargs():
    return {"num_traces": 3, "thingy": "abc"}


def test_create():
    assert TraceSet() is not None
    assert InspectorTraceSet() is not None
    assert ChipWhispererTraceSet() is not None
    assert PickleTraceSet() is not None
    assert HDF5TraceSet() is not None


def test_repr(example_traces, tmp_path):
    trs = InspectorTraceSet(
        *example_traces, num_traces=len(example_traces), sample_coding=SampleCoding.Int8, num_samples=5, y_scale=1
    )
    r1 = repr(trs)
    trs.write(tmp_path / "test.trs")
    r2 = repr(InspectorTraceSet.read(tmp_path / "test.trs"))
    assert r1
    assert r2

    cw = ChipWhispererTraceSet(*example_traces)
    r1 = repr(cw)
    assert r1

    pickle = PickleTraceSet(*example_traces)
    r1 = repr(pickle)
    pickle.write(tmp_path / "test.pickle")
    r2 = repr(PickleTraceSet.read(tmp_path / "test.pickle"))
    assert r1 == r2


def test_trs_load_fname():
    with as_file(files(test.data.sca).joinpath("example.trs")) as path:
        result = InspectorTraceSet.read(path)
        assert result is not None
        assert result.global_title == "Example trace set"
        assert len(result) == 10
        assert len(list(result)) == 10
        assert "InspectorTraceSet" in str(result)
        assert result[0].trace_set is result
        assert result.sampling_frequency == 12500000


def test_trs_load_file():
    with files(test.data.sca).joinpath("example.trs").open("rb") as f:
        assert InspectorTraceSet.read(f) is not None


def test_trs_load_bytes():
    with files(test.data.sca).joinpath("example.trs").open("rb") as f:
        assert InspectorTraceSet.read(f.read()) is not None


def test_trs_save():
    with as_file(files(test.data.sca).joinpath("example.trs")) as path:
        trace_set = InspectorTraceSet.read(path)
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "out.trs")
            trace_set.write(path)
            assert os.path.exists(path)
            assert InspectorTraceSet.read(path) is not None


def test_cw_load_fname():
    with as_file(files(test.data.sca).joinpath("config_chipwhisperer_.cfg")) as path:
        # This will not work if the test package is not on the file system directly.
        result = ChipWhispererTraceSet.read(path)
        assert result is not None
        assert len(result) == 2


def test_pickle_load_fname():
    with as_file(files(test.data.sca).joinpath("test.pickle")) as path:
        result = PickleTraceSet.read(path)
        assert result is not None


def test_pickle_load_file():
    with files(test.data.sca).joinpath("test.pickle").open("rb") as f:
        assert PickleTraceSet.read(f) is not None


def test_pickle_save(example_traces, example_kwargs):
    trace_set = PickleTraceSet(*example_traces, **example_kwargs)
    with tempfile.TemporaryDirectory() as dirname:
        path = os.path.join(dirname, "out.pickle")
        trace_set.write(path)
        assert os.path.exists(path)
        assert PickleTraceSet.read(path) is not None


def test_h5_load_fname():
    with as_file(files(test.data.sca).joinpath("test.h5")) as path:
        result = HDF5TraceSet.read(path)
        assert result is not None


def test_h5_load_file():
    with files(test.data.sca).joinpath("test.h5").open("rb") as f:
        assert HDF5TraceSet.read(f) is not None


def test_h5_inplace():
    with tempfile.TemporaryDirectory() as dirname, as_file(
        files(test.data.sca).joinpath("test.h5")
    ) as orig_path:
        path = os.path.join(dirname, "test.h5")
        shutil.copy(orig_path, path)
        trace_set = HDF5TraceSet.inplace(path)
        assert trace_set is not None
        test_trace = Trace(
            np.array([4, 7], dtype=np.dtype("i1")), meta={"thing": "ring"}
        )
        other_trace = Trace(np.array([8, 7], dtype=np.dtype("i1")), meta={"a": "b"})
        trace_set.append(test_trace)
        assert len(trace_set) == 3
        trace_set.append(other_trace)
        trace_set.remove(other_trace)
        assert len(trace_set) == 3
        trace_set.save()
        trace_set.close()
        test_set = HDF5TraceSet.read(path)
        assert test_set.get(2) == test_set[2]
        assert np.array_equal(test_set[2].samples, test_trace.samples)
        assert test_set[2].meta["thing"] == test_trace.meta["thing"]
        assert test_set[2] == test_trace


def test_h5_save(example_traces, example_kwargs):
    trace_set = HDF5TraceSet(*example_traces, **example_kwargs)
    with tempfile.TemporaryDirectory() as dirname:
        path = os.path.join(dirname, "out.h5")
        trace_set.write(path)
        assert os.path.exists(path)
        assert HDF5TraceSet.read(path) is not None
