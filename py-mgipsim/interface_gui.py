# TO RUN THE GUI TYPE: streamlit run interface_gui.py

import streamlit as st
import uuid
import subprocess
from pymgipsim.Utilities.paths import results_path
from pymgipsim.Utilities import simulation_folder
from pymgipsim.Interface.GUI.cohort import cohort
from pymgipsim.Interface.GUI.meals import meals
from pymgipsim.Interface.GUI.therapies import therapies
from pymgipsim.Interface.GUI.generate_results import generate_results
from pymgipsim.Interface.GUI.activities import activities
from pymgipsim.Interface.parser import generate_parser_cli
from pymgipsim.generate_subjects import generate_virtual_subjects_main


st.set_page_config(layout="wide", page_icon="./app/static/star_logo.png")

css = '''
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size:2rem;
    }
</style>
'''

st.markdown(css, unsafe_allow_html=True)


if 'dek' not in st.session_state:
    st.session_state.dek = str(uuid.uuid4())
    st.session_state.input_dek = str(uuid.uuid4())
    st.session_state.model = None
    st.session_state.multiscale_model = None
    st.session_state.carb_seq_dek = str(uuid.uuid4())
    st.session_state.act_seq_dek = str(uuid.uuid4())
    st.session_state.meal_generation_mode = "random"
    st.session_state.activity_type = ""

with st.sidebar:
    st.markdown('''<h1> <img src = "./app/static/Flag_of_Chicago_Illinois2red.png" alt="**" style="padding: 0px 0px 0px 0px; margin: 0; max-height: 40px; width:auto; height:auto; display: inline-block; object-fit: contain; border-radius: 0;" /> mGIPsim </h1>''', unsafe_allow_html=True)

with open("./static/star_logo2.svg") as logo_file:
    logo = logo_file.read()
st.image(logo,width=80)

tab_general, tab_cohort, tab_therapies, tab_inputs, tab_activities, tab_results = st.tabs(["General","Cohort", "Therapies", "Meals", "Activities", "Results"])

# Session State also supports attribute based syntax
if 'args' not in st.session_state:
    with st.spinner('Initialization...'):
        args = generate_parser_cli().parse_args()  # Hardcoded selection of singlescale
        args.model_name = "T1DM.ExtHovorka"  # Select Hovorka model
        args.patient_names = ["Patient_1","Patient_2","Patient_3","Patient_4","Patient_5","Patient_6","Patient_7","Patient_8",
                              "Patient_9","Patient_10","Patient_11","Patient_12","Patient_13","Patient_14","Patient_15","Patient_16",
                              "Patient_17","Patient_18","Patient_19","Patient_20"]
        st.session_state.args = args
        subprocess.run(['python', 'initialization.py'])
        _, _, _, st.session_state.results_folder_path = simulation_folder.create_simulation_results_folder(results_path)
        settings_file = simulation_folder.load_settings_file(st.session_state.args, st.session_state.results_folder_path)
        st.session_state.settings_file = settings_file
        st.session_state.settings_file = generate_virtual_subjects_main(scenario_instance=st.session_state.settings_file, args=args, results_folder_path="")
        st.session_state.args.basals = st.session_state.settings_file.patient.demographic_info.basal


with tab_general:
    st.header("General settings")
    st.session_state.args.multi_scale = False#st.toggle("📅🕙 Multiscale simulation")
    sim_length = st.number_input(
        "🕙 Simulation length (days)", value=1.0, placeholder="days",
        min_value = 0.1, max_value = 30.0, step=1.0
    )
    st.session_state.args.number_of_days = sim_length

with tab_cohort:
    cohort()

with tab_therapies:
    therapies()

with tab_inputs:
    meals()

with tab_activities:
    activities()

with tab_results:
    generate_results()