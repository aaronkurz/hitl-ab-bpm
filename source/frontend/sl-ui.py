import json

import streamlit as st
import requests
from config import BACKEND_URI


def get_currently_active_process_id():
    response = requests.get(BACKEND_URI + "/process-variants/active-meta")
    assert response.status_code == requests.codes.ok
    return response.json().get("id")


def upload_files():
    with st.expander("⬆️ Step 1: Upload Process Versions", expanded=True):
        with st.form(key="Upload Files"):
            process_name = st.text_input("Process name")
            f_a = st.file_uploader("Upload process variant A", type=["bpmn"])
            f_b = st.file_uploader("Upload process variant B", type=["bpmn"])
            if st.form_submit_button("Submit"):
                if (
                    f_a is not None
                    and f_b is not None
                    and process_name.replace(" ", "") != ""
                ):
                    files_in = {"variantA": f_a, "variantB": f_b}
                    # when
                    response = requests.post(
                        BACKEND_URI + "/process-variants/" + process_name,
                        files=files_in,
                    )
                    # then
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Files uploaded, continue below.")
                    else:
                        st.write("🚨️ File upload unsuccessful! Try again.")
                else:
                    st.write(
                        "⚠️ Both variant a and variant b have to be uploaded at once and a name has to be given."
                    )


def set_lepol():
    with st.expander("📐 Step 2: Set Learning Policy", expanded=True):
        with st.form(key="Set Lepol"):
            tooltip = """Please enter the json of your Learning Policy. Example:
            
            {
                "experimentationLength": 200,
                "experimentationDecay": 5,
                "executionStrategy": [
                    {
                        "customerCategory": "public",
                        "explorationProbabilityA": 0.3,
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
            lepol_input = st.text_area("Enter Learning Policy JSON", help=tooltip)
            if st.form_submit_button("Submit"):
                if lepol_input.replace(" ", "") != "":
                    try:
                        lepol_json = json.loads(lepol_input)
                        response = requests.post(
                            BACKEND_URI + "/learning-policy",
                            json=lepol_json,
                            headers={"Content-Type": "application/json"},
                        )
                        if response.status_code == requests.codes.ok:
                            st.write("✅ Learning Policy uploaded, continue below.")
                        else:
                            st.write(
                                "🚨 Upload of Learning Policy failed: HTTP status code "
                                + str(response.status_code)
                            )
                    except ValueError as ve:
                        st.write(
                            "🚨 Entered Learning Policy is not a valid JSON: " + str(ve)
                        )
                else:
                    st.write("⚠️ Please enter Learning Policy before submitting")


def display_results():

    with st.expander("⌚️ Step 3: Wait For Results", expanded=True):

        if st.button("Refresh"):

            params = {"process-id": get_currently_active_process_id()}

            response = requests.get(
                BACKEND_URI + "instance-router/aggregate-data", params=params
            )

            if response.status_code != requests.codes.ok:
                st.write("Can't fetch Data righ now")

            else:

                amount_instances_a = response.json().get("a").get("amount")
                amount_instances_b = response.json().get("b").get("amount")

                st.write(f"Amount of instances sent to variant A {amount_instances_a}")
                st.write(f"Amount of instances sent to variant B {amount_instances_b}")


def main():
    st.set_page_config(page_title="AB-BPM", page_icon="🔁")
    st.title("AB-BPM Dashboard 🎮")
    upload_files()
    set_lepol()
    display_results()


if __name__ == "__main__":
    main()
