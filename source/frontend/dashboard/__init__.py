""" Dashboard to manage experiment, make decisions and view state/data """
import streamlit as st
from dashboard import controls, data, end_of_experiment


def dashboard():
    """ Dashboard to manage experiment, make decisions and view state/data """
    st.title('Dashboard')
    controls.control_area()
    data.data()
    if st.session_state['cool_off']:
        end_of_experiment.end_of_experiment()
