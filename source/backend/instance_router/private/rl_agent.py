""" Here, the RL agent is implemented """
import csv
from datetime import datetime
import logging
import random

from models import db
from models.process_instance import ProcessInstance
from models.batch_policy_proposal import BatchPolicyProposal, set_bapol_proposal
from sqlalchemy import and_
from vowpalwabbit import pyvw

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Context
orgas = ['public', 'gov']
# Actions
actions = ["A", "B"]
# Store every action taken
actions_list = []
# Model
vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")

def get_reward(context: str, action: str, duration: float):
    """Returns a reward ∈ [0;1] given a list of contexts and an action.
    Args:
        context ([type]): [description]
        action ([type]): [description]
    Returns:
        [type]: [description]
    """
    # TODO
    if context == 'public' and action == 'A':
        return duration
    elif context == 'public' and action == 'B':
        return duration
    elif context == 'gov' and action == 'A':
        return duration
    else:
        return duration

# This function modifies (context, action, cost, probability) to VW friendly format
def to_vw_example_format(context, actions, cb_label=None):
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

def sample_custom_pmf(pmf):
    total = sum(pmf)
    scale = 1 / total
    pmf = [x * scale for x in pmf]
    draw = random.random()
    sum_prob = 0.0
    for index, prob in enumerate(pmf):
        sum_prob += prob
        if sum_prob > draw:
            return index, prob

def get_action(vw, context, actions):
    vw_text_example = to_vw_example_format(context, actions)
    pmf = vw.predict(vw_text_example)
    chosen_action_index, prob = sample_custom_pmf(pmf)
    return actions[chosen_action_index], prob

def get_action_prob_dict(vw, context, actions):
    vw_text_example = to_vw_example_format(context, actions)
    pmf = vw.predict(vw_text_example)
    dict = {}
    count = 0
    for elem in actions:
        dict[elem] = pmf[count]
        count = count + 1
    return dict

def action_prob_header2csv():
    print(actions)
    header = actions
    with open('action_prob.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

def action_prob2csv(ap_dict: dict):
    datas = []
    datas.append(ap_dict)
    header = ap_dict.keys()
    with open('action_prob.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writerows(datas)

def choose_orga(orgas: list):
    """
    Choose an organisation randomly from organisations list
    :param orgas:
    :return:
    """
    return random.choice(orgas)

def run_simulation(vw, orgas: list, actions: list, reward_function: get_reward, duration: float, do_learn: bool = True):
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
    organisation = choose_orga(orgas)
    # 2. Pass context to vw to get an action
    context = {'orga': organisation}
    action, prob = get_action(vw, context, actions)
    dic = get_action_prob_dict(vw, context, actions)
    action_prob2csv(dic)
    logging.info(f'Action: {action}, Prob: {prob}, Context: {context}')
    actions_list.append(action)
    # 3. Get reward of the action we chose
    reward = reward_function(context, action, duration)
    logging.info(f'Reward: {reward}')
    if do_learn:
        # 4. Inform VW of what happened so we can learn from it
        vw_format = vw.parse(to_vw_example_format(context, actions, (action, reward, prob)),
                             pyvw.vw.lContextualBandit)
        # 5. Learn
        vw.learn(vw_format)
        # 6. Let VW know you're done with these objects
        vw.finish_example(vw_format)
    # We negate this so that on the plot instead of minimizing cost, we are maximizing reward
    return reward


def calculate_duration(start_time: datetime, end_time: datetime):
    """
    Calculate the duration of a process instance given start and end timestamp
    """
    return (end_time - start_time).total_seconds()


def learn_and_set_new_batch_policy_proposal(process_id: int):
    """
    Query process instances which still have to be evaluated. With the calculated duration,
    train the agent and update the database with the newly calculated reward. 
    Finally, update the batch policy proposal.
    :param process_id:
    :return: new batch policy proposal
    """
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time != None,
                                                           ProcessInstance.do_evaluate == True,
                                                           ProcessInstance.reward == None))

    for instance in relevant_instances:
        duration = calculate_duration(instance.instantiation_time, instance.finished_time)
        reward = run_simulation(vw, orgas, actions, get_reward, duration, do_learn=True)
        instance.reward = reward
    db.session.commit()
    
    #                                       A               B
    set_bapol_proposal(process_id, orgas, [0.3, 0.5], [0.7, 0.5])
