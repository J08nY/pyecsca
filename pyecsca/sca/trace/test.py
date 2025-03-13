"""Provides statistical tests usable on groups of traces sample-wise (Welch's and Student's t-test, ...)."""

from typing import Sequence, Tuple

import numpy as np
from public import public
from scipy.stats import ttest_ind, ks_2samp, t

from pyecsca.sca.trace.trace import Trace, CombinedTrace
from pyecsca.sca.trace.combine import average_and_variance
from pyecsca.sca.trace.edit import trim


def _ttest_func(
    first_set: Sequence[Trace], second_set: Sequence[Trace], equal_var: bool
) -> CombinedTrace:
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        raise ValueError("Nothing to compute")
    first_stack = np.stack([first.samples for first in first_set])
    second_stack = np.stack([second.samples for second in second_set])
    result = ttest_ind(first_stack, second_stack, axis=0, equal_var=equal_var)
    return CombinedTrace(result[0])


@public
def welch_ttest(
    first_set: Sequence[Trace],
    second_set: Sequence[Trace],
    dof: bool = False,
    p_value: bool = False,
) -> Tuple[CombinedTrace, ...]:
    """
    Perform the Welch's t-test sample wise on two sets of traces :paramref:`~.welch_ttest.first_set` and :paramref:`~.welch_ttest.second_set`.

    Useful for Test Vector Leakage Analysis (TVLA).

    :param first_set:
    :param second_set:
    :param dof: Whether to compute and return the degrees-of-freedom.
    :param p_value: Whether to compute and return the p-values.
    :return: Welch's t-values (samplewise) (+ degrees-of-freedom, + p-values)
    """
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        raise ValueError("Nothing to compute")
    dof |= p_value
    n0 = len(first_set)
    n1 = len(second_set)
    mean_0, var_0 = average_and_variance(*first_set)  # type: ignore
    mean_1, var_1 = average_and_variance(*second_set)  # type: ignore
    if len(mean_0) < len(mean_1):
        mean_1 = trim(mean_1, end=len(mean_0))  # type: ignore
        var_1 = trim(var_1, end=len(mean_0))  # type: ignore
    if len(mean_1) < len(mean_0):
        mean_0 = trim(mean_0, end=len(mean_1))  # type: ignore
        var_0 = trim(var_0, end=len(mean_1))  # type: ignore
    varn_0 = var_0.samples / n0
    varn_1 = var_1.samples / n1
    tval = (mean_0.samples - mean_1.samples) / np.sqrt(varn_0 + varn_1)
    result = [CombinedTrace(tval)]
    if dof or p_value:
        top = (varn_0 + varn_1) ** 2
        bot = (varn_0**2 / (n0 - 1)) + (varn_1**2 / (n1 - 1))
        df = top / bot
        del top
        del bot
        result.append(CombinedTrace(df))
    if p_value:
        atval = np.abs(tval)
        p = 2 * t.sf(atval, df)
        del atval
        result.append(CombinedTrace(p))
    return tuple(result)


@public
def student_ttest(
    first_set: Sequence[Trace], second_set: Sequence[Trace]
) -> CombinedTrace:
    """
    Perform the Students's t-test sample wise on two sets of traces :paramref:`~.student_ttest.first_set` and :paramref:`~.student_ttest.second_set`.

    Useful for Test Vector Leakage Analysis (TVLA).

    :param first_set:
    :param second_set:
    :return: Student's t-values (samplewise)
    """
    return _ttest_func(first_set, second_set, True)


@public
def ks_test(first_set: Sequence[Trace], second_set: Sequence[Trace]) -> CombinedTrace:
    """
    Perform the Kolmogorov-Smirnov two sample test on equality of distributions sample wise on two sets of traces :paramref:`~.ks_test.first_set` and :paramref:`~.ks_test.second_set`.

    :param first_set:
    :param second_set:
    :return: Kolmogorov-Smirnov test statistic values (samplewise)
    """
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        raise ValueError("Nothing to compute")
    first_stack = np.stack([first.samples for first in first_set])
    second_stack = np.stack([second.samples for second in second_set])
    results = np.empty(len(first_set[0].samples), dtype=first_set[0].samples.dtype)
    for i in range(len(first_set[0].samples)):
        results[i] = ks_2samp(first_stack[..., i], second_stack[..., i])[0]
    return CombinedTrace(results)
