# -*- coding: utf-8 -*-
"""
Created on Thu May 11 23:08:31 2023

@author: Andy
"""
from numba import njit, jit_module

jit_module(nopython = True)

def euler_single_step(f, h, initial, time, parameters, inputs):
    """
    Performs a single step of the Euler method for solving ordinary differential equations.

    Parameters:
    - f: callable
        Function representing the ODE system. Should take (state, time, parameters, inputs) as arguments.
    - h: float
        Step size for the RK4 method.
    - initial: np.ndarray
        Initial state vector of the system.
    - time: float
        Current time.
    - parameters: tuple or dict
        Parameters needed for the ODE system.
    - inputs: tuple or dict
        External inputs to the ODE system.

    Returns:
    - np.ndarray
        Updated state vector after a single Euler step.
    """
    return initial + h * f(initial, time, parameters, inputs)

def rk4_single_step(f, h, initial, time, parameters, inputs):
    """
    Performs a single step of the Runge-Kutta 4th order (RK4) method for solving ordinary differential equations.

    Parameters:
    - f: callable
        Function representing the ODE system. Should take (state, time, parameters, inputs) as arguments.
    - h: float
        Step size for the RK4 method.
    - initial: np.ndarray
        Initial state vector of the system.
    - time: float
        Current time.
    - parameters: tuple or dict
        Parameters needed for the ODE system.
    - inputs: tuple or dict
        External inputs to the ODE system.

    Returns:
    - np.ndarray
        Updated state vector after a single RK4 step.
    """
    # Calculate the four intermediate steps (k1, k2, k3, k4) using the RK4 method
    k1 = f(initial, time, parameters, inputs)
    k2 = f(initial + 0.5 * h * k1, time + 0.5 * h, parameters, inputs)
    k3 = f(initial + 0.5 * h * k2, time + 0.5 * h, parameters, inputs)
    k4 = f(initial + h * k3, time, parameters, inputs)

    # Update the state using the weighted average of the four steps
    return initial + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)