""" Here, the RL agent is implemented """
import logging
import random
import vowpalwabbit
import pandas as pd
import os

from datetime import datetime
from models import db
from models.process_instance import ProcessInstance
from models.process import get_process_metadata
from models.batch_policy_proposal import set_bapol_proposal
from sqlalchemy import and_

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Actions
actions = ["A", "B"]
# Store stats of all iteration within a batch
learning_hist = []
# Pytest boolean flag
debugging = False


def get_reward(duration: float):
    """
        Return the reward for the action taken based on the duration of the process instance.
    params:
        duration (float): Duration of the process instance

    returns:  1 - duration. If the duration >= 1, 0 as the reward is returned
    """
    # TODO proper reward function
    neg_duration = 1.0 - duration
    if neg_duration <= 0:
        neg_duration = 0.0
    return neg_duration


def to_vw_example_format(context, actions, cb_label=None):
    """
    Modify (context, action, cost, probability) to a VW friendly format.

    params:
        context: The context of the cb
        actions: List of all possible actions
    
    returns: VW friendly String

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
    """
    Helper method

    params:
        pmf ([type]): [description]

    returns:
    """
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
    """
    Not used right now

    """
    vw_text_example = to_vw_example_format(context, actions)
    pmf = vw.predict(vw_text_example)
    chosen_action_index, prob = sample_custom_pmf(pmf)
    return actions[chosen_action_index], prob


def get_action_prob_per_context_dict(vw, orgas, actions):
    """
    Retrieve the probability for each action given any context.

    params:
        vw: The cb model
        orgas: The context
        actions: All possible actions
    
    returns:
        Dictionary containing the probabilities of each action under given context 

    """
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


def calculate_counterprobability(action, prob):
    """
    Calculate the counterprobability of a given action under a given context. Used in write_stats_to_csv.
    params:
        action (str): Action used in the current iteration
        prob (float): Corresponding probability 

    returns: Dictionary containing the probabilities
    """
    prob_dict = {}
    counter_prob = round(1.0-prob, 2)
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
    :param orgas
    :return Random chosen orga
    """
    return random.choice(orgas)


def calculate_duration(start_time: datetime, end_time: datetime):
    """
    Calculate the duration of a process instance given start and end timestamp
    :param start_time, end_time
    """
    return (end_time - start_time).total_seconds()


def load_model(process_id: int):
    """
    Load the cb model if it already exists. If not, instantiate the new model

    params:
        process_id (int): Id of the parent process.

    returns: vw: The cb model
    """
    model_path = f'instance_router/private/cb_models/cb_model_process_id={process_id}'
    if os.path.exists(model_path):
        vw = vowpalwabbit.Workspace(f'--cb_explore_adf -q UA -i {model_path} --epsilon 0.2', quiet=True)
    else: 
        vw = vowpalwabbit.Workspace('--cb_explore_adf -q UA --epsilon 0.2', quiet=True)
    return vw


def write_to_csv(process_id: int):
    """
    Write the (context, action, prob_a, prob_b, reward) of each iteration to a csv file.
    All iterations that belong to the same process, are written to the same csv file.

    params:
        process_id (int): Id of the parent process.
    """
    path = f'instance_router/private/results/learning_history_{process_id}.csv'
    path_without_csv = 'instance_router/private/results/'
    if not os.path.exists(path_without_csv):
        os.makedirs(path_without_csv)
    df = pd.DataFrame.from_dict(learning_hist, orient='columns')
    # If csv files already exists, append data.
    if os.path.exists(path):
        df.to_csv(path, mode='a', index=False, header=False)
    else:
        df.to_csv(path, index=False)


def run_simulation(vw, orgas: list, actions: list, reward_function: get_reward, duration: float, hist_action: str, customer_category: str):
    """
        
    param:
        vw (contextual_bandit): contextual bandit model to be trained
        orgas (List[String]): List of organsiation the agent can choose from
        actions (List[String]): List of actions the agent can choose from
        reward_function (int): Function to evaluate the action
        duration (float): Duration of a process instance
        hist_action (st): Action retrieved from the database
        customer_category (str): Context retrieved from the database
        do_learn (bool, optional): Signal to learn on iteration. Defaults to True.
    return: reward
    """
    # Set random seed
    # random.seed(1)
    #organisation = choose_orga(orgas)
    # 1. Set the context 
    context = {'orga': customer_category}
    # 2. Set the chosen action
    action = hist_action.value.upper()
    # Retrieve probabilty for the given context and action
    agent_stats_list = get_action_prob_per_context_dict(vw, orgas, actions)
    for elem in agent_stats_list:
        if elem['orga'] == customer_category:
            prob = elem[action]
    logging.info(f'Action: {action}, Prob: {prob}, Context: {context}')
    # 3. Get reward of the action we chose
    reward = reward_function(duration)
    logging.info(f'Reward: {reward}')
    # Write info of iteration to csv file
    prob_dict = calculate_counterprobability(action,prob)
    dict = {'context': customer_category, 'action': action, 'prob_a': prob_dict['prob_a'], 'prob_b': prob_dict['prob_b'], 'reward': reward}
    learning_hist.append(dict)
    # Learn on the current example
    # 4. Inform VW of what happened so we can learn from it
    vw_format = vw.parse(to_vw_example_format(context, actions, (action, reward, prob)),
                         vowpalwabbit.LabelType.CONTEXTUAL_BANDIT)
    # 5. Learn
    vw.learn(vw_format)
    # 6. Let VW know you're done with these objects
    vw.finish_example(vw_format)
    # Return the reward of the current iteration
    return reward


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
    # Load model
    vw = load_model(process_id)
    # Get context
    metadata = get_process_metadata(process_id)
    orgas = metadata['customer_categories'].split('-')
    for instance in relevant_instances:
        # Calculate duration
        duration = calculate_duration(instance.instantiation_time, instance.finished_time)
        # Learn 
        reward = run_simulation(vw, orgas, actions, get_reward, duration, instance.decision, instance.customer_category)
        # Update db
        instance.reward = reward
    db.session.commit()
    # Store learning history in csv file
    if not debugging:
        write_to_csv(process_id)
    learning_hist.clear()
    # Set batch policy proposal accordingly
    agent_stats_list = get_action_prob_per_context_dict(vw, orgas, actions)
    set_bapol_proposal(process_id, orgas, [round(agent_stats_list[0]['A'],2), round(agent_stats_list[-1]['A'],2)], 
                                                        [round(agent_stats_list[0]['B'],2), round(agent_stats_list[-1]['B'],2)])
    # Save model
    if not debugging:
        rel_path = 'instance_router/private/cb_models'
        if not os.path.exists(rel_path):
            os.makedirs(rel_path)
        vw.save(rel_path + f'/cb_model_process_id={process_id}')
        del vw