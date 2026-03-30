from collections.abc import Iterable
import numpy as np
from dataclasses import dataclass, field


from .waves import create_square_wave


@dataclass
class Events:
    """ Stores a series of (duration, magnitude, start time) triplets that uniquely define events which can either be
        measurement or input.

        Events from a scenario file are cast into Events dataclass and vice-versa.

        Note:
            For measurements, duration field is empty array as it is uninterpretable.

        Attributes:
            magnitude (Iterable) : Defines the magnitudes of the events.
            start_time (Iterable) : Defines the start times of the events in Unix timestamps [min].
            duration (Iterable) : Defines the duration of the events [min].

    """
    magnitude: np.ndarray = field(default_factory=lambda: np.array([[]], dtype=float))
    start_time: np.ndarray = field(default_factory=lambda: np.array([[]], dtype=float))
    duration: np.ndarray = field(default_factory=lambda: np.array([[]], dtype=float))

    def __post_init__(self):

        self.magnitude = np.asarray(self.magnitude).astype(float)
        self.duration = np.asarray(self.duration).astype(float)
        self.start_time = np.asarray(self.start_time).astype(float)

        if self.duration.size:
            assert not np.any(self.duration < 0)
            assert (self.magnitude.shape[0] == self.start_time.shape[0] == self.duration.shape[0] and
            self.magnitude.shape[1] == self.start_time.shape[1] == self.duration.shape[1])
        else:
            assert (self.magnitude.shape[0] == self.start_time.shape[0] and
             self.magnitude.shape[1] == self.start_time.shape[1])
        assert not np.any(self.start_time < 0)
        assert not np.any(self.magnitude < 0)




    def as_dict(self):
        """ Function to make the translation between the JSON scenario file and class smooth.
        """
        self.magnitude = self.magnitude.tolist()
        self.start_time = self.start_time.tolist()
        self.duration = self.duration.tolist()
        return self



class Signal(Events):
    """ Extends the Events class with sampled signal.

        Sampled square wave is generated based on the events information to use directly in solving the differential
        equations.

        Attributes:
            sampled_signal (np.ndarray) : 2D numpy array, 1st dim: subjects, 2nd dim: timestep in the simulation horizon.

    """
    def __init__(
        self,
        time: np.ndarray = np.array([], dtype=float),
        magnitude: Iterable = np.array([[]], dtype=float),
        start_time: Iterable = np.array([[]], dtype=float),
        duration: Iterable = np.array([[]], dtype=float),
        sampling_time: float = 1,
    ):
        """
        Initializes an instance of InputClass.

        Parameters:
        - time: np.ndarray
            Time array for the signal.
        - magnitude: tuple
            Tuple containing magnitude information for creating the signal.
        - start_time: tuple
            Tuple containing start time information for creating the signal.
        - duration: tuple
            Tuple containing duration information for creating the signal.
        - sampling_time: float
            Sampling time for the signal.
        """
        super().__init__(magnitude, start_time, duration)
        self.time = time
        self.sampling_time = sampling_time
        self.magnitude = np.stack(self.magnitude, axis=0)
        self.start_time = np.stack(self.start_time, axis=0)
        self.duration = np.stack(self.duration, axis=0)
        # Initialize signal_openloop using the __create_signal method
        self.sampled_signal = Signal.__create_signal(time, self.start_time, self.duration, self.magnitude, sampling_time
        )

    @staticmethod
    def __create_signal(
        time: np.ndarray,
        start_times: np.ndarray,
        durations: np.ndarray,
        amounts: np.ndarray,
        sampling_time: float,
        ) -> np.ndarray:
        """
        Static method to create a signal based on provided input parameters.

        Parameters:
        - time: np.ndarray
            Time array for the signal.
        - start_times: np.ndarray
            Array of start times for each event.
        - durations: np.ndarray
            Array of durations for each event.
        - amounts: np.ndarray
            Array of amounts for each event.
        - sampling_time: float
            Sampling time for the signal.

        Returns:
        - np.ndarray
            3D array representing the generated scenario signal.
        """
        return create_square_wave(time, start_times, durations, amounts, sampling_time)