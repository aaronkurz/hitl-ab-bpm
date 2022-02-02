import streamlit as st
import requests
from matplotlib import pyplot as plt

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
            st.write("New bapol proposal:")
            st.write(bapol_proposal_response.json().get('proposal'))
            st.write("Set a new batch policy here:")

            proposal_json = bapol_proposal_response.json().get('proposal')

            batch_size = st.number_input("Enter batch size", step=1)
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
    plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsA'), label='Version A')
    plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsB'), label='Version B')
    plt.legend(loc='upper left')
    plt.xlabel('Total requests')
    plt.ylabel('Requests per version')
    st.pyplot(fig=plt.gcf())


def data():
    st.write("### Data")
    if st.button("Refresh") or st.session_state['data_open'] is True:
        st.session_state['data_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response = requests.get(
            BACKEND_URI + "instance-router/aggregate-data", params=params
        )
        if response.status_code != requests.codes.ok:
            st.write("🚨 Can't fetch data right now")

        else:
            amount_instances_a = response.json().get("a").get("amount")
            amount_instances_b = response.json().get("b").get("amount")

            st.write("Amount of instances sent to variant A: ", amount_instances_a)
            st.write(f"Amount of instances sent to variant B: ", amount_instances_b)

        plot_instances()


def display_results():
    with st.expander("⌚️ Step 3: Wait For Results", expanded=True):
        if st.button("Refresh", key = "uniq id"):

            params = {"process-id": get_currently_active_process_id()}

            response = requests.get(
                BACKEND_URI + "instance-router/aggregate-data", params=params
            )

            if response.status_code != requests.codes.ok:
                st.write("Can't fetch Data right now")

            else:

                amount_instances_a = response.json().get("a").get("amount")
                amount_instances_b = response.json().get("b").get("amount")

                st.write(f"Amount of instances sent to variant A {amount_instances_a}")
                st.write(f"Amount of instances sent to variant B {amount_instances_b}")
        with st.form(key="Execution history"):
            if st.form_submit_button(
                    "Clean up history"):  # https://docs.camunda.org/manual/7.16/reference/rest/history/history-cleanup/post-history-cleanup/
                requests.post(
                    BACKEND_URI + "instance-router/clean-up-history"
                )
            st.write("Number of total activities:",
                     requests.get(BACKEND_URI + "instance-router/get-activity-count").json().get('activity_count'))
            st.write("Number of total batch:",
                     requests.get(BACKEND_URI + "instance-router/get-batch-count").json().get('batch_count'))
            st.write("Number of total process:",
                     requests.get(BACKEND_URI + "instance-router/get-process-count").json().get('process_count'))

            st.write("Time based cost")
            plt_cost()
            st.write("Reward")
            plt_reward()
            st.write("action_prob")


def view_results():
    with st.expander("⌚️ Step 4: View Results", expanded=True):
        options = st.multiselect(
            'Actions you would like to view',
            ['A', 'B'],
            ['A'])

        plt_action_prob(options)