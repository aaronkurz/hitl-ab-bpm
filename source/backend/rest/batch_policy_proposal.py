from flask import Blueprint, request
from models.batch_policy_proposal import exists_bapol_proposal_without_bapol, get_current_open_proposal_data, BatchPolicyProposal
from rest import utils

batch_policy_proposal_api = Blueprint('batch_policy_proposal_api', __name__)


@batch_policy_proposal_api.route('/open', methods=['GET'])
def check_get_open_proposal():
    process_id = int(request.args.get('process-id'))
    utils.validate_backend_process_id(process_id)
    if not exists_bapol_proposal_without_bapol(process_id):
        return {
            'newProposalExists': False
        }
    else:
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
