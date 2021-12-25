import logging
<<<<<<< HEAD
import pandas as pd
import pycamunda.processinst
from threading import Thread, Event
=======
from threading import Event, Thread
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365
from time import sleep

import pandas as pd
from backend.camunda.client import CamundaClient
<<<<<<< HEAD
from backend.contextual_bandit.contextual_bandit import RlEnv
from activityUtils import instance_terminated, fetch_acticity_duration, cal_time_based_cost

COST={'Schedule':25,
      'Eligibility Test':190,
      'Medical Exam':75,
      'Theory Test':455,
      'Practical Test':1145,
      'Approve':100,
      'Reject':0
}
# logging.basicConfig(level=logging.DEBUG,
#                     format='(%(threadName)-9s) %(message)s', )
logging.basicConfig(level=logging.INFO)
url = 'http://camunda:8080/engine-rest'

class RouterManager:
    process_variant_keys = ['source/backend/resources/bpmn/helicopter_license/helicopter_vA.bpmn',
                            'source/backend/resources/bpmn/helicopter_license/helicopter_vA.bpmn']

    # Configure
    BATCH_SIZE = 200
    NUMBER_OF_VARIANTS = 2
=======
from backend.contextual_bandit.rl_env import RlEnv
from dateutil import parser
from vowpalwabbit import pyvw

logging.basicConfig(level=logging.INFO,
                    format='(INFO) %(message)s', )

class RouterManager:
    # TODO
    process_variant_keys = ['source/backend/resources/bpmn/helicopter_license/helicopter_vA.bpmn',
                            'source/backend/resources/bpmn/helicopter_license/helicopter_vB.bpmn']
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

    # format: {'A': float, 'B': float} (in seconds)
    # TODO Store in db and train on historical data
    mean_duration_results = {}

<<<<<<< HEAD
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # pycharm docker env specified
        # TODO:should be 'http://localhost:8080/engine-rest'
        self.client = CamundaClient('http://camunda:8080/engine-rest')

    def set_events(self, event_rl, event_manager):
        self.event_rl = event_rl
        self.event_manager = event_manager
=======
    # Configure the vowpal wabbit algorithm and methods
    vw = pyvw.vw("--cb_explore_adf -q UA --epsilon 0.2")
    vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")
    #vw = pyvw.vw("--cb 2")
    # Init utility class methods
    # TODO
    client = CamundaClient('http://localhost:8080/engine-rest')
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

    def __init__(self, rl_env,batch_size, number_of_variants):
        self.rl_env = rl_env
        self.batch_size = batch_size
        self.number_of_variants = number_of_variants

<<<<<<< HEAD
    def start_simulation(self ,n):
        self.simulate_batch(n)
        logging.info('BATCH SIMULATED.')
        self.event_rl.set()
        self.event_manager.clear()

        logging.info(f'router is waiting for action')
        self.event_manager.wait(1)
        logging.info(f'router stopped waiting for action')

        logging.info(f'Doing some clean up.')
=======
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
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

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

<<<<<<< HEAD
    def simulate_batch(self, n):
=======
    def simulate_batch(self):
        """[summary]
        """
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365
        # Deploy process variants
        process_ids = self.client.deploy_processes(self.process_variant_keys)

        # Start instances
        for elem in process_ids:
<<<<<<< HEAD
            self.client.start_instances(elem, int(self.BATCH_SIZE / self.NUMBER_OF_VARIANTS))
        logging.info(f'Wait for termination, simulate_batch iteration {n+1}')
        # Wait 2 min to let the instances terminate. Hacky but check not implemented yet.
        # sleep(120)
        fetch_acticity_duration()
        cal_time_based_cost(self.BATCH_SIZE)
        if instance_terminated():
            # Get the data from the Camunda engine
            data = self.client.retrieve_data()
            # Calculate the mean reward for each variant
            self.calculate_mean_variant_duration(data)
=======
            self.client.start_instances(elem, int(self.batch_size / self.number_of_variants))

        logging.info('Waiting for termination.\n')
        
        # Wait 2 min to let the instances terminate. Hacky but check not implemented yet.
        sleep(120)

        # Get the data from the Camunda engine
        data = self.client.retrieve_data()
        logging.debug(data)
        
        # Calculate the mean reward for each variant
        self.calculate_mean_duration(data)
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

            # Update local variable according to the simulation results
            self.rl_env.update_mean_durations(self.mean_duration_results)

<<<<<<< HEAD
            # Clean engine after retrieving the duration
            self.client.clean_process_data()
=======
        # Clean engine after retrieving the duration data.
        self.client.clean_process_data()
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

def main():
    # Adjust accordingly
    logging.getLogger().setLevel(logging.DEBUG)
    
    num_iterations = 1  

    # Init rl_env
    rl_env = RlEnv()

<<<<<<< HEAD
    def thread_rl():
        # Instantiate learner in VW
        vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")
        #vw = pyvw.vw("--cb 2 --epsilon 0.2")

        acc_reward = []
        reward_sum = 0.0

        for i in range(NUM_ITERATIONS):
            logging.info(f'rl_thread iteration: {i}')
            reward = rl_env.init_step(vw)
            reward_sum += reward
            acc_reward.append((-1 * reward_sum / (i+1)))
            print(f'Reward Sum: {reward_sum}, Iteration: {i}')

        print(acc_reward)
        df = pd.DataFrame(acc_reward, columns=['Acc_Reward'])
        df.to_csv(f'source/backend/contextual_bandit/results/testing_refactor.csv')
        print(rl_env.actions_list)

    # Init multithreading events
    event_rl = Event()
    event_manager = Event()

    # Set events according to both env
    router.set_RLEnv(rl_env)
    rl_env.set_manager(router)
    router.set_events(event_rl, event_manager)
    rl_env.set_events(event_rl, event_manager)

    # Init RL thread
    rl_thread = Thread(name='RL Thread', target=thread_rl, args=())

    # Starting thread
    rl_thread.start()

    logging.info('Thread started.')
    router.client.clean_process_data()

    for n in range(NUM_ITERATIONS):
        router.start_simulation(n)

=======
    # Router
    router = RouterManager(rl_env, 200, 2)

    # For debugging, dividing by 0 error solution
    router.client.clean_process_data()

    print(f"Setup completed. Start learning...")
    logging.debug('\n')

    acc_reward = []
    reward_sum = 0.0
    for i in range(num_iterations):
        reward = router.start_simulation()
        reward_sum += reward
        acc_reward.append((-1 * reward_sum / (i + 1)))
        logging.info(f'Iteration {i} -> Reward Sum: {reward_sum} \n')
    
    print(acc_reward)
    print(rl_env.actions_list)
    
    df = pd.DataFrame(acc_reward, columns=['Mean_Reward'])
    df.to_csv('source/backend/contextual_bandit/results/testing_refactor.csv')
    

    print(f"\nFinished learning.\n")
>>>>>>> 0f86805393722d8a658d3e1c01966a7918efb365

    while True:
        sleep(0.5)


if __name__ == "__main__":
    main()
