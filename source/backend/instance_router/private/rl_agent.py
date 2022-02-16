""" Here, the RL agent is implemented """
import logging
import random
from datetime import datetime
import vowpalwabbit
from models import db
from models.process_instance import ProcessInstance
from models.process import get_process_metadata, Process
from models.batch_policy_proposal import set_bapol_proposal, set_or_update_final_bapol_proposal
from sqlalchemy import and_
from config import K_QUANTILES_REWARD_FUNC, LOWER_CUTOFF_REWARD_FUNC, UPPER_CUTOFF_REWARD_FUNC

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Array containing
quantiles = []
# Store latest process_id
latest_process_id = None
# Load model
vw = None
# Actions
ACTIONS = ["A", "B"]


def get_reward(duration: float):
    """
        Return the reward for the action taken based on the duration of the process instance and
        the history of the default proces version.
    params:
        duration (float): Duration of the process instance
    returns:  Reward between 0 and 1
    """
    step_height = (UPPER_CUTOFF_REWARD_FUNC - LOWER_CUTOFF_REWARD_FUNC) / K_QUANTILES_REWARD_FUNC
    quantiles.sort()
    if duration < quantiles[0]:
        return 1.0
    elif duration >= quantiles[K_QUANTILES_REWARD_FUNC]:
        return 0.0
    else:
        for i in range(1, K_QUANTILES_REWARD_FUNC + 1):
            if duration < quantiles[i]:
                return UPPER_CUTOFF_REWARD_FUNC - (i * step_height)


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


def get_action_prob_per_context_dict(orgas, actions):
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
        prob_dict = {}
        prob_dict.update(tmp)
        count = 0
        for action in actions:
            prob_dict[action] = pmf[count]
            count = count + 1
        dict_list.append(prob_dict)
    return dict_list  


def calculate_duration(start_time: datetime, end_time: datetime):
    """
    Calculate the duration of a process instance given start and end timestamp
    :param start_time, end_time
    """
    return (end_time - start_time).total_seconds()


def run_iteration(orgas: list, actions: list, reward_function: get_reward, duration: float, hist_action: str, customer_category: str):
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
    # 1. Set the context 
    context = {'orga': customer_category}
    # 2. Set the chosen action
    action = hist_action.value.upper()
    # Retrieve probabilty for the given context and action
    agent_stats_list = get_action_prob_per_context_dict(orgas, actions)
    for elem in agent_stats_list:
        if elem['orga'] == customer_category:
            prob = elem[action]
    logging.info(f'Action: {action}, Prob: {prob}, Context: {context}')
    # 3. Get reward of the action we chose
    reward = reward_function(duration)
    # vowpalwabbit uses a cost instead of a reward (lower = better)
    cost = 1 - reward
    logging.info(f'Cost: {cost}')
    # 4. Inform VW of what happened so we can learn from it
    vw_format = vw.parse(to_vw_example_format(context, actions, (action, cost, prob)),
                         vowpalwabbit.LabelType.CONTEXTUAL_BANDIT)
    # 5. Learn
    vw.learn(vw_format)
    # 6. Let VW know you're done with these objects
    vw.finish_example(vw_format)
    # Return the reward of the current iteration
    return reward, prob


def learn_and_set_new_batch_policy_proposal(process_id: int, in_cool_off: bool):
    """
    Query process instances which still have to be evaluated. With the calculated duration,
    train the agent and update the database with the reward.
    :param process_id:
    :param in_cool_off:
    :return: new batch policy proposal
    """
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time != None,
                                                           ProcessInstance.do_evaluate == True,
                                                           ProcessInstance.reward == None))
    global latest_process_id
    global vw
    global quantiles
    # Set latest process
    if latest_process_id != process_id:
        latest_process_id = process_id
        vw = vowpalwabbit.Workspace('--cb_explore_adf -q UA --rnd 3 --epsilon 0.025', quiet=True)
        quantiles = Process.query.filter(Process.id == process_id).first().quantiles_default_history
    # Get context
    metadata = get_process_metadata(process_id)
    orgas = metadata['customer_categories'].split('-')
    for instance in relevant_instances:
        # Calculate duration
        duration = calculate_duration(instance.instantiation_time, instance.finished_time)
        # Learn 
        reward, prob = run_iteration(orgas, ACTIONS, get_reward, duration, instance.decision, instance.customer_category)
        # Update db
        instance.reward = reward
        instance.rl_prob = prob
    db.session.commit()
    # Set batch policy proposal accordingly
    agent_stats_list = get_action_prob_per_context_dict(orgas, ACTIONS)
    logging.info(agent_stats_list)
    if in_cool_off:
        set_or_update_final_bapol_proposal(process_id,
                                            orgas,
                                            [round(agent_stats_list[0]['A'], 2),
                                             round(agent_stats_list[-1]['A'], 2)],
                                            [round(agent_stats_list[0]['B'], 2),
                                             round(agent_stats_list[-1]['B'], 2)])
    else:
        set_bapol_proposal(process_id,
                           orgas,
                           [round(agent_stats_list[0]['A'], 2),
                            round(agent_stats_list[-1]['A'], 2)],
                           [round(agent_stats_list[0]['B'], 2),
                            round(agent_stats_list[-1]['B'], 2)])
