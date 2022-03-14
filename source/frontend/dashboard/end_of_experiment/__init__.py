""" Show area to make final decision about winner/s of experiment """
import streamlit as st
import requests
from resources import user_assistance
from config import BACKEND_URI
import utils


def display_final_bapol_prop(response_final_prop_json: any):
    """ Display final bapol proposal and allow for sending final decision

    :param response_final_prop_json: JSOn if final bapol proposal
    """
    for exec_strat in response_final_prop_json.get('executionStrategy'):
        st.write("**Customer Category: " + exec_strat.get('customerCategory') + "**")
        st.write("Likelihood, with which agent would choose version a: ", exec_strat.get('explorationProbabilityA'))
        st.write("Likelihood, with which agent would choose version b: ", exec_strat.get('explorationProbabilityB'))
    decision = []
    for exec_strat in response_final_prop_json.get('executionStrategy'):
        cust_cat = exec_strat.get('customerCategory')
        winning_version = st.radio("Choose winning version for customer category " + cust_cat, ('a', 'b'))
        decision.append({
            'customer_category': cust_cat,
            'winning_version': winning_version
        })
    if st.button("Submit Choice", help=user_assistance.SUBMIT_CHOICE_BUTTON):
        response_set_winner = requests.post(BACKEND_URI + "process/active/winning", json={
            'decision': decision
        })
        if response_set_winner.status_code == requests.codes.ok:  # pylint: disable=no-member
            st.success("Winning version set successfully")
            st.session_state['cool_off'] = False
        else:
            st.exception("Setting winning version failed.")


def end_exp_show_evaluation_progress():
    """ Show the evaluation progress and possibility to trigger fetch and learn """
    response_evaluation_progress = \
        requests.get(BACKEND_URI + "instance-router/aggregate-data/evaluation-progress",
                     params={"process-id": utils.get_currently_active_process_id()})
    st.warning("No final proposal available at the moment. Only available at when all of the experimental "
               "instances have been finished and evaluated. Current evaluation progress: " +
               str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) + "%.")
    if st.button("Refresh", help=user_assistance.MANUAL_TRIGGER_FETCH_LEARN, key="refresh-end-of-exp-retrigger"):
        response_manual_trigger = requests.post(BACKEND_URI + "process/active/trigger-fetch-learn")
        assert response_manual_trigger.status_code == requests.codes.ok  # pylint: disable=no-member
        st.experimental_rerun()


def end_of_experiment():
    """ Show area to make final decision about winner/s of experiment """
    st.write("### End of Experiment")
    st.write('#### Final Proposal')
    response_final_prop = requests.get(BACKEND_URI + "batch-policy-proposal/final", params={
        "process-id": utils.get_currently_active_process_id()
    })
    if response_final_prop.status_code == requests.codes.ok:  # pylint: disable=no-member
        display_final_bapol_prop(response_final_prop.json())
    elif response_final_prop.status_code == 404:
        end_exp_show_evaluation_progress()
    else:
        st.exception("Fetching of final proposal failed.")
