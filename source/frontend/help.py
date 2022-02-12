AGGREGATE_DATA = """
Here you can see an overview and aggregated data over all batches. Please note that only \
the data from instances that are part of experimental batches is considered here, not data from instances that \
have been started in between batches.
"""

CUSTOMER_CATEGORIES_INPUT = "e.g. public-gov"

DEFAULT_VERSION_INPUT = "The version that is used in between batches"

MIN_DURATION_INPUT = """
Please enter the minimum and maximum duration of the past process data (old version) here. This data \
is used to calculate the reward of new instances more reliably.
"""

DETAILED_DATA = """
Here you can see the details of each and every instance that has been part of an experimental batch.
"""

BATCH_NUMBER_CHOICE = "Number 1 means the first batch set for a process, number 2 means the second, and so on"

BATCH_SIZE_HELP = """
Here you can choose how many of the next incoming process instantiation requests will be part of this experimental \
batch.
"""

HISTORY_UPLOAD_DEFAULT = """
Should be a .json file with this content format:
{
  "interarrivalTime": 0.98,
  "durations": [
    0.198,
    0.041,
    0.124,
    0.04,
    0.099,
    0.144
    ]
}
"""

DASHBOARD_HELP = "This is where the human process expert can control the experiment."

DEV_MODE_HELP = """
If you are just using the app for development purposes or to try it out \
you can simulate process instantiation requests instead of having real requests from customers/clients. \
An additional client simulator area will pop up in the dashboard if you activate dev mode.
"""
