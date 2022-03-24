""" Sidebar of app, displaying info, logo, links """
import streamlit as st

def build_bar():
    """ Sidebar of app, displaying info, logo, links """
    st.sidebar.image("resources/images/favicon.png")
    st.sidebar.title("HITL-AB-BPM")
    st.sidebar.write("### Continuous, rapid and controllable process improvement")
    st.sidebar.write("""
    - Continuous: AB Testing methodology
    - Rapid: Supported by reinforcement learning
    - Controllable: Expert oversight (Human-in-the-Loop)
    
    For reporting bugs, feedback and more info, please refer
     to the [Github repository](https://github.com/aaronkurz/hitl-ab-bpm).
    """)
