""" Rest endpoints regarding batch policy proposals """
from flask import Blueprint, request, abort
from models.batch_policy_proposal import exists_bapol_proposal_without_bapol, get_current_open_proposal_data, \
    BatchPolicyProposal, get_final_proposal_data
from models.process import cool_off_over
from rest import utils

batch_policy_proposal_api = Blueprint('batch_policy_proposal_api', __name__)


@batch_policy_proposal_api.route('/open', methods=['GET'])
def check_get_open_proposal():
    """ Check whether there is an open batch policy proposal for a certain process and if yes, return it """
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)
    if not exists_bapol_proposal_without_bapol(process_id):
        return {
            'newProposalExists': False
        }
    return {
        'newProposalExists': True,
        'proposal': get_current_open_proposal_data(process_id)
    }


@batch_policy_proposal_api.route('/count', methods=['GET'])
def get_count():
    """ Get amount of batch policy proposals for a certain process """
    process_id = int(request.args.get('process-id'))
    count = BatchPolicyProposal.query.filter(BatchPolicyProposal.process_id == process_id).count()
    return {
       'baPolProposalCount': count
    }


@batch_policy_proposal_api.route('/final', methods=['GET'])
def get_final_winning_proposal_ready():
    """ For cool-off period: tries to find final proposal (available in cool-off when all instances have been
    evaluated), if none can be found returns 404 """
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)

    if cool_off_over(process_id):
        return get_final_proposal_data(process_id)
    abort(404, "No final proposal available for currently active process")
