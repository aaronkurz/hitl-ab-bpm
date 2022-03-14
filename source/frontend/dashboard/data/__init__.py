""" User interface parts displaying data about experiment """
from resources import user_assistance, general_texts
import streamlit as st
import requests
from matplotlib import pyplot as plt
from pandas import DataFrame
from config import BACKEND_URI
import utils


def plot_instances():
    """ Plot an overview of instantiation requests coming on over time and how they have been routed (A/B) """
    params = {"process-id": utils.get_currently_active_process_id()}
    response = requests.get(BACKEND_URI + "instance-router/aggregate-data/client-requests", params=params)
    if response.status_code != requests.codes.ok:  # pylint: disable=no-member
        st.exception(general_texts.CANT_FETCH)
    response_json = response.json()
    if response_json.get('noTotalRequests') > 0:
        plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsA'), label='Version A')
        plt.plot(range(response_json.get('noTotalRequests')), response_json.get('requestsB'), label='Version B')
        plt.legend(loc='upper left')
        plt.xlabel('Total requests')
        plt.ylabel('Requests per version')
        plt.xlim(left=0)
        plt.ylim(bottom=0)
        st.pyplot(fig=plt.gcf())
    else:
        st.write("No instantiations yet. Plot of instantiation decisions will be shown here.")


def data():
    """ Data-area, calling methods to create UI for sub-parts (depending on choice in drop-down) """
    st.write("### Data")
    data_view = st.selectbox("Choose Data View",
                 ("Experiment Metadata", "Aggregate Data", "Detailed Data"))
    if data_view == "Experiment Metadata":
        experiment_metadata()
    elif data_view == "Aggregate Data":
        aggregate_data()
    elif data_view == "Detailed Data":
        detailed_data()


def experiment_metadata():
    """ Area containing metadata about experiment """
    st.write("#### Experiment Metadata")
    with st.expander("What is shown here?", expanded=False):
        st.write(user_assistance.EXPERIMENT_METADATA)
    if st.button("Refresh", key="refresh_exp_meta"):
        response_meta = requests.get(BACKEND_URI + "process/active/meta")
        if response_meta.status_code == requests.codes.ok:  # pylint: disable=no-member
            process_meta_json = response_meta.json()
            col1, col2 = st.columns(2)
            with col1:
                st.write("*Process name*: ", process_meta_json.get('name'))
                st.write("*Start of experiment*: ", process_meta_json.get('datetime_added'))
                st.write("*State*: ", process_meta_json.get('experiment_state'))
                st.write("*Customer categories*: ", process_meta_json.get('customer_categories'))
            with col2:
                st.write("*Default/old version*: ", process_meta_json.get('default_version'))
                st.write("*Winning versions*: ", process_meta_json.get('winning_versions'))
                st.write("*End of experiment*: ", process_meta_json.get('datetime_decided'))
        elif response_meta.status_code == 400:
            st.write("No running experiment yet. Upload proces versions above to start an experiment.")


def detailed_data():
    """ Display detailed data for a certain batch of choice and allow for download of data as CSV """
    st.write('#### Detailed Data')
    with st.expander('What is shown here?', expanded=False):
        st.write(user_assistance.DETAILED_DATA)
    if st.button("Refresh", key="10") or st.session_state['data_detailed_open'] is True:
        st.session_state['data_detailed_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response_bapol_count = requests.get(BACKEND_URI + "batch-policy/count", params=params)
        if response_bapol_count.status_code != requests.codes.ok:  # pylint: disable=no-member
            st.exception(general_texts.CANT_FETCH)
        else:
            batch_choice = st.selectbox(
                'Which batch would you like to see details about?',
                tuple(range(1, response_bapol_count.json().get('batchPolicyCount') + 1)),
                help=user_assistance.BATCH_NUMBER_CHOICE)

            if batch_choice is not None:
                params = {
                    "process-id": utils.get_currently_active_process_id(),
                    "batch-number": batch_choice
                }
                response_batch_instances = requests.get(BACKEND_URI + "instance-router/detailed-data/batch",
                                                        params=params)
                if response_batch_instances.status_code != requests.codes.ok:  # pylint: disable=no-member
                    st.exception(general_texts.CANT_FETCH)
                else:
                    batch_instances_df = DataFrame(
                        columns=["Version", "Customer Category", "Start Time", "End Time", "Reward"])
                    for i in range(len(response_batch_instances.json().get("instances"))):
                        batch_instances_df.loc[i] = [
                            response_batch_instances.json().get("instances")[i].get("decision"),
                            response_batch_instances.json().get("instances")[i].get("customerCategory"),
                            response_batch_instances.json().get("instances")[i].get("startTime"),
                            response_batch_instances.json().get("instances")[i].get("endTime"),
                            response_batch_instances.json().get("instances")[i].get("reward"),
                            ]
                    st.write("Batch Number: ", response_batch_instances.json().get("batchNumber"))
                    st.table(batch_instances_df)

                    batch_instanes_csv = batch_instances_df.to_csv().encode('utf-8')

                    st.download_button(
                        "Download as CSV",
                        batch_instanes_csv,
                        "batch_" + str(batch_choice) + "_instances.csv",
                        "text/csv",
                        key='download-batch-instances-csv'
                    )


def aggregate_data():
    """ Display aggregate data about current experiment """
    st.write('#### Aggregate Data')
    with st.expander('What is shown here?', expanded=False):
        st.write(user_assistance.AGGREGATE_DATA)
    if st.button("Refresh") or st.session_state['data_open'] is True:
        st.session_state['data_open'] = True
        params = {"process-id": utils.get_currently_active_process_id()}

        response = requests.get(
            BACKEND_URI + "instance-router/aggregate-data", params=params
        )
        if response.status_code != requests.codes.ok:  # pylint: disable=no-member
            st.exception(general_texts.CANT_FETCH)
        else:
            aggregate_data_df = DataFrame(
                columns=['Version', 'Number Started', 'Number Finished', 'Mean Duration (sec)', 'Mean Reward'])
            versions = ['a', 'b']
            for i in range(2):
                aggregate_data_df.loc[i] = [versions[i],
                                            response.json().get(versions[i]).get("numberStarted"),
                                            response.json().get(versions[i]).get("numberFinished"),
                                            None if response.json().get(versions[i]).get("averageDurationSec") is None
                                            else round(response.json().get(versions[i]).get("averageDurationSec"), 2),
                                            None if response.json().get(versions[i]).get("averageReward") is None
                                            else round(response.json().get(versions[i]).get("averageReward"), 2), ]
            # HIDE ROW INDICES:
            # CSS to inject contained in a string
            hide_table_row_index = """
                            <style>
                            tbody th {display:none}
                            .blank {display:none}
                            </style>
                            """
            # Inject CSS with Markdown
            st.markdown(hide_table_row_index, unsafe_allow_html=True)
            st.table(aggregate_data_df.astype(str))
        plot_instances()
