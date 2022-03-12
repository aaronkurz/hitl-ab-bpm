import streamlit as st
import requests
from resources import user_assistance
from config import BACKEND_URI


def upload_files():
    st.title("Upload Metadata")
    st.write("... and start experiment!")
    with st.expander("Upload Process Versions", expanded=True):
        with st.form(key="Upload Files"):
            process_name = st.text_input("Process name")
            f_a = st.file_uploader("Upload process variant A", type=['bpmn'])
            f_b = st.file_uploader("Upload process variant B", type=['bpmn'])
            customer_categories = st.text_input("Customer categories (separate with dash -)",
                                                help=help.CUSTOMER_CATEGORIES_INPUT)
            default=st.radio("Default version", ('a', 'b'),
                             help=help.DEFAULT_VERSION_INPUT)
            default_history = st.file_uploader("Upload data about default version", type=['json'],
                                               help=help.HISTORY_UPLOAD_DEFAULT)
            if st.form_submit_button("Submit"):
                if f_a is not None \
                        and f_b is not None \
                        and process_name.replace(" ", "") != ""\
                        and customer_categories.replace(" ", "") != ""\
                        and default_history is not None:
                    files_in = {
                        "variantA": f_a,
                        "variantB": f_b,
                        "defaultHistory": default_history
                    }
                    params = {
                        'customer-categories': customer_categories,
                        'default-version': default,
                    }
                    response = requests.post(BACKEND_URI + "process/" + process_name, files=files_in, params=params)
                    if response.status_code == requests.codes.ok:
                        st.success("Files uploaded, continue below.")
                    else:
                        st.exception("File upload unsuccessful! Try again.")
                else:
                    st.warning("All fields have to be supplied.")
