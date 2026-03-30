from abc import ABC, abstractmethod
from ..ODESolvers.ode_solvers import euler_single_step, rk4_single_step
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.VirtualPatient.Models.Model import BaseModel

class BaseSolver(ABC):


    def __init__(self, scenario_instance: scenario, model: BaseModel):

        # Directory where the results should be stored
        self.scenario_instance = scenario_instance

        self.model = model

        # ODE solver function
        self.set_solver(self.scenario_instance.settings.solver_name)

    def set_solver(self, solver_name):
        match solver_name:
            case "RK4":
                self.ode_solver = rk4_single_step
            case 'Euler':
                self.ode_solver = euler_single_step

    @abstractmethod
    def do_simulation(self):
        pass
