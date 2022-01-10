import logging
import time
from time import sleep

import pandas as pd
from dateutil import parser
from vowpalwabbit import pyvw

from instance_router.private.to_be_migrated.activity_utils import (cal_time_based_cost, instance_terminated, get_format_timestamp,
                                                                   sumup_history_activity_duration)
from camunda.client import CamundaClient
from contextual_bandit.rl_env import RlEnv

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


class RouterManager:
    # TODO Absolute paths? Source folder sbe_prototyping
    process_variant_keys = ['../../test_resources/bpmn/helicopter_license_fast/helicopter_fast_vA.bpmn',
                            '../../test_resources/bpmn/helicopter_license_fast/helicopter_fast_vB.bpmn']

    # format: {'A': float, 'B': float} (in seconds)
    # TODO Store in db and train on historical data
    mean_duration_results = {}

    # Configure the vowpal wabbit algorithm and methods
    # TODO delete --quiet for additional information 
    vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")

    # Init utility class method
    client = CamundaClient()

    def __init__(self, rl_env, batch_size, number_of_variants):
        self.rl_env = rl_env
        self.batch_size = batch_size
        self.number_of_variants = number_of_variants

    def start_simulation(self, iteration_n):
        """[summary]

        Returns:
            [type]: [description]
        """
        # Track the time the simulation and calculations take
        start_time = time.perf_counter()
        self.simulate_batch(iteration_n)
        end_time = time.perf_counter()
        logging.info(f'Simulation time: {end_time - start_time} Seconds')

        # Train the agent and retrieve the reward to log
        reward = self.rl_env.init_step(self.vw)

        return reward

    def calculate_mean_duration(self, data):
        """[summary]

        Args:
            data ([type]): [description]
        """
        # TODO: ensure order of processes is actually first A then B?
        mean_durations = []
        for process_history in data:
            instances = process_history.get('associated_instances')
            durations = []
            for instance in instances:
                start = parser.parse(instance.get('startTime'))
                end = parser.parse(instance.get('endTime'))
                duration = (end - start).total_seconds()
                durations.append(duration)
            mean_duration = sum(durations) / len(durations)
            mean_durations.append(mean_duration)

        # TODO: Refactor to handle more then 2 variants
        self.mean_duration_results['A'] = mean_durations[0]
        self.mean_duration_results['B'] = mean_durations[1]

    def simulate_batch(self, iteration_n):
        batch_start_timestamp = get_format_timestamp()

        """[summary]
        """
        # Deploy process variants
        process_ids = self.client.deploy_processes(self.process_variant_keys)

        # Start instances
        for elem in process_ids:
            self.client.start_instances(elem, int(self.batch_size / self.number_of_variants))

        logging.info(f'Wait for termination, simulate_batch iteration {iteration_n}')

        # Wait 2 min to let the instances terminate. Hacky but check not implemented yet.
        # sleep(120)

        # deprecated
        # time_elapsed = fetch_activity_duration()
        # cal_time_based_cost(self.batch_size, time_elapsed)

        if instance_terminated():
            # Get the data from the Camunda engine
            data = self.client.retrieve_data()
            # Calculate the mean reward for each variant
            self.calculate_mean_duration(data)

            # Update local variable according to the simulation results
            self.rl_env.update_mean_durations(self.mean_duration_results)

            # fetch_history_activity_duration(batch_start_timestamp)
            time_elapsed = sumup_history_activity_duration(batch_start_timestamp)
            cal_time_based_cost(self.batch_size, time_elapsed)

            # Clean engine after retrieving the duration
            self.client.clean_process_data()


def main():
    # Adjust accordingly
    #logging.getLogger().setLevel(logging.INFO)

    num_iterations = 1

    # Init rl_env
    rl_env = RlEnv()

    # Router
    router = RouterManager(rl_env, 50, 2)

    # For debugging, clean camund engine before deploying anything
    router.client.clean_process_data()

    print(f"Setup completed. Start learning...")
    logging.debug('\n')

    acc_reward = []
    reward_sum = 0.0
    for i in range(num_iterations):
        reward = router.start_simulation(i)
        reward_sum += reward
        acc_reward.append((-1 * reward_sum / (i + 1)))
        logging.info(f'Iteration {i} -> Reward Sum: {reward_sum} \n')

    print(acc_reward)
    print(rl_env.actions_list)

    df = pd.DataFrame(acc_reward, columns=['Mean_Reward'])
    df.to_csv('contextual_bandit/results/testing_reward.csv')

    print(f"\nFinished learning.\n")

    while True:
        sleep(0.5)


if __name__ == "__main__":
    main()
