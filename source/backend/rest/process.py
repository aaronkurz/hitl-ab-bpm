import os
import shutil
from flask import Blueprint
from flask import abort, request, send_from_directory
from flask import jsonify
from sqlalchemy import and_

from camunda.client import CamundaClient
from models.batch_policy_proposal import set_naive_bapol_proposal
from models.process_instance import ProcessInstance
from models import db
from models.process import Process, Version
from rest import utils

ALLOWED_EXTENSIONS = {'bpmn'}

process_api = Blueprint('process-variants', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@process_api.route('/<process_name>', methods=['POST'])
def set_process(process_name):
    """ Add a new process with two variants

     Query params:
     default-version: 'a' or 'b'
     customer-categories: separate categories with '-'
     """
    # check if the post request has the correct file part
    if not ('variantA' in request.files and 'variantB' in request.files):
        abort(400, description='No variantA and/or variantB file part')
    variant_a_file = request.files['variantA']
    variant_b_file = request.files['variantB']
    if not (allowed_file(variant_a_file.filename) and allowed_file(variant_b_file.filename)):
        abort(400, description='Only .bpmn files allowed')

    # get default version
    default_version = request.args.get('default-version')
    if default_version == 'a':
        default_version = Version.a
    elif default_version == 'b':
        default_version = Version.b
    else:
        abort(400, 'Default version has to be specified in query argument \'defaultVersion\'')

    # get relevant customer categories
    all_customer_categories = request.args.get('customer-categories').split('-')

    # get upper and lower time of version a history
    a_hist_min_duration = float(request.args.get('a-hist-min-duration'))
    a_hist_max_duration = float(request.args.get('a-hist-max-duration'))
    if a_hist_min_duration is None or a_hist_max_duration is None:
        abort(400, 'Missing query parameter a-hist-min-duration or a-hist-max-duration')

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

    existing = db.session.query(Process).filter(Process.name == process_name)
    if existing.count() == 1:
        db.session.delete(existing.first())
    elif existing.count() > 1:
        abort(500, "There should not be more than one row in process_variant db table with same name")

    variant_a_file.save(path_variant_a)
    variant_b_file.save(path_variant_b)

    # deploy processes to camunda
    camunda_id_a = CamundaClient().deploy_process(path_bpmn_file=path_variant_a)
    camunda_id_b = CamundaClient().deploy_process(path_bpmn_file=path_variant_b)

    process_variant = Process(name=process_name,
                              variant_a_path=path_variant_a,
                              variant_b_path=path_variant_b,
                              variant_a_camunda_id=camunda_id_a,
                              variant_b_camunda_id=camunda_id_b,
                              default_version=default_version,
                              a_hist_min_duration=a_hist_min_duration,
                              a_hist_max_duration=a_hist_max_duration,
                              customer_categories=request.args.get('customer-categories'))

    # change old active process to inactive
    db.session.query(Process).filter(Process.active.is_(True)).update(dict(active=False))
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


@process_api.route('/active-meta', methods=['GET'])
def get_active_process_variants_metadata():
    active_process_entry_query = db.session.query(Process).filter(Process.active.is_(True))
    if active_process_entry_query.count() == 0:
        abort(500, "No active process in db")
    elif active_process_entry_query.count() > 1:
        return abort(500, "More than one active process")
    active_process_entry = active_process_entry_query.first()
    ap_info = {
        'id': active_process_entry.id,
        'name': active_process_entry.name,
        'addedTime': active_process_entry.datetime_added,
        'customerCategories': active_process_entry.customer_categories,
        'defaultVersion':
            None if active_process_entry.default_version is None else active_process_entry.default_version.value,
        'winningVersion':
            None if active_process_entry.winning_version is None else active_process_entry.winning_version.value,
        'decisionTime': active_process_entry.datetime_decided
    }
    return ap_info


@process_api.route('variant-file/<a_or_b>', methods=['GET'])
def get_process_variant_files(a_or_b):
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


@process_api.route('/experiment-state', methods=['GET'])
def get_process_state():
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)
    if Process.query.filter(Process.id == process_id).count == 0:
        abort(404, "No such process/experiment.")
    if Process.query.filter(Process.id == process_id).first().winning_version is not None \
            and ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                  ProcessInstance.do_evaluate == True,
                                                  ProcessInstance.reward is not None)):
        state = "Finished"
    else:
        state = "Running"

    return {
        'state': state
    }
