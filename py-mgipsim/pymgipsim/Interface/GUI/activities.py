import streamlit as st
from pymgipsim.VirtualPatient.Models.T1DM import ExtHovorka
import pandas as pd

def activities():
    st.header("Activity settings")
    if st.session_state.args.model_name == ExtHovorka.Model.name:
        st.session_state.activity_type = st.selectbox(
            "Activity type",
            ("🏃‍ Running", "🚴‍♂️ Cycling")
        )
        if st.session_state.activity_type == "🏃‍ Running":
            sequence_table = pd.DataFrame({"Time (min)": [17*60],
                                           "Duration (min)": [30],
                                        "Speed (mph)": [0.0],
                                           "Gradient (%)": [0.0]})
            edited_seq = st.data_editor(sequence_table, key=st.session_state.act_seq_dek, hide_index=False, num_rows="dynamic")
            time = edited_seq["Time (min)"].to_list()
            running_duration = edited_seq["Duration (min)"].to_list()
            running_speed = edited_seq["Speed (mph)"].to_list()
            running_incline = edited_seq["Gradient (%)"].to_list()
            st.session_state.args.manual_running_start_time = time
            st.session_state.args.manual_running_duration = running_duration
            st.session_state.args.manual_running_speed = running_speed
            st.session_state.args.manual_running_incline = running_incline
        if st.session_state.activity_type == "🚴‍♂️ Cycling":
            sequence_table = pd.DataFrame({"Time (min)": [17*60],
                                           "Duration (min)": [30],
                                        "Power (Watt)": [0.0]})
            edited_seq = st.data_editor(sequence_table, key=st.session_state.act_seq_dek, hide_index=False, num_rows="dynamic")
            time = edited_seq["Time (min)"].to_list()
            duration = edited_seq["Duration (min)"].to_list()
            power = edited_seq["Power (Watt)"].to_list()
            st.session_state.args.manual_cycling_start_time = time
            st.session_state.args.manual_cycling_duration = duration
            st.session_state.args.manual_cycling_power = power
    else:
        st.session_state.activity_type = ""
        st.write("Only virtual cohort with type 1 diabetes supports activities currently.")