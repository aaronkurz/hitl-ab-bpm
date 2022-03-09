import streamlit as st
import dashboard.controls
import dashboard.data
import dashboard.end_of_experiment

def dashboard():
    st.title('Dashboard')
    controls.control_area()
    data.data()
    if st.session_state['cool_off']:
        end_of_experiment.end_of_experiment()