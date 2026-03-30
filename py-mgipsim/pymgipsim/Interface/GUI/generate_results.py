import statsmodels.tsa.vector_ar.svar_model
import streamlit.components.v1 as components
import copy
from pymgipsim.InputGeneration.activity_settings import activity_args_to_scenario
from pymgipsim.generate_settings import generate_simulation_settings_main
from pymgipsim.generate_inputs import generate_inputs_main
from pymgipsim.generate_subjects import generate_virtual_subjects_main
from pymgipsim.generate_results import generate_results_main, get_metrics
from pymgipsim.Interface.GUI.plots import *
import numpy as np
from pymgipsim.Utilities.Scenario import scenario, save_scenario
from pymgipsim.InputGeneration.heart_rate_settings import generate_heart_rate
from pymgipsim.InputGeneration.energy_expenditure_settings import generate_energy_expenditure
from pymgipsim.Utilities.simulation_folder import save_to_xls
import io
import pandas as pd
import base64
import json
import simplejson
from dataclasses import asdict
import os


def download_button(object_to_download, download_filename):
    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    dl_link = f"""
    <html>
    <head>
    <title>Start Auto Download file</title>
    <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
    <script>
    $('<a href="data:text/csv;base64,{b64}" download="{download_filename}">')[0].click()
    </script>
    </head>
    </html>
    """
    return dl_link

@st.fragment
def download_df():
    with st.spinner('Exporting results...'):
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            save_to_xls(st.session_state.model.states.as_array,
                        st.session_state.model.states.state_names,
                        st.session_state.model.states.state_units, writer, False)
    components.html(
        download_button(output.getvalue(), "state_results.xlsx"),
        height=0,
    )

@st.fragment
def download_scenario():
    with st.spinner('Exporting scenario...'):
        scenario = asdict(st.session_state.simulated_scenario)
    components.html(
        download_button(json.dumps(scenario, indent=4).encode('utf-8'), "scenario.json"),
        height=0,
    )

@st.fragment
def download_metrics():
    components.html(
        download_button(simplejson.dumps(st.session_state.metrics, indent=4, default=default, ignore_nan=True).encode('utf-8'), "metrics.json"),
        height=0,
    )


def color_col_high(val,thr):
    color = '#a8e36d' if val>thr else '#f5909c'
    return f'background-color: {color}'

def color_col_low(val,thr):
    color = '#a8e36d' if val<thr else '#f5909c'
    return f'background-color: {color}'

def default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()

def generate_metrics():
    #st.code("""Cappon G, Sparacino G, Facchinetti A. AGATA: A toolbox for automated glucose data analysis.
#J Diabetes Sci Technol. 2023. DOI: 10.1177/19322968221147570""", language=None, line_numbers=False)
    try:
        time_in_target, time_in_tight_target, time_in_hypo, time_in_hyper, glucose_risk_index = [], [], [], [], []
        for metrics in st.session_state.metrics:
            time_in_target.append(metrics["time_in_ranges"]["time_in_target"])
            time_in_tight_target.append(metrics["time_in_ranges"]["time_in_tight_target"])
            time_in_hypo.append(metrics["time_in_ranges"]["time_in_hypoglycemia"])
            time_in_hyper.append(metrics["time_in_ranges"]["time_in_hyperglycemia"])
            glucose_risk_index.append(metrics['risk']['gri'])
        if st.session_state.simulated_scenario.patient.model.name == T1DM.ExtHovorka.Model.name:
            patient_list = [file.replace(".json", "") for file in st.session_state.simulated_scenario.patient.files]
        else:
            patient_list = np.arange(st.session_state.simulated_scenario.patient.number_of_subjects)
        metric_table = pd.DataFrame({'Patient': patient_list, 'Time In Hypo': time_in_hypo, 'TIR': time_in_target,
                                     'TITR': time_in_tight_target, 'Time In Hyper': time_in_hyper,
                                     'Glycemic Risk Index': glucose_risk_index})
        metric_table = metric_table.style.applymap(color_col_high, subset=['TIR'], thr=70.0)
        metric_table.applymap(color_col_low, subset=['Time In Hypo'], thr=4.0)
        metric_table.applymap(color_col_low, subset=['Time In Hypo'], thr=4.0)
        metric_table.applymap(color_col_low, subset=['Time In Hyper'], thr=25.0)
        metric_table.applymap(color_col_low, subset=['Glycemic Risk Index'], thr=20.0)
        st.dataframe(metric_table)
    except:
        pass

def run_simulation(uploaded_scenario):
    args = st.session_state.args
    args.running_speed = 0.0  # Turn off physical activity
    args.plot_patient = 0  # Plots patient glucose, intakes, heartrate
    args.random_seed = 100

    settings_file = copy.deepcopy(st.session_state.settings_file)
    settings_file.input_generation.breakfast_time_range = st.session_state.args.breakfast_time_range
    settings_file.input_generation.am_snack_time_range = st.session_state.args.am_snack_time_range
    settings_file.input_generation.lunch_time_range = st.session_state.args.lunch_time_range
    settings_file.input_generation.pm_snack_time_range = st.session_state.args.pm_snack_time_range
    settings_file.input_generation.dinner_time_range = st.session_state.args.dinner_time_range
    activity_args_to_scenario(settings_file, args)
    if not args.scenario_name:
        settings_file = generate_simulation_settings_main(scenario_instance=settings_file, args=args,
                                                          results_folder_path=st.session_state.results_folder_path)

        settings_file = generate_virtual_subjects_main(scenario_instance=settings_file, args=args,
                                                       results_folder_path=st.session_state.results_folder_path)

        settings_file = generate_inputs_main(scenario_instance=settings_file, args=args,
                                             results_folder_path=st.session_state.results_folder_path)

    if st.session_state.meal_generation_mode == "manual":
        settings_file.inputs.meal_carb.start_time = [st.session_state.args.manual_meal_times] * len(args.patient_names)
        settings_file.inputs.meal_carb.magnitude = [st.session_state.args.manual_meal_amounts] * len(args.patient_names)
        settings_file.inputs.meal_carb.duration = [[20] * len(st.session_state.args.manual_meal_times)] * len(
            args.patient_names)
        settings_file.inputs.snack_carb.start_time = [[]] * len(args.patient_names)
        settings_file.inputs.snack_carb.magnitude = [[]] * len(args.patient_names)
        settings_file.inputs.snack_carb.duration = [[]] * len(args.patient_names)
    if st.session_state.activity_type == "🏃‍ Running":
        settings_file.inputs.running_speed.start_time = [st.session_state.args.manual_running_start_time] * len(
            args.patient_names)
        settings_file.inputs.running_speed.duration = [st.session_state.args.manual_running_duration] * len(
            args.patient_names)
        settings_file.inputs.running_speed.magnitude = [st.session_state.args.manual_running_speed] * len(
            args.patient_names)
        settings_file.inputs.running_incline.start_time = [st.session_state.args.manual_running_start_time] * len(
            args.patient_names)
        settings_file.inputs.running_incline.duration = [st.session_state.args.manual_running_duration] * len(
            args.patient_names)
        settings_file.inputs.running_incline.magnitude = [st.session_state.args.manual_running_incline] * len(
            args.patient_names)
        settings_file.inputs.heart_rate, settings_file.inputs.METACSM = generate_heart_rate(settings_file, args)
        settings_file.inputs.energy_expenditure = generate_energy_expenditure(settings_file, args)
    if st.session_state.activity_type == "🚴‍♂️ Cycling":
        settings_file.inputs.cycling_power.start_time = [st.session_state.args.manual_cycling_start_time] * len(
            args.patient_names)
        settings_file.inputs.cycling_power.duration = [st.session_state.args.manual_cycling_duration] * len(
            args.patient_names)
        settings_file.inputs.cycling_power.magnitude = [st.session_state.args.manual_cycling_power] * len(
            args.patient_names)
        settings_file.inputs.heart_rate, settings_file.inputs.METACSM = generate_heart_rate(settings_file, args)
        settings_file.inputs.energy_expenditure = generate_energy_expenditure(settings_file, args)

    if uploaded_scenario is not None:
        settings_file = scenario(**json.loads(uploaded_scenario.getvalue()))
    save_scenario(os.path.join(st.session_state.results_folder_path, "simulation_settings.json"), asdict(settings_file))
    if settings_file.settings.simulator_name == "MultiScaleSolver":
        model_solver,metrics = generate_results_main(scenario_instance=settings_file, args=vars(args),
                                             results_folder_path=st.session_state.results_folder_path)
        st.session_state.model = model_solver.singlescale_model
        st.session_state.multiscale_model = model_solver.multiscale_model
    else:
        cohort,metrics = generate_results_main(scenario_instance=settings_file, args=vars(args),
                                                       results_folder_path=st.session_state.results_folder_path)
        st.session_state.model = cohort.model_solver.model
    st.session_state.simulated_scenario = settings_file
    st.session_state.metrics = metrics

def generate_results():
    st.header("Simulation results")
    st.markdown("""
                <style>
                    div[data-testid="column"] {
                        width: fit-content !important;
                        flex: unset;
                    }
                    div[data-testid="column"] * {
                        width: fit-content !important;
                    }
                </style>
                """, unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    uploaded_scenario = st.file_uploader("Load and run scenario","json")
    # st.header("Visualizations")
    if col1.button('▶️ Run simulation', type="primary"):
        with st.spinner('Running simulation...'):
            run_simulation(uploaded_scenario)
    expanded = False
    if st.session_state.model is not None:
        col2.button("📊 Download PYAGATA metrics (json)", on_click=download_metrics)
        col3.button("📝 Download states (xls)", on_click=download_df)
        col4.button("🗎 Download scenario (json)", on_click=download_scenario)
        expanded = True
    try:
        with st.expander("Plots",expanded):
            if st.session_state.simulated_scenario.patient.model.name == T1DM.ExtHovorka.Model.name:
                plot_hovorka()
            # if st.session_state.simulated_scenario.patient.model.name == T2DM.Jauslin.Model.name:
            #     plot_jauslin()
            #     if st.session_state.args.multi_scale:
            #         plot_multiscale()
        with st.expander("Metrics",expanded):
            if st.button('Run PYAGATA (long computational time)', type="primary"):
                with st.spinner('Running Agata'):
                    st.session_state.metrics = get_metrics(st.session_state.model)
            generate_metrics()
    except:
       st.write("⚠️ Please rerun the simulation.")
