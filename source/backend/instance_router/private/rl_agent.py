""" Here, the RL agent is implemented """
import logging
from datetime import datetime
import vowpalwabbit
from models import db
from models.process_instance import ProcessInstance
from models.process import Process, get_sorted_customer_category_list
from models.batch_policy_proposal import set_or_update_bapol_proposal, set_or_update_final_bapol_proposal
from sqlalchemy import and_
from config import K_QUANTILES_REWARD_FUNC, LOWER_CUTOFF_REWARD_FUNC, UPPER_CUTOFF_REWARD_FUNC

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Store global mutable fields
rl_agent_globals = dict(latest_process_id=None, vw=None, quantiles=[])
# Actions
ACTIONS = ["A", "B"]


def get_reward(duration: float) -> float:
    """Return the reward for the action taken

    ...based on the duration of the process instance and the history of the default proces version.
    :param duration: Duration of the process instance
    :return: Reward between 0 and 1
    """
    step_height = (UPPER_CUTOFF_REWARD_FUNC - LOWER_CUTOFF_REWARD_FUNC) / K_QUANTILES_REWARD_FUNC
    rl_agent_globals['quantiles'].sort()
    if duration < rl_agent_globals['quantiles'][0]:
        return 1.0
    if duration >= rl_agent_globals['quantiles'][K_QUANTILES_REWARD_FUNC]:
        return 0.0
    for i in range(1, K_QUANTILES_REWARD_FUNC + 1):
        if duration < rl_agent_globals['quantiles'][i]:
            return UPPER_CUTOFF_REWARD_FUNC - (i * step_height)


def to_vw_format(context: str, actions: list, cb_label: tuple = None) -> str:
    """Modify (context, action, cost, probability) to a VW friendly format.

    :param context: The context of the cb
    :param actions: List of all possible actions
    :param cb_label: ?
    :return: VW friendly String
    """
    if cb_label is not None:
        chosen_action, cost, prob = cb_label
    example_string = ""
    example_string += f"shared |Orga orga={context['orga']}\n"
    for action in actions:
        if cb_label is not None and action == chosen_action:
            example_string += f"0:{cost}:{prob} "
        example_string += f"|Action variant={action} \n"
    # Strip the last newline
    return example_string[:-1]


def get_action_prob_per_context_dict(orgas: list, actions: list) -> dict:
    """Retrieve the probability for each action given any context.

    :param orgas: The context
    :param actions: All possible actions
    :return: Dictionary containing the probabilities of each action under given context
    """
    # Multiple contexts, loop over list of contexts
    dict_list = []
    for elem in orgas:
        tmp = {'orga': elem}
        vw_text_example = to_vw_format(tmp, actions)
        pmf = rl_agent_globals['vw'].predict(vw_text_example)
        prob_dict = {}
        prob_dict.update(tmp)
        count = 0
        for action in actions:
            prob_dict[action] = pmf[count]
            count = count + 1
        dict_list.append(prob_dict)
    return dict_list


def calculate_duration(start_time: datetime, end_time: datetime) -> float:
    """Calculate the duration of a process instance given start and end timestamp.

    :param start_time: start
    :param end_time: end
    :return: duration in seconds
    """
    return (end_time - start_time).total_seconds()


def run_iteration(orgas: list[str], duration: float, hist_action: str, customer_category: str) -> tuple[float, float]:
    """Run learning for one instance.

    :param orgas: List of organisations the agent can choose from
    :param duration: Duration of a process instance
    :param hist_action: Action retrieved from the database
    :param customer_category: Context retrieved from the database
    :return: reward and probability with which the agent would have chosen that action
    """
    # 1. Set the context
    context = {'orga': customer_category}
    # 2. Set the chosen action
    action = hist_action.value.upper()
    # Retrieve probability for the given context and action
    agent_stats_list = get_action_prob_per_context_dict(orgas, ACTIONS)
    for elem in agent_stats_list:
        if elem['orga'] == customer_category:
            prob = elem[action]
    logging.info('Action: %s, Prob: %f, Context: %s', action, prob, context)
    # 3. Get reward of the action we chose
    reward = get_reward(duration)
    # vowpalwabbit uses a cost instead of a reward (lower = better)
    cost = 1 - reward
    logging.info('Cost: %f', cost)
    # 4. Inform VW of what happened so we can learn from it
    vw_format = rl_agent_globals['vw'].parse(to_vw_format(context, ACTIONS, (action, cost, prob)),
                                             vowpalwabbit.LabelType.CONTEXTUAL_BANDIT)
    # 5. Learn
    rl_agent_globals['vw'].learn(vw_format)
    # 6. Let VW know you're done with these objects
    rl_agent_globals['vw'].finish_example(vw_format)
    # Return the reward of the current iteration
    return reward, prob


def learn_and_set_new_batch_policy_proposal(process_id: int, in_cool_off: bool):
    """Learn with finished but unevaluated instances of process and set new batch policy proposal

    Query process instances which still have to be evaluated. With the calculated duration,
    train the agent and update the database with the reward.
    :param process_id: id of process
    :param in_cool_off: whether this is called in cool-off for process or outside of cool-off period
    """
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time.is_not(None),
                                                           ProcessInstance.do_evaluate.is_(True),
                                                           ProcessInstance.reward.is_(None)))
    # Set latest process
    if rl_agent_globals['latest_process_id'] != process_id:
        rl_agent_globals['latest_process_id'] = process_id
        rl_agent_globals['vw'] = vowpalwabbit.Workspace('--cb_explore_adf -q UA --rnd 3 --epsilon 0.025', quiet=True)
        rl_agent_globals['quantiles'] = Process.query.filter(Process.id == process_id).first().quantiles_default_history
    # Get context
    orgas = get_sorted_customer_category_list(process_id)
    for instance in relevant_instances:
        # Calculate duration
        duration = calculate_duration(instance.instantiation_time, instance.finished_time)
        # Learn
        reward, prob = run_iteration(orgas, duration, instance.decision, instance.customer_category)
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
        set_or_update_bapol_proposal(process_id,
                                     orgas,
                                     [round(agent_stats_list[0]['A'], 2),
                                      round(agent_stats_list[-1]['A'], 2)],
                                     [round(agent_stats_list[0]['B'], 2),
                                      round(agent_stats_list[-1]['B'], 2)])
