import streamlit as st
import requests
from resources import user_assistance
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
        if st.button("Submit Choice", help=help.SUBMIT_CHOICE_BUTTON):
            response_set_winner = requests.post(BACKEND_URI + "process/active/winning", json={
                'decision': decision
            })
            if response_set_winner.status_code == requests.codes.ok:
                st.success("Winning version set successfully")
                st.session_state['cool_off'] = False
            else:
                st.exception("Setting winning version failed.")
    elif response_final_prop.status_code == 404:
        response_evaluation_progress = \
            requests.get(BACKEND_URI + "instance-router/aggregate-data/evaluation-progress",
                         params={"process-id": utils.get_currently_active_process_id()})
        st.warning("No final proposal available at the moment. Only available at when all of the experimental "
                   "instances have been finished and evaluated. Current evaluation progress: " +
                   str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) + "%.")
        if st.button("Refresh", help=help.MANUAL_TRIGGER_FETCH_LEARN, key="refresh-end-of-exp-retrigger"):
            response_manual_trigger = requests.post(BACKEND_URI + "process/active/trigger-fetch-learn")
            assert response_manual_trigger.status_code == requests.codes.ok
            st.experimental_rerun()
    else:
        st.exception("Fetching of final proposal failed.")