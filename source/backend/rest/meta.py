""" REST endpoints that do not concern any singular other endpoint but are more general """
# pylint: disable=missing-return-doc, missing-return-type-doc
import os
import shutil
from flask import Blueprint, abort
from models import db

meta_api = Blueprint('meta_api', __name__)


@meta_api.route('/all', methods=['DELETE'])
def empty_database():
    """ Empty database and delete stored state on filesystem """
    # delete process versions from filesystem
    folder = os.path.join(os.getcwd(), 'resources/')
    if not os.path.exists(folder):
        os.makedirs(folder)

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except (NotImplementedError, OSError) as file_path_error:
            abort(500, f'Failed to delete {file_path}. Reason: {file_path_error}')

    # delete all db content
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f'Clear table {table}')
        db.session.execute(table.delete())
    db.session.commit()
    return "Success"
