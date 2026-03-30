import numpy
import numpy as np
from collections import deque


class Hovorka_Parameters:
    ka1 = 0.006
    ka2 = 0.06
    ka3 = 0.03
    vI = 0.12
    vG = 0.16

    def __init__(self, TmaxI=55, SIT=51.2e-4, SID=8.2e-4, SIE=520e-4, Ke=0.138, K12=0.066, Ag=0.8, TmaxG=40, gain=1, TmaxE=5, EGP0=0.0161, F01=0.0097, BW=80):
        self.TmaxI = TmaxI
        self.SIT = SIT
        self.SID = SID
        self.SIE = SIE
        self.Ke = Ke
        self.K12 = K12
        self.Ag = Ag
        self.TmaxG = TmaxG
        self.gain = gain
        self.TmaxE = TmaxE
        self.EGP0 = EGP0
        self.F01 = F01
        self.BW = BW

    def get_VI(self):
        return Hovorka_Parameters.vI * self.BW

    def get_VG(self):
        return Hovorka_Parameters.vG * self.BW

    def get_kb1(self):
        return Hovorka_Parameters.ka1 * self.SIT

    def get_kb2(self):
        return Hovorka_Parameters.ka2 * self.SID

    def get_kb3(self):
        return Hovorka_Parameters.ka3 * self.SIE

    def get_parameters_dictionary(self):
        return {
            "TmaxI": self.TmaxI,
            "SIT": self.SIT,
            "SID": self.SID,
            "SIE": self.SIE,
            "Ke": self.Ke,
            "K12": self.K12,
            "Ag": self.Ag,
            "TmaxG": self.TmaxG,
            "gain": self.gain,
            "TmaxE": self.TmaxE,
            "EGP0": self.EGP0,
            "F01": self.F01,
            "BW": self.BW
        }

    def update_by_dictionary(self, dictionary):
        self.TmaxI = dictionary["TmaxI"]
        self.SIT = dictionary["SIT"]
        self.SID = dictionary["SID"]
        self.SIE = dictionary["SIE"]
        self.Ke = dictionary["Ke"]
        self.K12 = dictionary["K12"]
        self.Ag = dictionary["Ag"]
        self.TmaxG = dictionary["TmaxG"]
        self.gain = dictionary["gain"]
        self.TmaxE = dictionary["TmaxE"]
        self.EGP0 = dictionary["EGP0"]
        self.F01 = dictionary["F01"]
        self.BW = dictionary["BW"]


class Data_PW:
    # basal_pw unit is U/hr
    # bolus_pw unit is U or U/(sample time)
    # fast_carb_pw unit is gr or gr/(sample time)
    # energy_expenditure_pw unit is MET value
    # hypo_prob_pw and hyper_prob_pw are probability between 0 and 1
    # cgm_pw unit is mg/dl
    # gut_absorption_rate_pw unit is mmol/min
    # T is the sample time, e.g. when T=5 it means the data are stored every 5 min
    pw = 36

    def __init__(self, basal_pw=deque([0] * pw, maxlen=pw), bolus_pw=deque([0] * pw, maxlen=pw),
                 fast_carb_pw=deque([], maxlen=pw), energy_expenditure_pw=deque([1] * pw, maxlen=pw),
                 hypo_prob_pw=deque([], maxlen=pw), hyper_prob_pw=deque([], maxlen=pw),
                 cgm_pw=deque([100] * pw, maxlen=pw), gut_absorption_rate_pw=deque([], maxlen=pw),
                 meal_pw=deque([0] * pw, maxlen=pw), T=5):

        self.basal_pw = basal_pw
        self.bolus_pw = bolus_pw
        self.fast_carb_pw = fast_carb_pw
        self.energy_expenditure_pw = energy_expenditure_pw
        self.hypo_prob_pw = hypo_prob_pw
        self.hyper_prob_pw = hyper_prob_pw
        self.cgm_pw = cgm_pw
        self.gut_absorption_rate_pw = gut_absorption_rate_pw
        self.meal_pw = meal_pw
        self.T = T
        self.push_num = 0

    def push_cgm(self, cgm_val):
        self.cgm_pw.append(cgm_val)
        self.push_num += 1

    def get_last_cgm(self):
        return self.cgm_pw[-1]

    def get_dcgm_dt(self):
        # correct dcgm_dt calculation
        # dcgm_dt = (3.0 * self.cgm_pw[-1] - 4.0 * self.cgm_pw[-2] + self.cgm_pw[-3]) / (2.0 * self.T)

        # previous dcgm_dt calculation
        dcgm_dt = (3.0 * self.cgm_pw[-1] - 4.0 * self.cgm_pw[-2] + self.cgm_pw[-3]) / 2.0

        return dcgm_dt

    def get_d2cgm_dt2(self):
        # correct d2cgm_dt2 calculation
        # d2cgm_dt2 = (self.cgm_pw[-1] - 2.0 * self.cgm_pw[-2] + self.cgm_pw[-3]) / (self.T ** 2)

        # previous d2cgm_dt2 calculation
        d2cgm_dt2 = (self.cgm_pw[-1] - 2.0 * self.cgm_pw[-2] + self.cgm_pw[-3])

        return d2cgm_dt2

    def get_cgm_min(self, k):
        # this function returns the min cgm of the last k sample time
        cgm_pw = np.array(self.cgm_pw)
        if len(cgm_pw) >= k:
            cgm_min = np.min(cgm_pw[-k:])
        else:
            cgm_min = np.min(cgm_pw)

        return cgm_min

    def get_cgm_max(self, k):
        # this function returns the max cgm of the last k sample time
        cgm_pw = np.array(self.cgm_pw)
        if len(cgm_pw) >= k:
            cgm_max = np.min(cgm_pw[-k:])
        else:
            cgm_max = np.min(cgm_pw)

        return cgm_max

    # this function returns the cgm_pw as a numpy array
    def get_cgm_pw(self):
        return np.array(self.cgm_pw)

    def get_basal_pw_mU_min(self):
        return np.array(self.basal_pw) * 1000 / 60

    def push_basal(self, basal_val):
        self.basal_pw.append(basal_val)

    def get_last_basal(self):
        return self.basal_pw[-1]

    def get_last_basal_mU_min(self):
        return self.basal_pw[-1] * 1000 / 60

    def push_bolus(self, bolus_val):
        self.bolus_pw.append(bolus_val)

    def get_last_bolus(self):
        return self.bolus_pw[-1]

    def get_last_bolus_mU_min(self):
        return self.bolus_pw[-1] * 1000 / self.T

    def get_last_insulin_input_mU_min(self):
        return self.get_last_basal_mU_min() + self.get_last_bolus_mU_min()

    def push_fast_carb(self, fast_carb_val):
        self.fast_carb_pw.append(fast_carb_val)

    def get_last_fast_carb(self):
        return self.fast_carb_pw[-1]

    def push_energy_expenditure(self, energy_expenditure_val):
        self.energy_expenditure_pw.append(energy_expenditure_val)

    def get_last_energy_expenditure(self):
        return self.energy_expenditure_pw[-1]

    def push_hypo_prob(self, hypo_prob_val):
        self.hypo_prob_pw.append(hypo_prob_val)

    def get_last_hypo_prob(self):
        return self.hypo_prob_pw[-1]

    def push_hyper_prob(self, hyper_prob_val):
        self.hyper_prob_pw.append(hyper_prob_val)

    def get_last_hyper_prob(self):
        return self.hyper_prob_pw[-1]

    def push_gut_absorption_rate(self, gut_absorption_rate_val):
        self.gut_absorption_rate_pw.append(gut_absorption_rate_val)

    def get_last_gut_absorption_rate(self):
        return self.gut_absorption_rate_pw[-1]

    def push_meal(self, meal_val):
        self.meal_pw.append(meal_val)

    def get_last_meal(self):
        return self.meal_pw[-1]


class Demographic_Information:
    # the default values for the waist_size and height are in centimeter
    # the default value for BW is in kg
    # gender can either take 1 or 0 which corresponds to male and female respectively
    # insulin2carb_ratio unit is gr/U
    # basal_rate unit is U/hr

    def __init__(self, gender=1, age=30, waist_size=90, BW=80, height=180, HbA1c=6.5, insulin2carb_ratio=10,
                 basal_rate=1, correction_factor=40):
        self.gender = gender
        self.age = age
        self.waist_size = waist_size
        self.BW = BW
        self.height = height
        self.HbA1c = HbA1c
        self.insulin2carb_ratio = insulin2carb_ratio
        self.basal_rate = basal_rate
        self.correction_factor = correction_factor

    def get_BMI(self):
        # BMI = body weight (kg) / height^2 (meter)
        return self.BW / ((self.height/100) ** 2)

    def get_basal_rate_mU_min(self):
        return self.basal_rate * 1000 / 60

    def get_basal_rate(self):
        return self.basal_rate

    def update_by_dictionary(self, dictionary):
        self.gender = dictionary["gender"]
        self.age = dictionary["age"]
        self.waist_size = dictionary["waist_size"]
        self.BW = dictionary["BW"]
        self.height = dictionary["height"]
        self.HbA1c = dictionary["HbA1c"]
        self.insulin2carb_ratio = dictionary["insulin2carb_ratio"]
        self.basal_rate = dictionary["basal_rate"]
        self.correction_factor = dictionary["correction_factor"]

    def get_parameters_dictionary(self):
        return {
            'gender': self.gender,
            'age': self.age,
            'waist_size': self.waist_size,
            'BW': self.BW,
            'height': self.height,
            'HbA1c': self.HbA1c,
            'insulin2carb_ratio': self.insulin2carb_ratio,
            'basal_rate': self.basal_rate,
            'correction_factor': self.correction_factor
        }


class Hovorka_Model_Extended_States_Matrix:
    pw = 36
    num_states = 13

    def __init__(self, state_matrix=deque(np.zeros((pw, num_states)), maxlen=pw)):
        self.state_matrix = state_matrix

    def get_current_state_vector(self):
        return self.state_matrix[-1]

    def get_previous_state_vector(self):
        return self.state_matrix[-2]

    def get_current_state_object(self):
        return Hovorka_Model_Extended_States_Object(np.array(self.state_matrix[-1]))

    def get_previous_state_object(self):
        return Hovorka_Model_Extended_States_Object(np.array(self.state_matrix[-2]))

    def push_current_state_vector(self, state_vector):
        self.state_matrix.append(state_vector)


class Hovorka_Model_States_Object_0:
    num_states = 12

    def __init__(self, state_vector=np.zeros(num_states)):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.D1 = state_vector[5]
        self.D2 = state_vector[6]
        self.R1 = state_vector[7]
        self.R2 = state_vector[8]
        self.x1 = state_vector[9]
        self.x2 = state_vector[10]
        self.x3 = state_vector[11]

    def get_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.D1, self.D2, self.R1, self.R2, self.x1, self.x2, self.x3])

    def update_by_vector(self, state_vector):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.D1 = state_vector[5]
        self.D2 = state_vector[6]
        self.R1 = state_vector[7]
        self.R2 = state_vector[8]
        self.x1 = state_vector[9]
        self.x2 = state_vector[10]
        self.x3 = state_vector[11]

    def update_by_dictionary(self, dictionary):
        self.S1 = dictionary["S1"]
        self.S2 = dictionary["S2"]
        self.PIC = dictionary["PIC"]
        self.G = dictionary["G"]
        self.Q2 = dictionary["Q2"]
        self.D1 = dictionary["D1"]
        self.D2 = dictionary["D2"]
        self.R1 = dictionary["R1"]
        self.R2 = dictionary["R2"]
        self.x1 = dictionary["x1"]
        self.x2 = dictionary["x2"]
        self.x3 = dictionary["x3"]

    @classmethod
    def get_PIC_pos(cls):
        return np.concatenate(([0, 0, 1], np.zeros(cls.num_states - 3)))


class Hovorka_Model_States_Object_1:
    num_states = 10

    def __init__(self, state_vector=np.zeros(num_states)):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]

    def get_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3])

    def update_by_vector(self, state_vector):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]

    @classmethod
    def get_PIC_pos(cls):
        return np.concatenate(([0, 0, 1], np.zeros(cls.num_states-3)))


class Hovorka_Model_Extended_States_Object:
    num_states = 13

    def __init__(self, state_vector=np.zeros(num_states)):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.TmaxI = state_vector[10]
        self.Ke = state_vector[11]
        self.Ug = state_vector[12]

    def get_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3, self.TmaxI, self.Ke, self.Ug])

    def get_short_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3])

    def get_short_state_object(self):
        return Hovorka_Model_States_Object_1(self.get_short_state_vector())

    def update_by_vector(self, state_vector):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.TmaxI = state_vector[10]
        self.Ke = state_vector[11]
        self.Ug = state_vector[12]

    @staticmethod
    def get_PIC_pos():
        return np.concatenate(([0, 0, 1], np.zeros(Hovorka_Model_Extended_States_Object.num_states - 3)))


class Linear_State_Space_Model:
    # T is the sample time which by default is set to 5 min
    def __init__(self, A=None, B=None, C=None, D=None, x0=None, u0=None, f0=None, T=5):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.x0 = x0
        self.u0 = u0
        self.f0 = f0
        self.T = T

    def get_state_num(self):
        return self.A.shape[0]

    def get_input_num(self):
        return self.B.shape[1]

    def get_input_num_artificial(self):
        return self.B.shape[1] + 1

    def get_output_num(self):
        return self.C.shape[0]

    def get_A(self):
        return self.A

    def get_B(self):
        return self.B

    def get_B_artificial(self):
        return np.concatenate((self.B, np.reshape(self.T * self.f0, (-1, 1))), axis=1)

    def get_C(self):
        return self.C

    def get_D(self):
        return self.D


class Quadratic_Optimization_Problem:

    def __init__(self, H=None, f=None, A=None, b=None, Aeq=None, beq=None, lb=None, ub=None, x0=None, options=None):
        self.H = H
        self.f = f
        self.A = A
        self.b = b
        self.Aeq = Aeq
        self.beq = beq
        self.lb = lb
        self.ub = ub
        self.x0 = x0
        self.options = options


class MPC_Objective_Function_Params:

    def __init__(self, prediction_horizon=None, Q_x=None, Q_e=None, Q_u=None, Q_du=None, Q_PIC=None, PIC_pos=None, ysp=None):
        self.prediction_horizon = prediction_horizon
        self.Q_x = Q_x
        self.Q_e = Q_e
        self.Q_u = Q_u
        self.Q_du = Q_du
        self.Q_PIC = Q_PIC
        self.PIC_pos = PIC_pos
        self.ysp = ysp


class Bounds:

    def __init__(self, u_min=None, u_max=None, x_min=None, x_max=None, y_min=None, y_max=None, du_min=None, du_max=None):
        self.u_min = u_min
        self.u_max = u_max
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.du_min = du_min
        self.du_max = du_max


# ===================================================================================================================
# these classes are used in the version in which MPC model has a meal compartment

class Hovorka_Model_Extended_States_Matrix_MealComp0:
    pw = 36
    num_states = 12

    def __init__(self, state_matrix=deque(np.zeros((pw, num_states)), maxlen=pw)):
        self.state_matrix = state_matrix

    def get_current_state_vector(self):
        return self.state_matrix[-1]

    def get_previous_state_vector(self):
        return self.state_matrix[-2]

    def get_current_state_object(self):
        return Hovorka_Model_Extended_States_Object_MealComp0(np.array(self.state_matrix[-1]))

    def get_previous_state_object(self):
        return Hovorka_Model_Extended_States_Object_MealComp0(np.array(self.state_matrix[-2]))

    def push_current_state_vector(self, state_vector):
        self.state_matrix.append(state_vector)


class Hovorka_Model_Extended_States_Object_MealComp0:
    num_states = 12

    def __init__(self, state_vector=np.zeros(num_states)):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.D1 = state_vector[10]
        self.D2 = state_vector[11]

    def get_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3, self.D1, self.D2])

    def get_short_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3, self.D1, self.D2])

    def get_short_state_object(self):
        return Hovorka_Model_States_Object_1_MealComp0(self.get_short_state_vector())

    def update_by_vector(self, state_vector):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.D1 = state_vector[10]
        self.D2 = state_vector[11]

    @classmethod
    def get_PIC_pos(cls):
        return np.concatenate(([0, 0, 1], np.zeros(cls.num_states - 3)))


class Hovorka_Model_States_Object_1_MealComp0:
    num_states = 12

    def __init__(self, state_vector=np.zeros(num_states)):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.D1 = state_vector[10]
        self.D2 = state_vector[11]

    def get_state_vector(self):
        return np.array([self.S1, self.S2, self.PIC, self.G, self.Q2, self.R1, self.R2, self.x1, self.x2, self.x3, self.D1, self.D2])

    def update_by_vector(self, state_vector):
        if state_vector.ndim > 1:
            state_vector = np.reshape(state_vector, -1)

        self.S1 = state_vector[0]
        self.S2 = state_vector[1]
        self.PIC = state_vector[2]
        self.G = state_vector[3]
        self.Q2 = state_vector[4]
        self.R1 = state_vector[5]
        self.R2 = state_vector[6]
        self.x1 = state_vector[7]
        self.x2 = state_vector[8]
        self.x3 = state_vector[9]
        self.D1 = state_vector[10]
        self.D2 = state_vector[11]

    @classmethod
    def get_PIC_pos(cls):
        return np.concatenate(([0, 0, 1], np.zeros(cls.num_states-3)))


class Scenario:
    # scenario should be defined based on 1 min sample time
    T = 1

    def __init__(self, meal=np.zeros(24 * 60), energy_expenditure=np.zeros(24 * 60)):
        self.meal = meal
        self.energy_expenditure = energy_expenditure


class Data_TS:
    # TS is the acronym for Total Simulation
    # observer_states are the states that are estimated by the UKF
    # model_parameters are the parameters that are identified by the NRLS
    delta = 5

    def __init__(self):
        self.basal = []
        self.bolus = []
        self.hypo_prob = []
        self.hyper_prob = []
        self.observer_states = []
        self.model_parameters = []
        self.cgm = []
        self.P_UKF = []
        self.energy_expenditure = []
        self.hovorka_params = []
        self.fast_carb = []
        self.input_vector = []
        self.push_num = 0
        self.max_bolus = []

    def push_basal(self, value):
        self.basal.append(value)

    def push_bolus(self, value):
        self.bolus.append(value)

    def push_hypo_prob(self, value):
        self.hypo_prob.append(value)

    def push_hyper_prob(self, value):
        self.hyper_prob.append(value)

    def push_observer_states(self, value):
        self.observer_states.append(value)

    def push_model_parameters(self, value):
        self.model_parameters.append(value)

    def push_cgm(self, value):
        self.cgm.append(value)
        self.push_num += 1

    def push_P_UKF(self, value):
        self.P_UKF.append(value)

    def push_energy_expenditure(self, value):
        self.energy_expenditure.append(value)

    def push_hovorka_params(self, value):
        self.hovorka_params.append(value)

    def push_fast_carb(self, value):
        self.fast_carb.append(value)

    def push_input_vector(self, value):
        self.input_vector.append(value)

    def get_insulin_vector_mu_per_min(self, n=0):
        if n == 0:
            return np.array(self.basal) * 1000 / 60 + np.array(self.bolus) * 1000 / Data_TS.delta
        else:
            return np.array(self.basal[-n:]) * 1000 / 60 + np.array(self.bolus[-n:]) * 1000 / Data_TS.delta

    def get_cgm(self, n=0):
        if n == 0:
            return np.array(self.cgm)
        else:
            return np.array(self.cgm[-n:])

    def get_G(self, n=0):
        if n == 0:
            return np.array(self.cgm) / 18
        else:
            return np.array(self.cgm[-n:]) / 18

    def get_energy_expenditure(self, n=0):
        if n == 0:
            return np.array(self.energy_expenditure)
        else:
            return np.array(self.energy_expenditure[-n:])

    def get_fast_carb(self, n=0):
        if n == 0:
            return np.array(self.fast_carb)
        else:
            return np.array(self.fast_carb[-n:])

    def get_input_vector(self, n=0):
        if n == 0:
            return np.array(self.input_vector)
        else:
            return np.array(self.input_vector[-n:])

    def push_max_bolus(self, value):
        self.max_bolus.append(value)

    def get_max_bolus(self, n=0):
        if n == 0:
            return np.array(self.max_bolus)
        else:
            return np.array(self.max_bolus[-n:])

    @staticmethod
    def expand_vector(vector):
        return np.kron(vector, np.ones(Data_TS.delta))


class Flags:
    # this class will store all flags for entire simulation
    def __init__(self):
        self.mpc_solver_success_flag = 0
        self.mpc_solver_fail_flag = 0

    def mpc_solver_success_plus_one(self):
        self.mpc_solver_success_flag += 1

    def mpc_solver_fail_plus_one(self):
        self.mpc_solver_fail_flag += 1

    def get_mpc_solver_success_flag_percent(self):
        return self.mpc_solver_success_flag / (self.mpc_solver_success_flag + self.mpc_solver_fail_flag) * 100


class Metric_Evaluator:
    # this class calculates the TBR, TIR and TAR
    severe_hyper_threshold = 250
    hyper_threshold = 180
    tight_hyper_threshold = 140
    hypo_threshold = 70
    severe_hypo_threshold = 54

    def __init__(self, cgm_matrix):
        cgm_matrix_ = np.array(cgm_matrix)
        if cgm_matrix_.ndim < 2:
            cgm_matrix_ = cgm_matrix_.reshape(1, -1)

        self.cgm_matrix = np.array(cgm_matrix_)

    def get_TBR(self):
        # time percent below hypo threshold
        tbr_mat = self.cgm_matrix < Metric_Evaluator.hypo_threshold
        tbr = np.mean(tbr_mat, axis=1) * 100
        return tbr

    def get_overall_TBR(self):
        # time percent below hypo threshold
        return np.mean(self.get_TBR())

    def get_TAR(self):
        # time percent above hyper threshold
        tar_mat = self.cgm_matrix > Metric_Evaluator.hyper_threshold
        tar = np.mean(tar_mat, axis=1) * 100
        return tar

    def get_overall_TAR(self):
        # time percent above hyper threshold
        return np.mean(self.get_TAR())

    def get_TIR(self):
        # time percent in range
        return 100 - (self.get_TBR() + self.get_TAR())

    def get_overall_TIR(self):
        # time percent in range
        return np.mean(self.get_TIR())

    def get_TBSR(self):
        # time percent below hypo severe threshold
        tbsr_mat = self.cgm_matrix < Metric_Evaluator.severe_hypo_threshold
        tbsr = np.mean(tbsr_mat, axis=1) * 100
        return tbsr

    def get_overall_TBSR(self):
        # time percent below hypo severe threshold
        return np.mean(self.get_TBSR())

    def get_TASR(self):
        # time percent above hyper severe threshold
        tasr_mat = self.cgm_matrix > Metric_Evaluator.severe_hyper_threshold
        tasr = np.mean(tasr_mat, axis=1) * 100
        return tasr

    def get_overall_TASR(self):
        # time percent above hyper severe threshold
        return np.mean(self.get_TASR())

    def get_TATR(self):
        # time percent above hyper tight threshold
        tatr_mat = self.cgm_matrix > Metric_Evaluator.tight_hyper_threshold
        tatr = np.mean(tatr_mat, axis=1) * 100
        return tatr

    def get_overall_TATR(self):
        # time percent above hyper tight threshold
        return np.mean(self.get_TATR())

    def get_TITR(self):
        # time percent in tight range
        return 100 - (self.get_TBR() + self.get_TATR())

    def get_overall_TITR(self):
        # time percent in tight range
        return np.mean(self.get_TITR())

    def get_GRI(self):
        # glycemic risk index
        # GRI = 3 * severe_hypo + 2.4 * hypo + 1.6 * severe_hyper + 0.8 * hyper
        return 3 * self.get_TBSR() + 2.4 * self.get_TBR() + 1.6 * self.get_TASR() + 0.8 * self.get_TAR()

    def get_overall_GRI(self):
        # glycemic risk index
        return np.mean(self.get_GRI())

    def get_MIN(self):
        return np.min(self.cgm_matrix, axis=1)

    def get_overall_MIN(self):
        return np.min(self.get_MIN())

    def get_MAX(self):
        return np.max(self.cgm_matrix, axis=1)

    def get_overall_MAX(self):
        return np.max(self.get_MAX())

    def get_MEAN(self):
        return np.mean(self.cgm_matrix, axis=1)

    def get_SD(self):
        # standard deviation
        return np.std(self.cgm_matrix, axis=1)

















