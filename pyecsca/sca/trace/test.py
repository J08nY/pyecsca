from typing import Sequence, Optional, Tuple

import numpy as np
from public import public
from scipy.stats import ttest_ind, ks_2samp, t

from .trace import Trace, CombinedTrace
from .combine import average_and_variance
from .edit import trim


def ttest_func(first_set: Sequence[Trace], second_set: Sequence[Trace],
               equal_var: bool) -> Optional[CombinedTrace]:
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        return None
    first_stack = np.stack([first.samples for first in first_set])
    second_stack = np.stack([second.samples for second in second_set])
    result = ttest_ind(first_stack, second_stack, axis=0, equal_var=equal_var)
    return CombinedTrace(result[0])


@public
def welch_ttest(first_set: Sequence[Trace], second_set: Sequence[Trace], dof: bool = False, p_value: bool = False) -> Optional[Tuple[CombinedTrace, ...]]:
    """
    Perform the Welch's t-test sample wise on two sets of traces `first_set` and `second_set`.
    Useful for Test Vector Leakage Analysis (TVLA).

    :param first_set:
    :param second_set:
    :param dof: Whether to compute and return the degrees-of-freedom.
    :param p_value: Whether to compute and return the p-values.
    :return: Welch's t-values (samplewise) (+ degrees-of-freedom, + p-values)
    """
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        return None
    n0 = len(first_set)
    n1 = len(second_set)
    mean_0, var_0 = average_and_variance(*first_set)
    mean_1, var_1 = average_and_variance(*second_set)
    if len(mean_0) < len(mean_1):
        mean_1 = trim(mean_1, end=len(mean_0))
        var_1 = trim(var_1, end=len(mean_0))
    if len(mean_1) < len(mean_0):
        mean_0 = trim(mean_0, end=len(mean_1))
        var_0 = trim(var_0, end=len(mean_1))
    varn_0 = var_0.samples / n0
    varn_1 = var_1.samples / n1
    tval = (mean_0.samples - mean_1.samples) / np.sqrt(varn_0 + varn_1)
    result = [CombinedTrace(tval)]
    if dof or p_value:
        top = (varn_0 + varn_1)**2
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
def student_ttest(first_set: Sequence[Trace], second_set: Sequence[Trace]) -> Optional[
        CombinedTrace]:
    """
    Perform the Students's t-test sample wise on two sets of traces `first_set` and `second_set`.
    Useful for Test Vector Leakage Analysis (TVLA).

    :param first_set:
    :param second_set:
    :return: Student's t-values (samplewise)
    """
    return ttest_func(first_set, second_set, True)


@public
def ks_test(first_set: Sequence[Trace], second_set: Sequence[Trace]) -> Optional[CombinedTrace]:
    """
    Perform the Kolmogorov-Smirnov two sample test on equality of distributions sample wise on
    two sets of traces `first_set` and `second_set`.

    :param first_set:
    :param second_set:
    :return: Kolmogorov-Smirnov test statistic values (samplewise)
    """
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        return None
    first_stack = np.stack([first.samples for first in first_set])
    second_stack = np.stack([second.samples for second in second_set])
    results = np.empty(len(first_set[0].samples), dtype=first_set[0].samples.dtype)
    for i in range(len(first_set[0].samples)):
        results[i] = ks_2samp(first_stack[..., i], second_stack[..., i])[0]
    return CombinedTrace(results)
