""" Retrieve events from the instance queue and evaluate or reschedule

Takes the next instance in the async_instance_queue and checks whether it is done.
If so, it sends it to the rewards module for evaluation. If not, it is rescheduled.
"""
