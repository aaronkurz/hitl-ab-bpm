from flask import Blueprint, request

from models.batch_policy_proposal import exists_bapol_proposal_without_bapol, get_current_open_proposal_data, \
    ExecutionStrategyBaPolProp, BatchPolicyProposal
from models import db

batch_policy_proposal_api = Blueprint('batch_policy_proposal_api', __name__)


@batch_policy_proposal_api.route('/open', methods=['GET'])
def check_get_open_proposal():
    process_id = int(request.args.get('process-id'))
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


@batch_policy_proposal_api.route('', methods=['DELETE'])
def delete_batch_policy_rows():
    execs = db.session.query(ExecutionStrategyBaPolProp)
    for exec in execs:
        db.session.delete(exec)
    bapols = db.session.query(BatchPolicyProposal)
    print(bapols)
    for bapol in bapols:
        db.session.delete(bapol)
    db.session.commit()
    return "Success"
