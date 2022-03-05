import streamlit as st
import utils
from config import BACKEND_URI
import requests
import datetime
from resources import help


def proposal_expander():
    with st.expander("Batch Policy Proposal", expanded=True):
        if utils.currently_active_process_exists():

            response_evaluation_progress = \
                requests.get(BACKEND_URI + "instance-router/aggregate-data/evaluation-progress",
                             params={"process-id": utils.get_currently_active_process_id()})
            assert response_evaluation_progress.status_code == requests.codes.ok
            if response_evaluation_progress.json().get("alreadyEvaluatedPerc") is not None:
                if response_evaluation_progress.json().get("alreadyEvaluatedPerc") < 0.5:
                    st.warning(
                        "The current percentage of already evaluated experimental instances is very low, with an evaluation rate of only " +
                        str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) +
                        "%. Consider waiting before setting the next batch policy. The batch policy proposal "
                        "below will be updated periodically once more instances finish and are evaluated.")
                elif response_evaluation_progress.json().get("alreadyEvaluatedPerc") < 0.8:
                    st.info("The current percentage of already evaluated experimental instances is at " +
                            str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) +
                            "%. The batch policy proposal "
                            "below will be updated periodically once more instances finish and are evaluated.")
                elif response_evaluation_progress.json().get("alreadyEvaluatedPerc") < 1.0:
                    st.success("The current percentage of already evaluated experimental instances is high, with an " +
                               str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) +
                               "% evaluation rate. The batch policy proposal "
                               "below will be updated periodically once more instances finish and are evaluated.")
                else:
                    st.success("All prior experimental instances are finished and have been evaluated and taken into " +
                               "account for the batch policy below (" +
                               str(round(response_evaluation_progress.json().get("alreadyEvaluatedPerc") * 100, 2)) +
                               "% evaluation rate).")

            interarrival_time_sec = utils.get_currently_active_process_meta().get('default_interarrival_time_history')
            params = {
                'process-id': utils.get_currently_active_process_id()
            }
            bapol_proposal_response = requests.get(BACKEND_URI + "batch-policy-proposal/open", params=params)
            if bapol_proposal_response.status_code != requests.codes.ok:
                st.write("Something went wrong while polling for a new batch policy proposal")
            elif bapol_proposal_response.json().get('newProposalExists') is False:
                st.write('No new batch policy proposal available at this time')
            elif bapol_proposal_response.json().get('newProposalExists') is True or st.session_state[
                'new_proposal'] is True:
                st.session_state['new_proposal'] = True
                st.write(
                    "__This is the new batch policy proposal. Feel free to submit it as is or modify it and then submit it.__")

                proposal_json = bapol_proposal_response.json().get('proposal')

                batch_size = st.number_input("Enter batch size", step=1, value=10, help=help.BATCH_SIZE_HELP)
                st.write("Given this batch size of ", batch_size, ", it will take approximately ",
                         datetime.timedelta(seconds=(interarrival_time_sec * batch_size)),
                         " (hours:minutes:seconds) until the next batch policy proposal will be available.")
                exploration_probabilities_a = []
                exploration_probabilities_b = []
                for i in range(len(proposal_json.get('executionStrategy'))):
                    customer_category = proposal_json.get('executionStrategy')[i].get('customerCategory')
                    st.write("**Customer Category: " + customer_category + "**")
                    exploration_probabilities_a.append(
                        st.slider("Enter exploration probability for process A:", min_value=0.0,
                                  max_value=1.0,
                                  value=proposal_json.get('executionStrategy')[i].get('explorationProbabilityA'),
                                  step=0.01, key="a_" + customer_category))
                    exploration_probabilities_b.append(
                        st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0,
                                  step=0.1, value=1.0 - exploration_probabilities_a[i], key="b_" + customer_category,
                                  disabled=True))
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Submit"):
                        bapol_json = {
                            'batchSize': batch_size,
                            'executionStrategy': []
                        }
                        for i in range(len(proposal_json.get('executionStrategy'))):
                            bapol_json.get('executionStrategy').append({
                                'customerCategory': proposal_json.get('executionStrategy')[i].get('customerCategory'),
                                'explorationProbabilityA': exploration_probabilities_a[i],
                                'explorationProbabilityB': exploration_probabilities_b[i]
                            })
                        st.session_state['bapol_json'] = bapol_json
                        response = requests.post(BACKEND_URI + "batch-policy",
                                                 json=bapol_json,
                                                 headers={"Content-Type": "application/json"},
                                                 params={'process-id': utils.get_currently_active_process_id()})
                        if response.status_code == requests.codes.ok:
                            st.session_state['new_proposal'] = False
                            st.session_state['bapol_upload_success'] = True
                            st.session_state['bapol_upload_failed'] = False
                            st.experimental_rerun()
                        else:
                            st.session_state['bapol_upload_success'] = False
                            st.session_state['bapol_upload_failed'] = True
                with col2:
                    if utils.get_bapol_count() > 0:
                        if st.button("End Experiment/Start Cool-Off",
                                     help="For more info on Cool-Off, see dashboard help expander"):
                            post_cool_off_response = requests.post(BACKEND_URI + "process/active/cool-off")
                            if post_cool_off_response.status_code == requests.codes.ok:
                                st.session_state['post_cool_off_success'] = True
                                st.session_state['cool_off'] = True
                                st.session_state['post_cool_off_failed'] = False
                            else:
                                st.session_state['post_cool_off_failed'] = True
                                st.session_state['post_cool_off_success'] = False
        else:
            st.warning("No active process/experiment. Please start one by uploading process variants above.")