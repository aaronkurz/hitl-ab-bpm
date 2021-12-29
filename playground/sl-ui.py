import json

import streamlit as st
import requests

BACKEND_BASE_URL = "http://localhost:5001"


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
                    response = requests.post(BACKEND_BASE_URL + "/process-variants/" + process_name, files=files_in)
                    # then
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Files uploaded, continue below.")
                    else:
                        st.write("🚨️ File upload unsuccessful! Try again.")
                else:
                    st.write("⚠️ Both variant a and variant b have to be uploaded at once and a name has to be given.")


def set_bapol():
    with st.expander("📐 Step 2: Set Batch Policy", expanded=True):
        with st.form(key="Set Bapol"):
            tooltip = """Please enter the json of your Batch Policy. Example:
            
            {
            "batchSize": 200,
            "executionStrategy": [
                {
                    "customerCategory": "public",
                    "explorationProbabilityA": 1.3,
                    "explorationProbabilityB": 0.7
                },
                {
                    "customerCategory": "gov",
                    "explorationProbabilityA": 0.7,
                    "explorationProbabilityB": 0.3
                }
            ]
            }
            """
            bapol_input = st.text_area("Enter Batch Policy JSON", help=tooltip)
            if st.form_submit_button("Submit"):
                if bapol_input.replace(" ", "") != "":
                    try:
                        bapol_json = json.loads(bapol_input)
                        response = requests.post(BACKEND_BASE_URL + "/batch-policy", json=bapol_json,
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
