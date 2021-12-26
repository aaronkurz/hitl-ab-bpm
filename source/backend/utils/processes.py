from flask import Blueprint
from models.processes import ProcessVariants
from flask import Flask, abort, request, redirect, url_for
import os, shutil
from models import db
from flask import jsonify

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
    os.mkdir(path)

    path_variant_a = os.path.join(path, variant_a_file.filename)
    path_variant_b = os.path.join(path, variant_b_file.filename)

    variant_a_file.save(path_variant_a)
    variant_b_file.save(path_variant_b)
    process_variant = ProcessVariants(name=process_name,
                                      variant_a=path_variant_a,
                                      variant_b=path_variant_b)

    # change old active process to inactive
    db.session.query(ProcessVariants).filter(ProcessVariants.active.is_(True)).update(dict(active=False))
    db.session.add(process_variant)
    db.session.commit()
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
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    # remove db rows
    db.session.query(ProcessVariants).delete()
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


# TODO: get current processes via api and internally
