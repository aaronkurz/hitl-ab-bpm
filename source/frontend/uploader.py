import streamlit as st
import requests
from config import BACKEND_URI


def upload_files():
    with st.expander("Upload Process Versions", expanded=True):
        with st.form(key="Upload Files"):
            process_name = st.text_input("Process name")
            f_a = st.file_uploader("Upload process variant A", type=['bpmn'])
            f_b = st.file_uploader("Upload process variant B", type=['bpmn'])
            customer_categories = st.text_input("Customer categories (separate with dash -)")
            default=st.radio("Default version", ('a', 'b'))
            min_dur_a = st.number_input("Minimum duration A (s)", step=0.1)
            max_dur_a = st.number_input("Maximum duration A (s)", step=0.1)
            if st.form_submit_button("Submit"):
                if f_a is not None \
                        and f_b is not None \
                        and process_name.replace(" ", "") != ""\
                        and customer_categories.replace(" ", "") != ""\
                        and min_dur_a != 0.0\
                        and max_dur_a != 0.0:
                    files_in = {
                        "variantA": f_a,
                        "variantB": f_b
                    }
                    params = {
                        'customer-categories': customer_categories,
                        'default-version': default,
                        "a-hist-min-duration": min_dur_a,
                        "a-hist-max-duration": max_dur_a
                    }
                    response = requests.post(BACKEND_URI + "/process/" + process_name, files=files_in, params=params)
                    if response.status_code == requests.codes.ok:
                        st.write("✅ Files uploaded, continue below.")
                    else:
                        st.write("🚨️ File upload unsuccessful! Try again.")
                else:
                    st.write("⚠️ All fields have to be supplied.")
