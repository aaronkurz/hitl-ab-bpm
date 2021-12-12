from threading import Thread, Event
from time import sleep
import numpy
import pandas
import logging
import random

from vowpalwabbit import pyvw

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


class RlEnv:
    USER_LIKED_ARTICLE = 1.0
    USER_DISLIKED_ARTICLE = 0.0

    orgas = ['gov', 'public']
    # cost_profiles = ['relevant', 'irrelevant']
    actions = ["A", "B"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_events(self, event_rl, event_manager):
        self.event_rl = event_rl
        self.event_manager = event_manager

    def set_manager(self, manager):
        self.manager = manager

    # Just for testing here, delete later
    def step(self, n):
        self.event_manager.set()
        self.event_rl.clear()
        logging.debug("Rl_env waiting for simulation info")
        self.event_rl.wait()
        logging.debug(f'Rl_env stopped waiting')
        logging.debug(f'Reward {random.randint(0, 10)}')
        logging.debug(f'step done {n}')

    def get_reward(self, context, action):
        if action == 'A':
            return self.USER_LIKED_ARTICLE
        else:
            return self.USER_DISLIKED_ARTICLE

    # This function modifies (context, action, cost, probability) to VW friendly format
    def to_vw_example_format(self, context, actions, cb_label=None):
        if cb_label is not None:
            chosen_action, cost, prob = cb_label
        example_string = ""
        # example_string += "shared |Orga orga={} Cost_profile={}\n".format(context["orga"], context["cost_profile"])
        example_string += "shared |Orga orga={}\n".format(context["orga"])
        for action in actions:
            if cb_label is not None and action == chosen_action:
                example_string += "0:{}:{} ".format(cost, prob)
            example_string += "|Action variant={} \n".format(action)
        # Strip the last newline
        return example_string[:-1]

    def sample_custom_pmf(self, pmf):
        total = sum(pmf)
        scale = 1 / total
        pmf = [x * scale for x in pmf]
        draw = random.random()
        sum_prob = 0.0
        for index, prob in enumerate(pmf):
            sum_prob += prob
            if sum_prob > draw:
                return index, prob

    def get_action(self, vw, context, actions):
        vw_text_example = self.to_vw_example_format(context, actions)
        pmf = vw.predict(vw_text_example)
        chosen_action_index, prob = self.sample_custom_pmf(pmf)
        return actions[chosen_action_index], prob

    def choose_orga(self, orgas):
        return random.choice(orgas)

    def generate_input_data(self):
        # start simulation
        return

    def run_simulation(self, vw, num_iterations, orgas, actions, reward_function, do_learn=True):
        reward_sum = 0.
        acc_reward = []

        for i in range(1, num_iterations + 1):
            # 1. In each simulation choose a user
            organisation = self.choose_orga(orgas)
            # 2. Choose time of day for a given user
            # Do not use for now
            # time_of_day = choose_time_of_day(times_of_day)

            # 3. Pass context to vw to get an action
            # context = {'orga': user, 'cost_profile': time_of_day}
            context = {'orga': organisation}
            action, prob = self.get_action(vw, context, actions)

            # 4. Get reward of the action we chose
            reward = reward_function(context, action)
            reward_sum += reward

            if do_learn:
                # 5. Inform VW of what happened so we can learn from it
                vw_format = vw.parse(self.to_vw_example_format(context, actions, (action, reward, prob)),
                                     pyvw.vw.lContextualBandit)
                # 6. Learn
                vw.learn(vw_format)
                # 7. Let VW know you're done with these objects
                vw.finish_example(vw_format)

            # We negate this so that on the plot instead of minimizing cost, we are maximizing reward
            acc_reward.append(reward_sum / i)

        return acc_reward

    # def plot_ctr(num_iterations, acc_reward):
    #    plt.plot(range(1,num_iterations+1), ctr)
    #    plt.xlabel('num_iterations', fontsize=14)
    #    plt.ylabel('ctr', fontsize=14)
    #    plt.ylim([0,1])
