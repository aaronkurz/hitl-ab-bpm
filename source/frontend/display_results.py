# TODO: should be removed to somewhere else
# TODO: hard coded url should be refined
# TODO: should communicate to db?
import streamlit as st
from matplotlib import pyplot as plt
import pandas as pd
import requests
CAMUNDA_ENGINE_URI = f"http://localhost:8080/engine-rest"

def fetch_history_activity_duration():
    history_url = '/history/activity-instance?'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url)
    history_activity_duration_dict = {}
    # st.write('fetch_history_activity_duration')
    # st.write(result.json())
    for instance in result.json():
        history_activity_duration_dict[instance['id']] = [instance['activityName'], instance['durationInMillis']]
    # st.write(history_activity_duration_dict.values())
    return history_activity_duration_dict

def get_activity_count():
    history_url = '/history/activity-instance/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return result['count']

def get_batch_count():
    history_url = '/history/batch/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return result['count']

def get_process_count():
    history_url = '/history/process-instance/count'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url).json()
    return result['count']

def plt_cost():
    df = pd.read_csv('../source/backend/instance_router/time_based_cost.csv')
    plt.plot(df[:])
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('time based cost(cost/milliseconds', fontsize=14)
    plt.legend(df.columns.values.tolist())
    st.pyplot()

def plt_reward():
    df = pd.read_csv('../source/backend/instance_router/reward.csv')
    plt.plot(range(1, 11), df['Mean_Reward'])
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('mean_reward', fontsize=14)
    st.pyplot()

def plt_action_prob(options):
    df = pd.read_csv('../source/backend/instance_router/action_prob.csv')
    plt.plot(df[options])
    plt.legend(df.columns.values.tolist())
    plt.xlabel('num_iterations', fontsize=14)
    plt.ylabel('Action probabilities', fontsize=14)
    st.pyplot()

def clean_up_history():
    history_url = '/history/cleanup'
    query_url = CAMUNDA_ENGINE_URI + history_url
    requests.post(query_url)