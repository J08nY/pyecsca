from typing import Sequence, Optional

import numpy as np
from public import public
from scipy.stats import ttest_ind, ks_2samp

from .trace import Trace, CombinedTrace


def ttest_func(first_set: Sequence[Trace], second_set: Sequence[Trace],
               equal_var: bool) -> Optional[CombinedTrace]:
    if not first_set or not second_set or len(first_set) == 0 or len(second_set) == 0:
        return None
    first_stack = np.stack([first.samples for first in first_set])
    second_stack = np.stack([second.samples for second in second_set])
    result = ttest_ind(first_stack, second_stack, axis=0, equal_var=equal_var)
    return CombinedTrace(None, None, result[0], parents=[*first_set, *second_set])


@public
def welch_ttest(first_set: Sequence[Trace], second_set: Sequence[Trace]) -> Optional[CombinedTrace]:
    """
    Perform the Welch's t-test sample wise on two sets of traces `first_set` and `second_set`.
    Useful for Test Vector Leakage Analysis (TVLA).

    :param first_set:
    :param second_set:
    :return: Welch's t-values (samplewise)
    """
    return ttest_func(first_set, second_set, False)


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
    return CombinedTrace(None, None, results, parents=[*first_set, *second_set])
