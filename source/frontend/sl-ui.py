import streamlit as st
import uploader
import dashboard


def setup():
    if 'new_proposal' not in st.session_state:
        st.session_state['new_proposal'] = False
    if 'data_open' not in st.session_state:
        st.session_state['data_open'] = False
    if 'data_detailed_open' not in st.session_state:
        st.session_state['data_detailed_open'] = False
    if 'data_detailed_batch_open' not in st.session_state:
        st.session_state['data_detailed_batch_open'] = False
    if 'bapol_upload_success' not in st.session_state:
        st.session_state['bapol_upload_success'] = False
    if 'dev_mode' not in st.session_state:
        st.session_state['dev_mode'] = False


def main():
    st.set_page_config(page_title="HITL-AB-BPM", page_icon="🔁")
    setup()
    st.title("HITL-AB-BPM Experiment-Cockpit")
    uploader.upload_files()
    dashboard.dashboard()


if __name__ == '__main__':
    main()
