import streamlit as st
import requests
from config import BACKEND_URI

from utils import get_currently_active_process_id, post_manual_decision

st.set_option('deprecation.showPyplotGlobalUse', False)
from display_results import *


def upload_files():
    with st.expander("⬆️ Step 1: Upload Process Versions", expanded=True):
        with st.form(key="Upload Files"):
            process_name = st.text_input("Process name")
            f_a = st.file_uploader("Upload process variant A", type=['bpmn'])
            f_b = st.file_uploader("Upload process variant B", type=['bpmn'])
            if st.form_submit_button("Submit"):
                if f_a is not None and f_b is not None and process_name.replace(" ", "") != "":
                    files_in = {
                        "variantA": f_a,
                        "variantB": f_b
                    }
                    # when
                    response = requests.post(BACKEND_URI + "/process/" + process_name, files=files_in)
                    # then
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Files uploaded, continue below.")
                    else:
                        st.write("🚨️ File upload unsuccessful! Try again.")
                else:
                    st.write("⚠️ Both variant a and variant b have to be uploaded at once and a name has to be given.")


def set_bapol():
    with st.expander("📐 Step 2: Set Batch Policy", expanded=True):
        batch_size = st.number_input("Enter batch size")

        # Execution strategy
        # CustomerCategory: public
        st.caption("Category: Public")
        explorationProbability_A_pub = st.slider("Enter exploration probability for process A:", min_value=0.0,
                                                 max_value=1.0, value=0.5, step=0.01, key="a_pub")
        explorationProbability_B_pub = st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0,
                                                 step=0.1, value=1.0 - explorationProbability_A_pub, key="b_pub",
                                                 disabled=True)

        # CustomerCategory: gov (dynamic)
        st.caption("Category: Gov")
        explorationProbability_A_gov = st.slider("Exploration probability for process A:", min_value=0.0, max_value=1.0,
                                                 value=0.5, step=0.01, key="a_gov")
        explorationProbability_B_gov = st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0,
                                                 step=0.1, value=1.0 - explorationProbability_A_gov, key="b_gov",
                                                 disabled=True)
        if st.button("Submit"):
            try:
                bapol_json = {
                    'batchSize': batch_size,
                    'executionStrategy': [
                        {
                            'customerCategory': 'public',
                            'explorationProbability_A_pub': explorationProbability_A_pub,
                            'explorationProbability_B_pub': explorationProbability_B_pub
                        },
                        {
                            'customerCategory': 'gov',
                            'explorationProbability_A_gov': explorationProbability_A_gov,
                            'explorationProbability_B_gov': explorationProbability_B_gov
                        }
                    ]
                }

                response = requests.post(BACKEND_URI + "/batch-policy", json=bapol_json,
                                         headers={"Content-Type": "application/json"})
                if response.status_code == requests.codes.ok:
                    st.write("✅ Batch Policy uploaded, continue below.")
                else:
                    st.write("🚨 Upload of Batch Policy failed: HTTP status code " + str(response.status_code))
            except ValueError as ve:
                st.write("🚨 Entered Batch Policy is not a valid JSON: " + str(ve))


def manual_decision():
    successfully_posted_manual_dec = None
    if st.button("Manual decision: Version A"):
        successfully_posted_manual_dec = post_manual_decision('a')
    if st.button("Manual decision: Version B"):
        successfully_posted_manual_dec = post_manual_decision('b')
    if successfully_posted_manual_dec:
        st.write("✅")
    elif successfully_posted_manual_dec is False:
        st.write("🚨 Something went wrong")


def plot_instances():
    params = {"process-id": get_currently_active_process_id()}
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


def experiment_cockpit():
    with st.expander("⌚️ Step 3: Experiment Cockpit", expanded=True):
        manual_decision()
        st.markdown("***")
        if st.button("Refresh"):
            params = {"process-id": get_currently_active_process_id()}

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


def main():
    st.set_page_config(page_title="AB-BPM", page_icon="🔁")
    st.title("AB-BPM Dashboard 🎮")
    upload_files()
    set_bapol()
    experiment_cockpit()
    display_results()
    view_results()


if __name__ == '__main__':
    main()
