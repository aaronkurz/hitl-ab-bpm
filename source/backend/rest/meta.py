import os
import shutil

from flask import Blueprint, abort
from models import db

meta_api = Blueprint('meta_api', __name__)


@meta_api.route('/all', methods=['DELETE'])
def empty_database():
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
        except Exception as e:
            abort(500, 'Failed to delete %s. Reason: %s' % (file_path, e))

    # delete all db content
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table %s' % table)
        db.session.execute(table.delete())
    db.session.commit()
    return "Success"
