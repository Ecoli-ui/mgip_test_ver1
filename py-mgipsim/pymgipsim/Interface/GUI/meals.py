import streamlit as st
import pandas as pd
def meals():
    st.header("Meals")
    if not st.session_state.args.multi_scale:
        on = st.toggle("Manual meal sequence")
        if on:
            sequence_table = pd.DataFrame({"Time": [8*60, 12*60, 18*60],
                                        "Amount": [30,90,50]})
            edited_seq = st.data_editor(sequence_table, key=st.session_state.carb_seq_dek, hide_index=False, num_rows="dynamic")
            st.session_state.meal_generation_mode = "manual"
            time = edited_seq["Time"].to_list()
            amount = edited_seq["Amount"].to_list()
            st.session_state.args.manual_meal_times = time
            st.session_state.args.manual_meal_amounts = amount
        else:
            st.write("Parameters for random generation")
            carb_bound_low = [st.session_state.settings_file.input_generation.breakfast_carb_range[0],
                           st.session_state.settings_file.input_generation.am_snack_carb_range[0],
                           st.session_state.settings_file.input_generation.lunch_carb_range[0],
                           st.session_state.settings_file.input_generation.pm_snack_carb_range[0],
                           st.session_state.settings_file.input_generation.dinner_carb_range[0]]
            carb_bound_high = [st.session_state.settings_file.input_generation.breakfast_carb_range[1],
                           st.session_state.settings_file.input_generation.am_snack_carb_range[1],
                           st.session_state.settings_file.input_generation.lunch_carb_range[1],
                           st.session_state.settings_file.input_generation.pm_snack_carb_range[1],
                           st.session_state.settings_file.input_generation.dinner_carb_range[1]]
            timing_bound_low = [st.session_state.settings_file.input_generation.breakfast_time_range[0],
                       st.session_state.settings_file.input_generation.am_snack_time_range[0],
                        st.session_state.settings_file.input_generation.lunch_time_range[0],
                       st.session_state.settings_file.input_generation.pm_snack_time_range[0],
                        st.session_state.settings_file.input_generation.dinner_time_range[0]]
            timing_bound_high = [st.session_state.settings_file.input_generation.breakfast_time_range[1],
                       st.session_state.settings_file.input_generation.am_snack_time_range[1],
                        st.session_state.settings_file.input_generation.lunch_time_range[1],
                       st.session_state.settings_file.input_generation.pm_snack_time_range[1],
                        st.session_state.settings_file.input_generation.dinner_time_range[1]]
            input_table = pd.DataFrame({"Meal":["🥪☕ Breakfast","🍎 AM snack", "🍛 Lunch", "🍌 PM snack", "🥗 Dinner"],
                               "Timing lower bound":timing_bound_low,"Timing upper bound":timing_bound_high,
                                        "Amount lower bound":carb_bound_low,"Amount upper bound":carb_bound_high})


            edited = st.data_editor(input_table, key=st.session_state.input_dek, hide_index=False, disabled=("Meal",))
            loa = edited["Amount lower bound"].to_list()
            upa = edited["Amount upper bound"].to_list()
            lot = edited["Timing lower bound"].to_list()
            upt = edited["Timing upper bound"].to_list()
            st.session_state.args.breakfast_carb_range = [loa[0],upa[0]]
            st.session_state.args.am_snack_carb_range = [loa[1], upa[1]]
            st.session_state.args.lunch_carb_range = [loa[2], upa[2]]
            st.session_state.args.pm_snack_carb_range = [loa[3], upa[3]]
            st.session_state.args.dinner_carb_range = [loa[4], upa[4]]
            st.session_state.args.breakfast_time_range = [lot[0],upt[0]]
            st.session_state.args.am_snack_time_range = [lot[1], upt[1]]
            st.session_state.args.lunch_time_range = [lot[2], upt[2]]
            st.session_state.args.pm_snack_time_range = [lot[3], upt[3]]
            st.session_state.args.dinner_time_range = [lot[4], upt[4]]
            st.session_state.meal_generation_mode = "random"
    else:
        net_calorie_balance = st.slider("⚖️ Net calorie balance", min_value=-1000, max_value=1000, value=0, step=50)
        st.session_state.args.net_calorie_balance = [net_calorie_balance]