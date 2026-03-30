from .distributions import *

def generate_random_percentages(number_of_days, number_of_subjects, number_of_meals, lower_limit = 0.2, upper_limit = 0.6):
    """
    Generates random percentage values for a given number of subjects, meals, and days.

    Parameters:
    - number_of_days (int): The number of days.
    - lower_limit (float): The lower limit for random percentage generation.
    - upper_limit (float): The upper limit for random percentage generation.
    - number_of_subjects (int): The number of subjects.
    - number_of_meals (int): The number of meals.

    Returns:
    - percentages (numpy.ndarray): A 3D array of random percentages with dimensions
    (number_of_subjects, number_of_days, number_of_meals) where the sum along the second axis is 1.
    """

    """ Input Assertions """
    for var_name, var in zip(
                            ['number_of_days', 'number_of_subjects', 'number_of_meals'],
                            [number_of_days, number_of_subjects, number_of_meals]
                            ):
        assert var >= 0, f'{var_name} must be >=0 not {var}'
        assert ~np.isnan(var), f'{var_name} must not be nan'

        var = int(var)

    for var_name, var in zip(
                            ['lower_limit', 'upper_limit'],
                            [lower_limit, upper_limit]
                            ):
        assert var >= 0, f'{var_name} must be >=0 not {var}'
        assert var <= 1, f'{var_name} must be <=1 not {var}'
        assert ~np.isnan(var), f'{var_name} must not be nan'

        var = float(var)

    """ Calculations """

    # Generate random arrays between lower_limit and upper_limit for each subject and day
    rand_arrays = np.random.uniform(lower_limit, upper_limit, (number_of_subjects, number_of_days, number_of_meals))

    # Ensure that the sum of each set of random arrays is equal to 1
    rand_sums = np.sum(rand_arrays, axis=-1, keepdims=True)

    # Normalize the values by the sum to convert all to fractions
    rand_arrays /= rand_sums


    """ Output Assertions """
    assert np.all(rand_arrays <= 1), f"All values must be decimals"
    # assert np.all(rand_arrays.sum(axis = -1).round(2) == 1.0), f"Values must sum to 1 not ({rand_arrays.sum(axis = -1).round(2)})"

    # Return the reshaped percentages array
    return rand_arrays


def generate_normalized_pdfs(distribution_name, **pdf_parameters):
    """
    Generate and normalize probability density functions (PDFs) for a given distribution.

    Parameters:
    - distribution_name: str
        Name of the probability distribution.
    - *pdf_parameters: variable arguments
        Parameters needed for the specified distribution.

    Returns:
    - normalized_pdf: np.ndarray
        Normalized PDF values for the specified distribution.
    """

    match distribution_name:
        case 'norm':
            pdf = normal_pdf(**pdf_parameters)

        case 'trunc_norm':
            pdf = truncated_normal_pdf(**pdf_parameters)

        case 'uniform':
            pdf = uniform_pdf(**pdf_parameters)

    if sum(pdf) == 0:
        normalized_pdf = pdf
    else:
        normalized_pdf = pdf / sum(pdf)

    assert normalized_pdf.sum().round(2) == 1 or normalized_pdf.sum().round(2) == 0, f"PDF probabilities must sum to 1 or 0 not {normalized_pdf.sum().round(2)}"

    return normalized_pdf


def sample_pdfs(normalized_pdf, sample_range, sample_size, rng_generator):
    """
    Sample values from a given normalized probability density function (PDF).

    Parameters:
    - normalized_pdf: np.ndarray
        Normalized PDF values.
    - sample_range: np.ndarray
        Range of values to sample from.
    - sample_size: int
        Number of samples to generate.
    - rng_generator

    Returns:
    - samples: np.ndarray
        Sampled values based on the given PDF.
    """

    assert normalized_pdf.sum().round(2) == 1 or normalized_pdf.sum().round(2) == 0, f"PDF probabilities must sum to 1 or 0 not {normalized_pdf.sum().round(2)}"

    if normalized_pdf.sum().round(2) == 1:
        # rng = np.random.default_rng(DEFAULT_RANDOM_SEED+i)
        # np.random.seed(DEFAULT_RANDOM_SEED)
        return rng_generator.choice(a=sample_range, size=sample_size, p=normalized_pdf)
    
    elif normalized_pdf.sum().round(2) == 0 and all(normalized_pdf >= 0):
        return np.zeros_like(sample_size)

    else:
        raise ValueError('Invalid PDF')



def sample_generator(value_limits, distribution, sample_size, rng_generator):

    if not type(value_limits) == list:
        value_limits = [value_limits]

    if len(value_limits) == 1:
        value_range = np.arange(value_limits[0], value_limits[0] + 1, 1)

        assert value_range[0] == value_limits[0]

        pdf = generate_normalized_pdfs(
                                        distribution_name=distribution,
                                        x = value_range,
                                        lower = value_limits[0],
                                        upper = value_limits[0]
                                        )


    elif len(value_limits) == 2:
        value_range = np.linspace(value_limits[0], value_limits[1], 100)

        assert value_range[0] == value_limits[0] and value_range[-1] == value_limits[-1]

        pdf = generate_normalized_pdfs(
                                        distribution_name=distribution,
                                        x = value_range,
                                        lower = value_limits[0],
                                        upper = value_limits[1]
                                        )

    else:
        raise ValueError(f'The length of value_limits should be 1 or 2 not {len(value_limits)}')

    samples = sample_pdfs(normalized_pdf=pdf, sample_range=value_range, sample_size=sample_size, rng_generator=rng_generator)

    assert samples.ndim == len(sample_size)

    return value_range, pdf, samples


def generate_random_percentages(number_of_days, number_of_subjects, number_of_meals, lower_limit = 0.2, upper_limit = 0.6):
    """
    Generates random percentage values for a given number of subjects, meals, and days.

    Parameters:
    - number_of_days (int): The number of days.
    - lower_limit (float): The lower limit for random percentage generation.
    - upper_limit (float): The upper limit for random percentage generation.
    - number_of_subjects (int): The number of subjects.
    - number_of_meals (int): The number of meals.

    Returns:
    - percentages (numpy.ndarray): A 3D array of random percentages with dimensions
    (number_of_subjects, number_of_days, number_of_meals) where the sum along the second axis is 1.
    """

    # Generate random arrays between lower_limit and upper_limit for each subject and day
    rand_arrays = np.random.uniform(lower_limit, upper_limit, (number_of_subjects, number_of_days, number_of_meals))

    # Ensure that the sum of each set of random arrays is equal to 1
    rand_sums = np.sum(rand_arrays, axis=-1, keepdims=True)

    # Normalize the values by the sum to convert all to fractions
    rand_arrays /= rand_sums

    # Return the reshaped percentages array
    return rand_arrays