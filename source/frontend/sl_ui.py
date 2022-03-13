""" Entrypoint for frontend streamlit app """
import streamlit as st
import uploader
import dashboard
import sidebar


def setup():
    """ Initialize session state """
    # pylint: disable=too-complex
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
    if 'bapol_upload_failed' not in st.session_state:
        st.session_state['bapol_upload_failed'] = False
    if 'dev_mode' not in st.session_state:
        st.session_state['dev_mode'] = False
    if 'post_cool_off_success' not in st.session_state:
        st.session_state['post_cool_off_success'] = False
    if 'post_cool_off_failed' not in st.session_state:
        st.session_state['post_cool_off_failed'] = False
    if 'cool_off' not in st.session_state:
        st.session_state['cool_off'] = False

def main():
    """ Call main components """
    st.set_page_config(page_title="HITL-AB-BPM", page_icon="resources/images/favicon.png")
    setup()
    uploader.upload_files()
    dashboard.dashboard()
    sidebar.build_bar()


if __name__ == '__main__':
    main()
