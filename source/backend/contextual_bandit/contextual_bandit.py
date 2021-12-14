import logging
import random
from matplotlib import pyplot as plt

from vowpalwabbit import pyvw

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


class RlEnv:
    # Context
    orgas = ['gov', 'public']
    # Actions
    actions = ["A", "B"]
    # Store every action taken
    actions_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mean_durations = {}

    def set_events(self, event_rl, event_manager):
        self.event_rl = event_rl
        self.event_manager = event_manager

    def set_manager(self, manager):
        self.manager = manager

    def update_mean_durations(self, mean_duration):
        self.mean_durations = mean_duration

    def get_reward(self, context, action):
        if context == 'public' and action == 'A':
            return -(self.mean_durations['A'])
        elif context == 'public' and action == 'B':
            return -(self.mean_durations['B'])
        elif context == 'gov' and action == 'A':
            return -(self.mean_durations['A'])
        else:
            return -(self.mean_durations['B'])

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

    def init_step(self, vw):
        self.event_manager.set()
        self.event_rl.clear()
        logging.debug("Rl_env waiting for simulation info")
        self.event_rl.wait()
        logging.debug(f'Rl_env stopped waiting')
        reward = self.run_simulation(vw, self.orgas, self.actions, self.get_reward, do_learn=True)
        return reward

    def run_simulation(self, vw, orgas, actions, reward_function, do_learn=True):
        reward_sum = 0.
        acc_reward = []

        # Set random seed
        #random.seed(1)
        # 1. In each simulation choose a user
        organisation = self.choose_orga(orgas)
        # 2. Pass context to vw to get an action
        context = {'orga': organisation}
        action, prob = self.get_action(vw, context, actions)
        print(f'Action: {action}, Prob: {prob}, Context: {context}')
        self.actions_list.append(action)
        # 3. Get reward of the action we chose
        reward = reward_function(context, action)
        print(f'Reward: {reward}')

        if do_learn:
            # 4. Inform VW of what happened so we can learn from it
            vw_format = vw.parse(self.to_vw_example_format(context, actions, (action, reward, prob)), pyvw.vw.lContextualBandit)
            # 5. Learn
            vw.learn(vw_format)
            # 6. Let VW know you're done with these objects
            vw.finish_example(vw_format)
        # We negate this so that on the plot instead of minimizing cost, we are maximizing reward
        return reward

    # Deprecated
    def plot_cum_mean_reward(self, num_iterations, data_frame, counter):
        plt.plot(range(1, num_iterations + 1), data_frame['Acc_Reward'])
        plt.xlabel('num_iterations', fontsize=14)
        plt.ylabel('ctr', fontsize=14)
        plt.savefig(f'../source/backend/rl_agent/results/reward_{counter}.pdf')
