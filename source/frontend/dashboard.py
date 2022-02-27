import datetime
import help
import streamlit as st
import requests
from matplotlib import pyplot as plt
from pandas import DataFrame
from config import BACKEND_URI
import utils
import client_simulator


def dashboard():
    st.write('## Dashboard')
    controls()
    data()
    if st.session_state['cool_off']:
        end_of_experiment()


def controls():
    st.write('### Controls')
    with st.expander('What is the controls area?', expanded=False):
        st.write(help.CONTROLS_HELP)
        st.write(help.COOL_OFF_DETAILED)
        st.write("---")
        dev_mode = st.checkbox('Activate Dev Mode', help=help.DEV_MODE_HELP)
        if dev_mode is True:
            st.session_state['dev_mode'] = True
        elif dev_mode is False:
            st.session_state['dev_mode'] = False
    manual_decision()
    if (st.button("Check for new Batch Policy Proposal") or st.session_state['new_proposal'] is True) \
            and st.session_state['post_cool_off_success'] is False:
        with st.expander("Batch Policy Proposal", expanded=True):
            if utils.currently_active_process_exists():
                interarrival_time_sec = utils.get_currently_active_process_meta().get('default_interarrival_time_history')
                params = {
                    'process-id': utils.get_currently_active_process_id()
                }
                bapol_proposal_response = requests.get(BACKEND_URI + "batch-policy-proposal/open", params=params)
                if bapol_proposal_response.status_code != requests.codes.ok:
                    st.write("Something went wrong while polling for a new batch policy proposal")
                elif bapol_proposal_response.json().get('newProposalExists') is False:
                    st.write('No new batch policy proposal available at this time')
                elif bapol_proposal_response.json().get('newProposalExists') is True or st.session_state['new_proposal'] is True:
                    st.session_state['new_proposal'] = True
                    st.write("__This is the new batch policy proposal. Feel free to submit it as is or modify it and then submit it.__")

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
                            if st.button("End Experiment/Start Cool-Off", help="For more info on Cool-Off, see dashboard help expander"):
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

    if st.session_state['bapol_upload_success'] is True:
        st.success("Batch Policy upload successful")
        st.session_state['bapol_upload_success'] = False
    if st.session_state['bapol_upload_failed']:
        st.exception("Upload of Batch Policy failed: HTTP status code " + str(response.status_code))
        st.session_state['bapol_upload_failed'] = False
    if st.session_state['post_cool_off_failed']:
        st.exception("Starting Cool-Off failed.")
        st.session_state['post_cool_off_failed'] = False
    if st.session_state['post_cool_off_success']:
        st.success("Starting Cool-Off successful")
        st.session_state['post_cool_off_success'] = False

    if st.session_state['dev_mode']:
        with st.expander("Dev Mode: Client Simulator"):
            simulate_batch_size = st.number_input("Enter batch size to be simulated", step=1, value=10)
            simulate_batch_interarrival_time = st.number_input("Enter average break between instantiations (in seconds)",
                                                               step=0.1, value=1.0)
            if st.button("Simulate"):
                client_simulator.run_simulation(simulate_batch_size, simulate_batch_interarrival_time)
                st.success("Simulation done")


def manual_decision():
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


def plot_instances():
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BACKEND_URI + "instance-router/aggregate-data/client-requests", params=params)
    if response.status_code != requests.codes.ok:
        st.exception("🚨 Can't fetch data right now")
    response_json = response.json()
    if response_json.get('noTotalRequests') > 0:
        plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsA'), label='Version A')
        plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsB'), label='Version B')
        plt.legend(loc='upper left')
        plt.xlabel('Total requests')
        plt.ylabel('Requests per version')
        plt.xlim(left=0)
        plt.ylim(bottom=0)
        st.pyplot(fig=plt.gcf())
    else:
        st.write("No instantiations yet. Plot of instantiation decisions will be shown here.")


def data():
    st.write("### Data")
    data_view = st.selectbox("Choose Data View",
                 ("Experiment Metadata", "Aggregate Data", "Detailed Data"))
    if data_view == "Experiment Metadata":
        experiment_metadata()
    elif data_view == "Aggregate Data":
        aggregate_data()
    elif data_view == "Detailed Data":
        detailed_data()


def experiment_metadata():
    st.write("#### Experiment Metadata")
    with st.expander("What is shown here?", expanded=False):
        st.write(help.EXPERIMENT_METADATA)
    if st.button("Refresh", key="refresh_exp_meta"):
        response_meta = requests.get(BACKEND_URI + "process/active/meta")
        if response_meta.status_code == requests.codes.ok:
            process_meta_json = response_meta.json()
            col1, col2 = st.columns(2)
            with col1:
                st.write("*Process name*: ", process_meta_json.get('name'))
                st.write("*Start of experiment*: ", process_meta_json.get('datetime_added'))
                st.write("*State*: ", process_meta_json.get('experiment_state'))
                st.write("*Customer categories*: ", process_meta_json.get('customer_categories'))
            with col2:
                st.write("*Default/old version*: ", process_meta_json.get('default_version'))
                st.write("*Winning versions*: ", process_meta_json.get('winning_versions'))
                st.write("*End of experiment*: ", process_meta_json.get('datetime_decided'))
        elif response_meta.status_code == 400:
            st.write("No running experiment yet. Upload proces versions above to start an experiment.")


def detailed_data():
    st.write('#### Detailed Data')
    with st.expander('What is shown here?', expanded=False):
        st.write(help.DETAILED_DATA)
    if st.button("Refresh", key="10") or st.session_state['data_detailed_open'] is True:
        st.session_state['data_detailed_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response_bapol_count = requests.get(BACKEND_URI + "batch-policy/count", params=params)
        if response_bapol_count.status_code != requests.codes.ok:
            st.exception("🚨 Can't fetch data right now")
        else:
            batch_choice = st.selectbox(
                'Which batch would you like to see details about?',
                tuple(range(1, response_bapol_count.json().get('batchPolicyCount') + 1)),
                help=help.BATCH_NUMBER_CHOICE)

            if batch_choice is not None:
                params = {
                    "process-id": utils.get_currently_active_process_id(),
                    "batch-number": batch_choice
                }
                response_batch_instances = requests.get(BACKEND_URI + "instance-router/detailed-data/batch",
                                                        params=params)
                if response_batch_instances.status_code != requests.codes.ok:
                    st.exception("🚨 Can't fetch data right now")
                else:
                    batch_instances_df = DataFrame(
                        columns=["Version", "Customer Category", "Start Time", "End Time", "Reward"])
                    for i in range(len(response_batch_instances.json().get("instances"))):
                        batch_instances_df.loc[i] = [
                            response_batch_instances.json().get("instances")[i].get("decision"),
                            response_batch_instances.json().get("instances")[i].get("customerCategory"),
                            response_batch_instances.json().get("instances")[i].get("startTime"),
                            response_batch_instances.json().get("instances")[i].get("endTime"),
                            response_batch_instances.json().get("instances")[i].get("reward"),
                            ]
                    st.write("Batch Number: ", response_batch_instances.json().get("batchNumber"))
                    st.table(batch_instances_df)

                    batch_instanes_csv = batch_instances_df.to_csv().encode('utf-8')

                    st.download_button(
                        "Download as CSV",
                        batch_instanes_csv,
                        "batch_" + str(batch_choice) + "_instances.csv",
                        "text/csv",
                        key='download-batch-instances-csv'
                    )


def aggregate_data():
    st.write('#### Aggregate Data')
    with st.expander('What is shown here?', expanded=False):
        st.write(help.AGGREGATE_DATA)
    if st.button("Refresh") or st.session_state['data_open'] is True:
        st.session_state['data_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response = requests.get(
            BACKEND_URI + "instance-router/aggregate-data", params=params
        )
        if response.status_code != requests.codes.ok:
            st.exception("🚨 Can't fetch data right now")
        else:
            aggregate_data_df = DataFrame(
                columns=['Version', 'Number Started', 'Number Finished', 'Mean Duration (sec)', 'Mean Reward'])
            versions = ['a', 'b']
            for i in range(2):
                aggregate_data_df.loc[i] = [versions[i],
                                            response.json().get(versions[i]).get("numberStarted"),
                                            response.json().get(versions[i]).get("numberFinished"),
                                            None if response.json().get(versions[i]).get("averageDurationSec") is None
                                            else round(response.json().get(versions[i]).get("averageDurationSec"), 2),
                                            None if response.json().get(versions[i]).get("averageReward") is None
                                            else round(response.json().get(versions[i]).get("averageReward"), 2), ]
            # HIDE ROW INDICES:
            # CSS to inject contained in a string
            hide_table_row_index = """
                            <style>
                            tbody th {display:none}
                            .blank {display:none}
                            </style>
                            """
            # Inject CSS with Markdown

            st.markdown(hide_table_row_index, unsafe_allow_html=True)

            st.table(aggregate_data_df.astype(str))

        plot_instances()


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
