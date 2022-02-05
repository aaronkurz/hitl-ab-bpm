import help
import streamlit as st
import requests
from matplotlib import pyplot as plt
from pandas import DataFrame
from config import BACKEND_URI
import utils


def dashboard():
    st.write('## Dashboard')
    controls()
    data()


def controls():
    st.write('### Controls')
    manual_decision()
    if st.button("Check for new batch policy proposal") or st.session_state['new_proposal'] is True:
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

            batch_size = st.number_input("Enter batch size", step=1, value=10)
            exploration_probabilities_a = []
            exploration_probabilities_b = []
            for i in range(len(proposal_json.get('executionStrategy'))):
                customer_category = proposal_json.get('executionStrategy')[i].get('customerCategory')
                st.caption(customer_category)
                exploration_probabilities_a.append(st.slider("Enter exploration probability for process A:", min_value=0.0,
                                                         max_value=1.0, value=proposal_json.get('executionStrategy')[i].get('explorationProbabilityA'), step=0.01, key="a_" + customer_category))
                exploration_probabilities_b.append(st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0,
                                                         step=0.1, value=1.0 - exploration_probabilities_a[i], key="b_" + customer_category,
                                                         disabled=True))
            if st.button("Submit"):
                bapol_json = {
                    'batchSize': batch_size,
                    'executionStrategy': []
                }
                for i in range(len(proposal_json.get('executionStrategy'))):
                    bapol_json.get('executionStrategy').append({
                        'customerCategory': proposal_json.get('executionStrategy')[i].get('customerCategory'),
                        'explorationProbability_A_pub': exploration_probabilities_a[i],
                        'explorationProbability_B_pub': exploration_probabilities_b[i]
                    })
                response = requests.post(BACKEND_URI + "batch-policy",
                                         json=bapol_json,
                                         headers={"Content-Type": "application/json"},
                                         params={'process-id': utils.get_currently_active_process_id()})
                if response.status_code == requests.codes.ok:
                    st.write("✅ Batch Policy uploaded")
                    st.session_state['new_proposal'] = False
                    st.experimental_rerun()
                else:
                    st.write("🚨 Upload of Batch Policy failed: HTTP status code " + str(response.status_code))


def manual_decision():
    successfully_posted_manual_dec = None
    if st.button("Manual decision: Version A"):
        successfully_posted_manual_dec = utils.post_manual_decision('a')
    if st.button("Manual decision: Version B"):
        successfully_posted_manual_dec = utils.post_manual_decision('b')
    if successfully_posted_manual_dec:
        st.write("✅")
    elif successfully_posted_manual_dec is False:
        st.write("🚨 Something went wrong")


def plot_instances():
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BACKEND_URI + "instance-router/aggregate-data/client-requests", params=params)
    if response.status_code != requests.codes.ok:
        st.write("🚨 Can't fetch data right now")
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
    aggregate_data()
    detailed_data()


def detailed_data():
    st.write('#### Detailed Data')
    with st.expander('What is shown here?', expanded=False):
        st.write(help.DETAILED_DATA)
    if st.button("Refresh", key="10") or st.session_state['data_detailed_open'] is True:
        st.session_state['data_detailed_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response_bapol_count = requests.get(BACKEND_URI + "batch-policy/count", params=params)
        if response_bapol_count.status_code != requests.codes.ok:
            st.write("🚨 Can't fetch data right now")
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
                response_batch_instances = requests.get(BACKEND_URI + "instance-router/detailed-data/batch", params=params)
                if response_batch_instances.status_code != requests.codes.ok:
                    st.write("🚨 Can't fetch data right now")
                else:
                    batch_instances_df = DataFrame(columns=["Version", "Start Time", "End Time", "Reward"])
                    for i in range(len(response_batch_instances.json().get("instances"))):
                        batch_instances_df.loc[i] = [response_batch_instances.json().get("instances")[i].get("decision"),
                                                     response_batch_instances.json().get("instances")[i].get("startTime"),
                                                     response_batch_instances.json().get("instances")[i].get("endTime"),
                                                     response_batch_instances.json().get("instances")[i].get("reward"),
                                                     ]
                    st.write("Batch Number: ", response_batch_instances.json().get("batchNumber"))
                    st.table(batch_instances_df)




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
            st.write("🚨 Can't fetch data right now")
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
