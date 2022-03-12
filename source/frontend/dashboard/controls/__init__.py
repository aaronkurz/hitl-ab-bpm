""" Containing methods related to controls-area in frontend

Elements for batch policy (proposal); manual decision; dev mode; ...
"""
from dashboard.controls import batch_policy
import streamlit as st
import utils
from resources import user_assistance
import client_simulator

def control_area():
    """ General controls-area, linking to other methods generating the parts of the controls-area"""
    st.write('### Controls')
    with st.expander('What is the controls area?', expanded=False):
        st.write(user_assistance.CONTROLS_HELP)
        st.write(user_assistance.COOL_OFF_DETAILED)
        st.write(user_assistance.EXPERIMENTAL_INSTANCE)
        st.write("---")
        dev_mode = st.checkbox('Activate Dev Mode', help=user_assistance.DEV_MODE_HELP)
        if dev_mode is True:
            st.session_state['dev_mode'] = True
        elif dev_mode is False:
            st.session_state['dev_mode'] = False
    manual_decision()
    if (st.button("Check for new Batch Policy Proposal") or st.session_state['new_proposal'] is True) \
            and st.session_state['post_cool_off_success'] is False:
        batch_policy.proposal_expander()

    if st.session_state['bapol_upload_success'] is True:
        st.success("Batch Policy upload successful")
        st.session_state['bapol_upload_success'] = False
    if st.session_state['bapol_upload_failed']:
        st.exception("Upload of Batch Policy failed")
        st.session_state['bapol_upload_failed'] = False
    if st.session_state['post_cool_off_failed']:
        st.exception("Starting Cool-Off failed.")
        st.session_state['post_cool_off_failed'] = False
    if st.session_state['post_cool_off_success']:
        st.success("Starting Cool-Off successful")
        st.session_state['post_cool_off_success'] = False

    if st.session_state['dev_mode']:
        with st.expander("Dev Mode: Client Simulator"):
            simulate_batch_size = st.number_input("Enter batch size to be simulated",
                                                  step=1,
                                                  value=10)
            simulate_batch_interarrival_time = \
                st.number_input("Enter average break between instantiations (in seconds)",
                                step=0.1,
                                value=1.0)
            if st.button("Simulate"):
                client_simulator.run_simulation(simulate_batch_size, simulate_batch_interarrival_time)
                st.success("Simulation done")


def manual_decision():
    """ Display the controls for allowing user to make manual decision """
    col1, col2, col3 = st.columns(3)
    successfully_posted_manual_dec = None
    with col1:
        if st.button("Manual Decision: Version A"):
            successfully_posted_manual_dec = utils.post_manual_decision('a')

    with col2:
        if st.button("Manual Decision: Version B"):
            successfully_posted_manual_dec = utils.post_manual_decision('b')
    with col3:
        if successfully_posted_manual_dec:
            st.success("✅")
        elif successfully_posted_manual_dec is False:
            st.exception("🚨 Something went wrong")
