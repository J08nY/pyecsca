import numpy as np
import numpy.typing as npt
from numba import cuda
from math import sqrt


@cuda.jit(device=True, cache=True)
def gpu_pearson_corr(samples: npt.NDArray[np.number],
                     intermediate_values: npt.NDArray[np.number],
                     result: cuda.devicearray.DeviceNDArray):
    """
    Calculates the Pearson correlation coefficient between the given samples and intermediate values using GPU acceleration.

    :param samples: A 2D array of shape (n, m) containing the samples.
    :type samples: npt.NDArray[np.number]
    :param intermediate_values: A 1D array of shape (n,) containing the intermediate values.
    :type intermediate_values: npt.NDArray[np.number]
    :param result: A 1D array of shape (m,) to store the resulting correlation coefficients.
    :type result: cuda.devicearray.DeviceNDArray
    """
    col: int = cuda.grid(1)  # type: ignore

    if col >= samples.shape[1]:  # type: ignore
        return

    n = samples.shape[0]
    samples_sum = 0.
    samples_sq_sum = 0.
    intermed_sum = 0.
    intermed_sq_sum = 0.
    product_sum = 0.

    for row in range(n):
        samples_sum += samples[row, col]
        samples_sq_sum += samples[row, col] ** 2
        intermed_sum += intermediate_values[row]
        intermed_sq_sum += intermediate_values[row] ** 2
        product_sum += samples[row, col] * intermediate_values[row]

    numerator = n * product_sum - samples_sum * intermed_sum
    denominator = (sqrt(n * samples_sq_sum - samples_sum * samples_sum)
                   * sqrt(n * intermed_sq_sum - intermed_sum * intermed_sum))

    result[col] = numerator / denominator
