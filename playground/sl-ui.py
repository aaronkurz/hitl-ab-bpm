import streamlit as st


def upload_files():
    with st.form(key="My Form"):
        f_a = st.file_uploader("Upload process variant A")
        f_b = st.file_uploader("Upload process variant B")
        if st.form_submit_button("Submit"):
            if f_a is not None and f_b is not None:
                st.write("Files uploaded, continue below.")
            else:
                st.write("Both variant a and variant b have to be uploaded at once.")


def set_bapol():
    pass


def display_results():
    st.button("Refresh")


def main():
    st.set_page_config(page_title="AB-BPM", page_icon="🔁")
    st.title("AB-BPM Dashboard 🎮")
    st.header("⬆️ Step 1: Upload Process Versions")
    upload_files()
    st.header("📐 Step 2: Set Batch Policy")
    set_bapol()
    st.header("⌚️ Step 3: Wait For Results")
    display_results()


if __name__ == '__main__':
    main()
