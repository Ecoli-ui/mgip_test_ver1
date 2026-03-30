
import numpy as np
from math import ceil
from numba import njit

@njit
def create_square_wave(
                        time: np.ndarray,           # Time array for the signal
                        start_times: np.ndarray,    # 3D array of start times for each event
                        durations: np.ndarray,      # 3D array of durations for each event
                        amounts: np.ndarray,        # 3D array of amounts for each event
                        sampling_time: float,       # Sampling time for the signal
                        ) -> np.ndarray:
    """
    Creates a scenario signal based on event start times, durations, and amounts.

    Parameters:
    - time: np.ndarray
        Time array for the signal.
    - start_times: np.ndarray
        3D array of start times for each event.
    - durations: np.ndarray
        3D array of durations for each event.
    - amounts: np.ndarray
        3D array of amounts for each event.
    - sampling_time: float
        Sampling time for the signal.

    Returns:
    - np.ndarray
        3D array representing the generated scenario signal.
    """

    # assert start_times.shape == amounts.shape, f"{start_times.shape}, {amounts.shape}"
    # assert np.all(start_times == np.sort(start_times, axis = -1)), f"start_times ({start_times.shape}) is not sorted in ascending order. {start_times}"

    # Initialize the signal array with zeros
    signal = np.zeros((amounts.shape[0],time.size))
    with_duration = True
    # If durations are undefined it is assumed to be a measurement
    if durations.size == 0:
        durations = np.inf*np.ones_like(start_times)
        with_duration = False

    for idx in range(amounts.shape[0]):
        for event_number in range(amounts.shape[1]):
            # Calculate start and stop indices based on start times and durations
            start = np.maximum(ceil((start_times[idx,event_number] - time[0]) / sampling_time), 0) # Ceil ensures that the input won't start before the defined timepoint due to sampling
            duration = np.round(np.maximum(durations[idx,event_number] / sampling_time, 1))  # max(,1) ensures that impulsive inputs also appear in the signal
            stop = int(min(start + duration, time.size))  # Min ensures to not index outside the array

            if with_duration:
                # Calculate magnitude of the event signal
                magnitude = np.nan_to_num(amounts[idx,event_number] / (duration * sampling_time), 0)
                # Assign the magnitude to the corresponding time indices in the signal array
                signal[idx,start:stop] = signal[idx,start:stop] + magnitude # Sum ensures that overlapping inputs dont exclude each other out
            else:
                # Calculate magnitude of the event signal
                magnitude = np.nan_to_num(amounts[idx, event_number], 0)
                # Assign the magnitude to the corresponding time indices in the signal array
                signal[idx, start:stop] = magnitude  # Holds the current value until the new one


    return signal
