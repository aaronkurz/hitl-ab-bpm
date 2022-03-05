import streamlit as st
import requests
from config import BACKEND_URI
import utils

def end_of_experiment():
    st.write("### End of Experiment")
    st.write('#### Final Proposal')
    response_final_prop = requests.get(BACKEND_URI + "batch-policy-proposal/final", params={
        "process-id": utils.get_currently_active_process_id()
    })
    if response_final_prop.status_code == requests.codes.ok:
        for exec_strat in response_final_prop.json().get('executionStrategy'):
            st.write("**Customer Category: " + exec_strat.get('customerCategory') +"**")
            st.write("Likelihood, with which agent would choose version a: ", exec_strat.get('explorationProbabilityA'))
            st.write("Likelihood, with which agent would choose version b: ", exec_strat.get('explorationProbabilityB'))
        decision = []
        for exec_strat in response_final_prop.json().get('executionStrategy'):
            cust_cat = exec_strat.get('customerCategory')
            winning_version = st.radio("Choose winning version for customer category " + cust_cat, ('a', 'b'))
            decision.append({
                'customer_category': cust_cat,
                'winning_version': winning_version
            })
        if st.button("Submit Choice"):
            response_set_winner = requests.post(BACKEND_URI + "process/active/winning", json={
                'decision': decision
            })
            if response_set_winner.status_code == requests.codes.ok:
                st.success("Winning version set successfully")
                st.session_state['cool_off'] = False
            else:
                st.exception("Setting winning version failed.")
    elif response_final_prop.status_code == 404:
        st.warning("No final proposal available at the moment.")
    else:
        st.exception("Fetching of final proposal failed.")