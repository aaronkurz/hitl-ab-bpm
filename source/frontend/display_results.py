import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt

CAMUNDA_ENGINE_URI = f"http://localhost:8080/engine-rest"


def plt_cost():
    df = pd.read_csv('../source/backend/instance_router/results/time_based_cost.csv')
    plt.plot(df[:])
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('time based cost(cost/milliseconds', fontsize=14)
    plt.legend(df.columns.values.tolist())
    st.pyplot()


def plt_reward():
    df = pd.read_csv('../source/backend/instance_router/results/reward.csv')
    plt.plot(range(1, 11), df['Mean_Reward'])
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('mean_reward', fontsize=14)
    st.pyplot()


def plt_action_prob(options):
    df = pd.read_csv('../source/backend/instance_router/results/action_prob.csv')
    plt.plot(df[options])
    plt.legend(df.columns.values.tolist())
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('Action probabilities', fontsize=14)
    st.pyplot()
