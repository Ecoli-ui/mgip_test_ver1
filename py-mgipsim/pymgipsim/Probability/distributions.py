import numpy as np
from scipy.stats import uniform, truncnorm


def uniform_pdf(x, lower, upper):
    """
    Calculate the probability density function (PDF) of a uniform distribution.

    Parameters:
    - x: Values at which to evaluate the PDF.
    - lower: Lower bound of the uniform distribution.
    - upper: Upper bound of the uniform distribution.

    Returns:
    - pdf_values: PDF values for the given 'x' within the specified bounds.
    """
    if type(x) is not np.ndarray:
        x = np.array(x)

    """ Check Inputs """
    assert ~np.isnan(x).any(), 'x cannot have Nan'
    assert upper >= lower, f'Upper limit ({lower}) must be >= lower limit ({upper})'
    assert lower in x or upper in x, f"Lower limit ({lower} or upper limit ({upper}) must in x range ({x})"

    if upper == lower:

        idx = np.argwhere(x == lower).flatten()[0]

        pdf = np.zeros_like(x)
        pdf[idx] = 1.0

    else:
        pdf = uniform.pdf(x, loc=lower, scale=upper - lower)

    return pdf

def normal_pdf(x, mean, std):
    """
    Calculate the probability density function (PDF) of a normal distribution.

    Parameters:
    - x: Values at which to evaluate the PDF.
    - mean: Mean (average) of the normal distribution.
    - std: Standard deviation of the normal distribution.

    Returns:
    - pdf_values: PDF values for the given 'x'.
    """
    x = np.array(x)

    assert ~np.isnan(x).any(), 'X cannot have NaN'

    assert ~np.isnan(mean), 'mean cannot have NaN'

    assert ~np.isnan(std), 'std cannot have NaN'
    assert std >= 0

    return uniform.pdf(x, loc=mean, scale=std)

def truncated_normal_pdf(x, mean, std, lower, upper):
    """
    Calculate the probability density function (PDF) of a truncated normal distribution.

    Parameters:
    - x: Values at which to evaluate the PDF.
    - mean: Mean (average) of the normal distribution.
    - std: Standard deviation of the normal distribution.
    - lower: Lower truncation point of the distribution.
    - upper: Upper truncation point of the distribution.

    Returns:
    - pdf_values: PDF values for the given 'x' within the specified truncation range.
    """

    x = np.array(x)

    assert ~np.isnan(x).any()

    assert upper >= lower, f'Upper limit ({lower}) must be >= lower limit ({upper})'

    assert ~np.isnan(mean), 'mean cannot have NaN'

    assert ~np.isnan(std), 'std cannot have NaN'
    assert std >= 0

    a = (lower - mean) / std
    b = (upper + mean) / std
    pdf_values = truncnorm.pdf(x, a, b, loc=mean, scale=std)

    return pdf_values



