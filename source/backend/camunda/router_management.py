import logging
import pandas as pd
from threading import Thread, Event
from time import sleep
from vowpalwabbit import pyvw
from dateutil import parser

from client import CamundaClient
from contextual_bandit import RlEnv

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


class RouterManager:

    process_variant_keys = ['../resources/bpmn/helicopter_license/helicopter_vA.bpmn', '../resources/bpmn/helicopter_license/helicopter_vB.bpmn']

    # Configure
    BATCH_SIZE = 50
    NUMBER_OF_VARIANTS = 2
    # Initially 0.5/0.5. Subject to change.
    #batch_policy_probability_A = 0.5
    #batch_policy_probability_B = 0.5

    # format: {'A': float, 'B': float} (in seconds)
    mean_duration_results = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = CamundaClient('http://localhost:8080/engine-rest')

    def set_events(self, event_rl, event_manager):
        self.event_rl = event_rl
        self.event_manager = event_manager

    def set_RLEnv(self, rl_env):
        self.rl_env = rl_env

    # Just for testing here, delete later
    def on_simulation_termination(self, message):
        self.event_rl.set()
        self.event_manager.clear()

        logging.debug(f'router is waiting for action')
        self.event_manager.wait(1)
        logging.debug(f'router stopped waiting for action')

        logging.debug(f'Doing some clean up {message}')

    def simulate_batch(self):
        # Deploy process variants
        process_ids = self.client.deploy_processes(self.process_variant_keys)

        # Start instances
        for elem in process_ids:
            self.client.start_instances(elem, int(self.BATCH_SIZE/self.NUMBER_OF_VARIANTS))
        logging.debug('Wait for termination')
        # Wait 2 min to let the instances terminate. Hacky but check not implemented yet.
        sleep(120)
        logging.debug('Done waiting!')
        data = self.client.retrieve_data()

        # TODO: ensure order of processes is actually first A then B?
        mean_durations = []
        for process_history in data:
            instances = process_history.get('associated_instances')
            durations = []
            for instance in instances:
                start = parser.parse(instance.get('startTime'))
                end = parser.parse(instance.get('endTime'))
                duration = (end-start).total_seconds()
                durations.append(duration)
            mean_duration = sum(durations) / len(durations)
            mean_durations.append(mean_duration)

        self.mean_duration_results['A'] = mean_durations[0]
        self.mean_duration_results['B'] = mean_durations[1]

        print('Average times versions: ')
        print(str(self.mean_duration_results))





def main():
    # Router
    router = RouterManager()

    # Init rl_env
    rl_env = RlEnv()

    def thread_rl():
        # Instantiate learner in VW
       #vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")

       #num_iterations = 5000
       #ctr = rl_env.run_simulation(vw, num_iterations, rl_env.orgas, rl_env.actions, rl_env.get_reward)

        # plot_ctr(num_iterations, ctr)
        for m in range(6):
            rl_env.step(m)

    def thread_router():
        # Infinite loop in order to leave the client running in the background
        while True:
            sleep(0.5)

    # Init multithreading events
    event_rl = Event()
    event_manager = Event()

    # Set events according to both env
    router.set_RLEnv(rl_env)
    rl_env.set_manager(router)
    router.set_events(event_rl, event_manager)
    rl_env.set_events(event_rl, event_manager)

    # Init both threads
    rl_thread = Thread(name='RL Thread', target=thread_rl, args=())
    #router_thread = Thread(name='Router Thread', target=thread_router, args=())

    # Starting threads
    rl_thread.start()
    #router_thread.start()

    logging.debug('Threads started.')

    #for n in range(6):
    #    router.on_simulation_termination(str(n))
    router.simulate_batch()
    #router.client.clean_process_data()

    while True:
        sleep(0.5)


if __name__ == "__main__":
    main()
