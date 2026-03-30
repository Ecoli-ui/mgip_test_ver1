import streamlit as st
import pandas as pd
import uuid
from pymgipsim.VirtualPatient.Models import *

def cohort():
    st.header("Cohort settings")
    if st.button('Reset'):
        st.session_state.dek = str(uuid.uuid4())

    if st.session_state.args.multi_scale:
        model_options = ("Type 2 diabetes",)
    else:
        model_options = ("Type 1 diabetes",)

    diabetes_type = st.selectbox(
        "Diabetes type",
        model_options
    )
    if diabetes_type == "Type 1 diabetes":
        st.session_state.args.model_name = "T1DM.ExtHovorka"
        st.markdown("Extended Hovorka model with physical activity submodel [link](%s)." % "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7449052/")
    else:
        st.session_state.args.model_name = "T2DM.Jauslin"

    if st.session_state.args.model_name == T1DM.ExtHovorka.Model.name:
        pat_names = []
        for pat in st.session_state.settings_file.patient.files:
            pat_names.append(pat.replace(".json", ""))
        basals = st.session_state.settings_file.patient.demographic_info.basal
        body_weights = st.session_state.settings_file.patient.demographic_info.body_weight
        hba1c = st.session_state.settings_file.patient.demographic_info.HbA1c

        # if 'cohort_table' not in st.session_state:
        cohort_table = pd.DataFrame({"ID":pat_names,
                           "Basal rate":basals,"Body weight":body_weights,"HbA1c":hba1c})
        # st.session_state.args.patient_names = st.session_state.cohort_table["Patients"].to_list()
        # st.session_state.args.basals = st.session_state.cohort_table["Basal rate"].to_list()
        edited = st.data_editor(cohort_table, key=st.session_state.dek,hide_index=False, num_rows="dynamic", disabled=("ID","Basal rate","Body weight","HbA1c"))
        st.session_state.args.patient_names = edited["ID"].to_list()
        st.session_state.args.basals = edited["Basal rate"].to_list()
    else:
        number_of_subjects = st.number_input(
            "Number of subjects", value=10,
            min_value=1, max_value=100, step=1
        )
        renal_function_category = st.slider("Renal function category", min_value=1, max_value=5, value=1, step=1)
        st.session_state.args.renal_function_category = renal_function_category
        st.session_state.args.number_of_subjects = number_of_subjects
        st.session_state.args.patient_names = None