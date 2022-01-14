import json

import streamlit as st
import requests
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


# def set_bapol():
#     with st.expander("📐 Step 2: Set Batch Policy", expanded=True):
#         with st.form(key="Set Bapol"):
#             tooltip = """Please enter the json of your Batch Policy. Example:
            
#             {
#             "m": 0,
#             "lambda": 0, 
#             "executionStrategy": [
#                 {
#                     "customerCategory": "public",
#                     "explorationProbabilityA": 0.3,
#                     "explorationProbabilityB": 0.7
#                 },
#                 {
#                     "customerCategory": "gov",
#                     "explorationProbabilityA": 0.7,
#                     "explorationProbabilityB": 0.3
#                 }
#             ]
#             }
#             """
#             bapol_input = st.text_area("Enter Batch Policy JSON", help=tooltip)
#             if st.form_submit_button("Submit"):
#                 if bapol_input.replace(" ", "") != "":
#                     try:
#                         bapol_json = json.loads(bapol_input)
#                         response = requests.post(BACKEND_URI + "/batch-policy", json=bapol_json,
#                                                  headers={"Content-Type": "application/json"})
#                         if response.status_code == requests.codes.ok:
#                             st.write("✅ Batch Policy uploaded, continue below.")
#                         else:
#                             st.write("🚨 Upload of Batch Policy failed: HTTP status code " + str(response.status_code))
#                     except ValueError as ve:
#                         st.write("🚨 Entered Batch Policy is not a valid JSON: " + str(ve))
#                 else:
#                     st.write("⚠️ Please enter Batch Policy before submitting")


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
        explorationProbability_A_gov = st.slider("Exploration probability for process A:", min_value=0.0, max_value=1.0, step=0.01, value=1.0-explorationProbability_A_pub, key="a_gov")
        explorationProbability_B_gov = st.slider("Exploration probability for process B:", min_value=0.0, max_value=1.0, step=0.01, value=1.0 - explorationProbability_B_pub, key="b_gov")

        #TODO: make slider values depend on each other (atm the gov category is depends on the pub category; however user is able to change gov *after* setting pub -> this should not be the case; keyword disabled=True doesn't work...)

        with st.form(key="Set Bapol2"):
            if st.form_submit_button("Submit"):
                try:
                    bapol_json = json.dumps( #create a json file from the given values
                        {
                            'decay':decay,
                            'length':length,
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


def display_results():
    with st.expander("⌚️ Step 3: Wait For Results", expanded=True):
        st.write("To Be Implemented (Relevant API endpoints and functionality missing)")

def main():
    st.set_page_config(page_title="AB-BPM", page_icon="🔁")
    st.title("AB-BPM Dashboard 🎮")
    upload_files()
    set_bapol()
    display_results()


if __name__ == '__main__':
    main()
