import logging
from threading import Event, Thread
from time import sleep

import pandas as pd
from backend.camunda.client import CamundaClient
from backend.contextual_bandit.rl_env import RlEnv
from dateutil import parser
from vowpalwabbit import pyvw

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


class RouterManager:
    # TODO
    process_variant_keys = ['../resources/bpmn/helicopter_license/helicopter_vA.bpmn',
                            '../resources/bpmn/helicopter_license/helicopter_vB.bpmn']

    # format: {'A': float, 'B': float} (in seconds)
    # TODO Store in db and train on historical data
    mean_duration_results = {}

    # Configure the vowpal wabbit algorithm and methods
    vw = pyvw.vw("--cb 2")
    # Init utility class methods
    # TODO
    client = CamundaClient('http://localhost:8080/engine-rest')

    def __init__(self, rl_env,batch_size, number_of_variants):
        self.rl_env = rl_env
        self.batch_size = batch_size
        self.number_of_variants = number_of_variants

    def start_simulation(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        self.simulate_batch()
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

        # TODO: Prepare for more than 2 variants
        self.mean_duration_results['A'] = mean_durations[0]
        self.mean_duration_results['B'] = mean_durations[1]

    def simulate_batch(self):
        """[summary]
        """
        # Deploy process variants
        process_ids = self.client.deploy_processes(self.process_variant_keys)

        # Start instances
        for elem in process_ids:
            self.client.start_instances(elem, int(self.batch_size / self.number_of_variants))

        logging.debug('Wait for termination')
        # Wait 2 min to let the instances terminate. Hacky but check not implemented yet.
        sleep(120)

        # Get the data from the Camunda engine
        data = self.client.retrieve_data()
        print(data)
        # Calculate the mean reward for each variant
        self.calculate_mean_duration(data)

        # Update local variable according to the simulation results
        self.rl_env.update_mean_durations(self.mean_duration_results)

        # Clean engine after retrieving the duration
        self.client.clean_process_data()

def main():
    num_iterations = 20

    # Init rl_env
    rl_env = RlEnv()

    # Router
    router = RouterManager(rl_env, 200, 2)

    # For debugging, dividing by 0 error
    router.client.clean_process_data()

    acc_reward = []
    reward_sum = 0.0
    for i in range(num_iterations):
        reward = router.start_simulation()
        reward_sum += reward
        acc_reward.append((-1 * reward_sum / (i + 1)))
        print(f'Reward Sum: {reward_sum}, Iteration: {i}')
    print(acc_reward)
    df = pd.DataFrame(acc_reward, columns=['Mean_Reward'])
    df.to_csv(f'../rl_agent/results/testing_refactor.csv')
    print(rl_env.actions_list)

    while True:
        sleep(0.5)


if __name__ == "__main__":
    main()
