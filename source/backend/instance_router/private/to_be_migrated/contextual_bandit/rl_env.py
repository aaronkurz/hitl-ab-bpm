import csv
import logging
import random

from vowpalwabbit import pyvw

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


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

    def update_mean_durations(self, mean_duration):
        """[summary]

        Args:
            mean_duration ([type]): [description]
        """
        self.mean_durations = mean_duration

    def get_reward(self, context, action):
        """Returns a reward ∈ [0;1] given a list of contexts and an action.

        Args:
            context ([type]): [description]
            action ([type]): [description]

        Returns:
            [type]: [description]
        """
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
        """[summary]

        Args:
            context ([type]): [description]
            actions ([type]): [description]
            cb_label ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
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

    def get_action_prob_dict(self, vw, context, actions):
        vw_text_example = self.to_vw_example_format(context, actions)
        pmf = vw.predict(vw_text_example)
        dict = {}
        count = 0
        for elem in actions:
            dict[elem] = pmf[count]
            count = count + 1
        return dict

    def action_prob_header2csv(self):
        print(self.actions)
        header = self.actions
        with open('action_prob.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

    def action_prob2csv(self, ap_dict):
        datas = []
        datas.append(ap_dict)
        header = ap_dict.keys()
        with open('action_prob.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writerows(datas)

    def choose_orga(self, orgas):
        """
        Choose an organisation randomly from organisations list
        :param orgas:
        :return:
        """
        return random.choice(orgas)

    def init_step(self, vw):
        """

        :param vw:
        :return:
        """
        reward = self.run_simulation(vw, self.orgas, self.actions, self.get_reward, do_learn=True)

        return reward

    def run_simulation(self, vw, orgas, actions, reward_function: get_reward, do_learn: bool = True):
        """[summary]

        Args:
            vw (contextual_bandit): contextual bandit model to be trained
            orgas (List[String]): List of organsiation the agent can choose from
            actions (List[String]): List of actions the agent can choose from 
            reward_function (int): [description]
            do_learn (bool, optional): [description]. Defaults to True.

        Returns:
            [type]: [description]
        """
        reward_sum = 0.
        acc_reward = []

        # Set random seed
        # random.seed(1)
        # 1. In each simulation choose a user
        organisation = self.choose_orga(orgas)
        # 2. Pass context to vw to get an action
        context = {'orga': organisation}
        action, prob = self.get_action(vw, context, actions)
        dic = self.get_action_prob_dict(vw, context, actions)
        self.action_prob2csv(dic)
        logging.info(f'Action: {action}, Prob: {prob}, Context: {context}')
        self.actions_list.append(action)
        # 3. Get reward of the action we chose
        reward = reward_function(context, action)
        logging.info(f'Reward: {reward}')

        if do_learn:
            # 4. Inform VW of what happened so we can learn from it
            vw_format = vw.parse(self.to_vw_example_format(context, actions, (action, reward, prob)),
                                 pyvw.vw.lContextualBandit)
            # 5. Learn
            vw.learn(vw_format)
            # 6. Let VW know you're done with these objects
            vw.finish_example(vw_format)
        # We negate this so that on the plot instead of minimizing cost, we are maximizing reward
        return reward
