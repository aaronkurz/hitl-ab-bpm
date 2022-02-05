""" Here, the RL agent is implemented """
import csv
import logging
import random

from datetime import datetime
from models import db
from models.process_instance import ProcessInstance
from models.batch_policy_proposal import BatchPolicyProposal, set_bapol_proposal
from sqlalchemy import and_
from vowpalwabbit import pyvw

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Context
orgas = ['gov', 'public']
# Actions
actions = ["A", "B"]
# Model
vw = pyvw.vw("--cb_explore_adf -q UA --quiet --epsilon 0.2")

header_flag = False


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

def get_action(vw, context: str, actions):
    vw_text_example = to_vw_example_format(context, actions)
    pmf = vw.predict(vw_text_example)
    chosen_action_index, prob = sample_custom_pmf(pmf)
    return actions[chosen_action_index], prob

def get_action_prob_per_context_dict(vw, orgas, actions):
    # Multiple contexts, loop over list of contexts
    dict_list = []
    for elem in orgas:
        tmp = {'orga': elem}
        vw_text_example = to_vw_example_format(tmp, actions)
        pmf = vw.predict(vw_text_example)
        dict = {}
        dict.update(tmp) 
        count = 0
        for action in actions:
            dict[action] = pmf[count]
            count = count + 1
        dict_list.append(dict)
    return dict_list  

def write_stats_to_csv(dict):
    prob_dict = calculate_counterprobability(dict['action'], dict['prob'])
    header = ['context', 'action', 'reward', 'prob_a', 'prob_b']
    data = [dict['context'],dict['action'],dict['reward'],prob_dict['prob_a'],prob_dict['prob_b']]
    with open('action_prob.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not header_flag:
            writer.writerow(header)
        writer.writerow(data)

def calculate_counterprobability(action, prob):
    prob_dict = {}
    counter_prob = round(1-prob, 2)
    prob = round(prob, 2)
    if action == 'A':
        prob_dict['prob_a'] = prob
        prob_dict['prob_b'] = counter_prob
    else: 
        prob_dict['prob_a'] = counter_prob
        prob_dict['prob_b'] = prob
    return prob_dict


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
    #current_action_choosen,current_context,reward,action_prob_a_gov,action_prob_b_gov,action_prob_a_public,action_prob_b_public
    # Set random seed
    # random.seed(1)
    # 1. In each simulation choose a user
    organisation = choose_orga(orgas)
    # 2. Pass context to vw to get an action
    context = {'orga': organisation}
    action, prob = get_action(vw, context, actions)
    logging.info(f'Action: {action}, Prob: {prob}, Context: {context}')
    # 3. Get reward of the action we chose
    reward = reward_function(context, action, duration)
    logging.info(f'Reward: {reward}')
    dict = {'context': organisation, 'action': action, 'prob': prob, 'reward': reward}
    write_stats_to_csv(dict)
    header_flag = True
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
    train the agent and update the database with the reward.
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
    agent_stats_list = get_action_prob_per_context_dict(vw, orgas, actions)
    set_bapol_proposal(process_id, ["gov", "public"], [round(agent_stats_list[0]['A'],2), round(agent_stats_list[-1]['A'],2)], 
                                                        [round(agent_stats_list[0]['B'],2), round(agent_stats_list[-1]['B'],2)])