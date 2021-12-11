import logging

from threading import Thread, Event
from time import sleep
from vowpalwabbit import pyvw

from backend.camunda.contextual_bandit import RlEnv

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


class RouterManager:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_events(self, event_rl, event_manager):
        self.event_rl = event_rl
        self.event_manager = event_manager

    def set_RLEnv(self, rl_env):
        self.rl_env = rl_env

    def on_simulation_termination(self, message):
        self.event_rl.set()
        self.event_manager.clear()

        logging.debug(f'router is waiting for action')
        self.event_manager.wait(1)
        logging.debug(f'router stopped waiting for action')

        logging.debug(f'Doing something very important {message}')


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
    router_thread = Thread(name='Router Thread', target=thread_router, args=())

    # Starting threads
    rl_thread.start()
    router_thread.start()

    logging.debug('Threads started.')

    for n in range(6):
        router.on_simulation_termination(str(n))

    logging.debug('Main terminated.')


if __name__ == "__main__":
    main()
