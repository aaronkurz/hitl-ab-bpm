import json
from utils import get_currently_active_process_id, post_manual_decision
import streamlit as st
import requests
import matplotlib.pyplot as plt
from config import BACKEND_URI


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
                    response = requests.post(BACKEND_URI + "/process-variants/" + process_name, files=files_in)
                    # then
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Files uploaded, continue below.")
                    else:
                        st.write("🚨️ File upload unsuccessful! Try again.")
                else:
                    st.write("⚠️ Both variant a and variant b have to be uploaded at once and a name has to be given.")                   


def set_bapol():
    with st.expander("📐 Step 2: Set Batch Policy", expanded=True):
        decay = st.number_input("Enter decay (lambda) value")
        length = st.number_input("Enter length (M) value:")

        #Execution strategy
        #CustomerCategory: public
        st.caption("Category: Public")
        explorationProbability_A_pub = st.slider("Enter exploration probability for process A:", min_value=0.0, max_value=1.0, step=0.01, key="a_pub")
        explorationProbability_B_pub = st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0, step=0.01, key="b_pub")

        #CustomerCategory: gov (dynamic)
        st.caption("Category: Gov")
        explorationProbability_A_gov = st.slider("Exploration probability for process A:", min_value=0.0, max_value=1.0, step=0.01, value=1.0-explorationProbability_A_pub, key="a_gov", disabled=True)
        explorationProbability_B_gov = st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0, step=0.01, value=1.0 - explorationProbability_B_pub, key="b_gov", disabled=True)

        with st.form(key="Set Bapol2"):
            if st.form_submit_button("Submit"):
                try:
                    bapol_json = json.dumps( #create a json file from the given values
                        {
                            'experimentationDecay':decay,
                            'experimentationLength':length,
                            'executionStrategy':[
                                {
                                    'customerCategory':'public',
                                    'explorationProbability_A_pub':explorationProbability_A_pub,
                                    'explorationProbability_B_pub':explorationProbability_B_pub
                                },
                                {
                                    'customerCategory':'gov',
                                    'explorationProbability_A_gov':explorationProbability_A_gov,
                                    'explorationProbability_B_gov':explorationProbability_B_gov
                                }
                            ]
                        }
                    , separators=(',', ':'))
                    
                    response = requests.post(BACKEND_URI + "/batch-policy", json=bapol_json,
                                                headers={"Content-Type": "application/json"})
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Batch Policy uploaded, continue below.")
                    else:
                        st.write("🚨 Upload of Batch Policy failed: HTTP status code " + str(response.status_code))
                except ValueError as ve:
                    st.write("🚨 Entered Batch Policy is not a valid JSON: " + str(ve))
            else:
                st.write("⚠️ Please enter Batch Policy before submitting")


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


def main():
    st.set_page_config(page_title="AB-BPM", page_icon="🔁")
    st.title("AB-BPM Dashboard 🎮")
    upload_files()
    set_lepol()
    experiment_cockpit()


if __name__ == '__main__':
    main()
