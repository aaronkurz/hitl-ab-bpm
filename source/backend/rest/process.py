""" REST endpoints regarding processes/experiments """
# pylint: disable=missing-return-doc, missing-return-type-doc
import json
import os
import shutil
import requests
from flask import Blueprint
from flask import abort, request, send_from_directory
from flask import jsonify
from scipy.stats.mstats import mquantiles
from werkzeug.datastructures import FileStorage
from camunda.client import CamundaClient
from instance_router import instance_router_interface
from instance_router.instance_router_interface import manual_fetch_and_learn
from models.batch_policy_proposal import set_naive_bapol_proposal
from models.batch_policy import get_number_finished_bapols, BatchPolicy
from models import db, process
from models.process import Process, cool_off_over, set_winning, CustomerCategory, get_sorted_customer_category_list, \
    get_experiment_state_str, get_process_entry, is_decision_made, get_winning, get_active_process_id
from models.process_instance import ProcessInstance
from models.utils import WinningReasonEnum, Version, parse_version_str, ExperimentState
from rest import utils
from config import K_QUANTILES_REWARD_FUNC

process_api = Blueprint('process-variants', __name__)


def get_process_metadata(process_id: int) -> dict:
    """Get data about specified process.

    :param process_id: specify process
    :return: metadata about process
    """
    relevant_process_entry = get_process_entry(process_id)
    # get customer categories
    customer_category_string = "-".join(process.get_sorted_customer_category_list(process_id))
    ap_info = {
        'id': relevant_process_entry.id,
        'name': relevant_process_entry.name,
        'customer_categories': customer_category_string,
        'datetime_added': relevant_process_entry.datetime_added,
        'default_interarrival_time_history': relevant_process_entry.interarrival_default_history,
        'experiment_state': process.get_experiment_state_str(process_id),
        'default_version':
            None if relevant_process_entry.default_version is None else relevant_process_entry.default_version.value,
        'winning_versions': None if not is_decision_made(process_id) else
        [{"customer_category": part_win['customer_category'],
          "winning_version": part_win['winning_version'].value}
         for part_win in get_winning(process_id)],
        'winning_reason':
            None if relevant_process_entry.winning_reason is None else relevant_process_entry.winning_reason.value,
        'datetime_decided': relevant_process_entry.datetime_decided,
        'number_batch_policies':
            BatchPolicy.query.filter(BatchPolicy.process_id == relevant_process_entry.id).count(),
        'number_instances':
            ProcessInstance.query.filter(ProcessInstance.process_id == relevant_process_entry.id).count()
    }
    return ap_info


def get_active_process_metadata() -> dict:
    """Get data about currently active process.

    :return: data about active process
    """
    return get_process_metadata(get_active_process_id())


def allowed_file_models(filename: str) -> bool:
    """Check whether the type is allowed for a bpmn model file.

    :param filename: name of the file
    :return: True or False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['bpmn']


def allowed_file_history(filename: str) -> bool:
    """Check whether the type is allowed for a file history file.

    :param filename: name of the file
    :return: True or False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['json']


def get_active_process_entry() -> Process:
    """Get the currently active process entry.

    :return: Currently active process entry instance from process table
    """
    active_process_entry_query = db.session.query(Process).filter(Process.active.is_(True))
    if active_process_entry_query.count() == 0:
        abort(404, "No active process/experiment in db yet")
    elif active_process_entry_query.count() > 1:
        abort(500, "More than one active process")
    return active_process_entry_query.first()


def extract_data_from_history(path_json: str) -> tuple[list[float], float]:
    """Extract quantiles list and interarrival time from history data.

    :param path_json: path to history json file
    :return: list with quantile borders and average interarrival time
    """
    with open(path_json, encoding='us-ascii') as json_file:
        history_data: dict = json.load(json_file)
        if not (sorted(list(history_data.keys())) == sorted(['durations', 'interarrivalTime'])
                and isinstance(history_data.get('durations'), list)
                and isinstance(history_data.get('durations')[0], float)
                and isinstance(history_data.get('interarrivalTime'), float)):
            abort(400, "Wrong json format interarrival time file")
        quantiles = mquantiles(history_data.get('durations'),
                               prob=[round((1 / 20) * x, 2) for x in range(0, K_QUANTILES_REWARD_FUNC + 1)])
        quantiles_list = quantiles.tolist()
        quantiles_list.sort()
        interarrival_time = history_data.get('interarrivalTime')
        return quantiles_list, interarrival_time


def store_files_on_filesystem(process_name: str,
                              variant_a_file: FileStorage,
                              variant_b_file: FileStorage,
                              history_durations_file: FileStorage,
                              default_version: Version) -> tuple[str, str, str]:
    """Store submitted files on filesystem of server.

    :param process_name: Name of process
    :param variant_a_file: Variant a file
    :param variant_b_file: Variant b file
    :param history_durations_file: History durations file
    :param default_version: which is the default version
    :return: Path of variant a and b and history json on filesystem
    """
    # Directory
    directory = process_name
    # Parent Directory path
    parent_dir = os.path.join(os.getcwd(), 'resources/bpmn/')
    # Path
    path = os.path.join(parent_dir, directory)
    # Create the directory
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    if len(os.listdir(path)) != 0:
        abort(500, "Directory for bpmn files with process name should be empty")
    path_variant_a = os.path.join(path, variant_a_file.filename)
    path_variant_b = os.path.join(path, variant_b_file.filename)

    # Storing the json file in file system
    path_json = os.path.join(os.getcwd(), path + '/duration-history-' + default_version.value + ".json")
    history_durations_file.save(path_json)
    return path_variant_a, path_variant_b, path_json


@process_api.route('/<process_name>', methods=['POST'])
def set_process(process_name: str):
    """ Add a new process with two variants

    :param process_name: Name of process, from url param

     Query params:
     default-version: 'a' or 'b'
     customer-categories: separate categories with '-'
     """
    # check if the post request has the correct file part
    if not ('variantA' in request.files and 'variantB' in request.files and 'defaultHistory' in request.files):
        abort(400, description='No variantA and/or variantB file part')
    variant_a_file = request.files['variantA']
    variant_b_file = request.files['variantB']
    history_durations_file = request.files['defaultHistory']
    if not (allowed_file_models(variant_a_file.filename)
            and allowed_file_models(variant_b_file.filename)
            and allowed_file_history(history_durations_file.filename)):
        abort(400, description='Only .bpmn files allowed for models and .json files allowed for history')

    # get relevant customer categories
    all_customer_categories = request.args.get('customer-categories').split('-')

    try:
        default_version = parse_version_str(request.args.get('default-version'))
    except RuntimeError as r_e:
        abort(400, str(r_e))

    # Storing the files in filesystem
    path_variant_a, path_variant_b, path_history_json = store_files_on_filesystem(process_name,
                                                                                  variant_a_file,
                                                                                  variant_b_file,
                                                                                  history_durations_file,
                                                                                  default_version)

    existing = db.session.query(Process).filter(Process.name == process_name)
    if existing.count() == 1:
        db.session.delete(existing.first())
    elif existing.count() > 1:
        abort(500, "There should not be more than one row in process_variant db table with same name")

    variant_a_file.save(path_variant_a)
    variant_b_file.save(path_variant_b)

    quantiles_list, interarrival_time = extract_data_from_history(path_history_json)

    process_variant = Process(name=process_name,
                              variant_a_path=path_variant_a,
                              variant_b_path=path_variant_b,
                              variant_a_camunda_id=CamundaClient().deploy_process(path_bpmn_file=path_variant_a),
                              variant_b_camunda_id=CamundaClient().deploy_process(path_bpmn_file=path_variant_b),
                              default_version=default_version,
                              quantiles_default_history=quantiles_list,
                              interarrival_default_history=interarrival_time,
                              customer_categories=[CustomerCategory(name=customer_category)
                                                   for customer_category in all_customer_categories])

    # change old active process to inactive
    db.session.query(Process).filter(Process.active.is_(True)).update({"active": False})
    db.session.add(process_variant)
    db.session.commit()
    # add naive bp proposal
    set_naive_bapol_proposal(process_variant.id, all_customer_categories)
    return {
        'processId': process_variant.id
    }


@process_api.route('/count', methods=['GET'])
def get_processes_count():
    """ Get amount of processes that have been set / entries in processes db table """
    data = {
        "processesCount": Process.query.count()
    }
    json_data = jsonify(data)
    return json_data


@process_api.route('/active/meta', methods=['GET'])
def get_active_process_variants_metadata():
    """ Get metadata about running experiment/process """
    active_process_entry = get_active_process_entry()
    return get_process_metadata(active_process_entry.id)


@process_api.route('/active/cool-off', methods=['POST'])
def start_cool_off_active():
    """ Start cool-off period

    Condition: can only be started after one finished batch.
    """
    active_process_entry = get_active_process_entry()
    number_finished_bapols = get_number_finished_bapols(active_process_entry.id)
    if number_finished_bapols == 0:
        abort(404, """
        No bapol has been finished yet. The cool-off period can only be started after at least one finished bapol
        """)
    elif number_finished_bapols > 0:
        active_process_entry.in_cool_off = True
        db.session.commit()
        manual_fetch_and_learn(active_process_entry.id)
        return {
            'experimentState': get_experiment_state_str(active_process_entry.id)
        }
    elif number_finished_bapols < 0:
        abort(500, "Unexpected finished bapol count < 0")


@process_api.route('/active/winning', methods=['POST'])
def set_winning_version():
    """ Set a decision/winning versions

    Only available if in cool-off and all instances have been evaluates ('cool-off-over')
    """
    active_process_entry = get_active_process_entry()
    if not cool_off_over(active_process_entry.id):
        abort(404, "No active process that has a finished cool off period available")

    dec_json = request.json
    assert "decision" in dec_json.keys()
    decision_parsed = []
    for part_decision in dec_json.get("decision"):
        assert "winning_version" in part_decision.keys()
        assert "customer_category" in part_decision.keys()
        if part_decision.get('winning_version') == 'a':
            decision_parsed.append({"customer_category": part_decision.get('customer_category'),
                                    "winning_version": Version.A})
        elif part_decision.get('winning_version') == 'b':
            decision_parsed.append({"customer_category": part_decision.get('customer_category'),
                                    "winning_version": Version.B})
        else:
            abort(400, "winning_version must be a or b")
    set_winning(active_process_entry.id, decision_parsed, WinningReasonEnum.EXPERIMENT_ENDED)
    return {
        'experiment_state': get_experiment_state_str(active_process_entry.id)
    }


@process_api.route('active/manual-decision', methods=['POST'])
def manual_decision():
    """API endpoint to allow human expert to manually make a decision

    Only supports same decision for all customer categories!
    """
    active_process_entry = get_active_process_entry()
    winning_version_str = request.args.get("version-decision")
    if winning_version_str == 'a':
        winning_version = Version.A
    elif winning_version_str == 'b':
        winning_version = Version.B
    else:
        abort(400, "version-decision query param must be a or b")
    decision_list = []
    for customer_category in get_sorted_customer_category_list(active_process_entry.id):
        decision_list.append({"customer_category": customer_category, "winning_version": winning_version})
    set_winning(active_process_entry.id, decision_list, WinningReasonEnum.MANUAL_CHOICE)
    return "Success"


@process_api.route('active/trigger-fetch-learn', methods=['POST'])
def trigger_fetch_learn():
    """ Manually trigger fetching info about instances from camunda and training rl agent with this additional info """
    active_process_entry = get_active_process_entry()
    if process.get_experiment_state_enum(active_process_entry.id) == ExperimentState.COOL_OFF_FIN_DEC_OUTSTANDING:
        abort(requests.codes.conflict, "Not possible in current experiment state")  # pylint: disable=no-member
    try:
        instance_router_interface.manual_fetch_and_learn(active_process_entry.id)
    except RuntimeWarning as r_w:
        abort(requests.codes.conflict, str(r_w))  # pylint: disable=no-member
    return "Success", requests.codes.ok  # pylint: disable=no-member


@process_api.route('variant-file/<a_or_b>', methods=['GET'])
def get_process_variant_files(a_or_b: str):
    """ Retrieve the bpmn file of a certain process and version via the API

    :param a_or_b: 'a' or 'b'
    """
    requested_id = int(request.args.get('id'))
    utils.validate_backend_process_id(requested_id)
    if requested_id is None:
        abort(400, description='id query parameter not specified')
    active_process_entry_query = db.session.query(Process).filter(Process.id == requested_id)
    if active_process_entry_query.count() == 0:
        abort(404, description='No process with specified id found')

    active_process_entry = active_process_entry_query.first()
    if a_or_b == 'a':
        try:
            path = active_process_entry.variant_a_path.split('/')[
                len(active_process_entry.variant_a_path.split('/')) - 1]
            directory = active_process_entry.variant_a_path.split('/')
            directory.pop()
            directory = "/".join(directory)
            return send_from_directory(directory=directory,
                                       path=path,
                                       as_attachment=True)
        except FileNotFoundError:
            abort(500)
    elif a_or_b == 'b':
        try:
            path = active_process_entry.variant_b_path.split('/')[
                len(active_process_entry.variant_b_path.split('/')) - 1]
            directory = active_process_entry.variant_b_path.split('/')
            directory.pop()
            directory = "/".join(directory)
            return send_from_directory(directory=directory,
                                       path=path,
                                       as_attachment=True)
        except FileNotFoundError:
            abort(404)
    else:
        abort(400, description='requested variant must be a or b (e.g. process-variants/variant-file/a)')
