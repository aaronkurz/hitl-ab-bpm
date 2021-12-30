import os
import shutil

from flask import Blueprint
from flask import abort, request, send_from_directory
from flask import jsonify

from camunda.client import CamundaClient
from models import db
from models.processes import ProcessVariants

ALLOWED_EXTENSIONS = {'bpmn'}

process_variants_api = Blueprint('process-variants', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@process_variants_api.route('/<process_name>', methods=['POST'])
def set_process(process_name):
    """ Add a new process with two variants """
    # check if the post request has the correct file part
    if not ('variantA' in request.files and 'variantB' in request.files):
        abort(400, description='No variantA and/or variantB file part')
    variant_a_file = request.files['variantA']
    variant_b_file = request.files['variantB']
    if not (allowed_file(variant_a_file.filename) and allowed_file(variant_b_file.filename)):
        abort(400, description='Only .bpmn files allowed')

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

    existing = db.session.query(ProcessVariants).filter(ProcessVariants.name == process_name)
    if existing.count() == 1:
        db.session.delete(existing.first())
    elif existing.count() > 1:
        abort(500, "There should not be more than one row in process_variant db table with same name")

    variant_a_file.save(path_variant_a)
    variant_b_file.save(path_variant_b)

    # deploy processes to camunda
    # TODO: replace static url with flexible approach from backend/config.py (didn't work)
    camunda_id_a = CamundaClient("http://localhost:8080/engine-rest").deploy_process(path_bpmn_file=path_variant_a)
    camunda_id_b = CamundaClient("http://localhost:8080/engine-rest").deploy_process(path_bpmn_file=path_variant_b)

    process_variant = ProcessVariants(name=process_name,
                                      variant_a_path=path_variant_a,
                                      variant_b_path=path_variant_b,
                                      variant_a_camunda_id=camunda_id_a,
                                      variant_b_camunda_id=camunda_id_b)

    # change old active process to inactive
    db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True)).update(dict(active=False))
    db.session.add(process_variant)
    db.session.commit()
    # TODO: return new row
    return "Success"


@process_variants_api.route('', methods=['DELETE'])
def delete_process_variants_rows():
    # delete process versions from filesystem
    folder = os.path.join(os.getcwd(), 'resources/bpmn/')

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            abort(500, 'Failed to delete %s. Reason: %s' % (file_path, e))
    # remove db rows
    results = db.session.query(ProcessVariants).all()
    for result in results:
        db.session.delete(result)
    db.session.commit()
    return "Success"


@process_variants_api.route('/count', methods=['GET'])
def get_processes_count():
    """ Get amount of processes that have been set / entries in processes db table """
    data = {
        "processesCount": ProcessVariants.query.count()
    }
    json_data = jsonify(data)
    return json_data


@process_variants_api.route('/active-meta', methods=['GET'])
def get_active_process_variants_metadata():
    active_process_entry_query = db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True))
    if active_process_entry_query.count() == 0:
        return "No active process in db"
    elif active_process_entry_query.count() > 1:
        return abort(500, "More than one active process")
    active_process_entry = active_process_entry_query.first()
    ap_info = {
        'id': active_process_entry.id,
        'name': active_process_entry.name,
        'added': active_process_entry.datetime_added
    }
    return ap_info


@process_variants_api.route('variant_file/<a_or_b>', methods=['GET'])
def get_process_variant_files(a_or_b):
    requested_id = request.args.get('id')
    if requested_id is None:
        abort(400, description='id query parameter not specified')
    active_process_entry_query = db.session.query(ProcessVariants).filter(ProcessVariants.id == requested_id)
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
        abort(400, description='requested variant must be a or b (e.g. process-variants/variant_file/a)')
