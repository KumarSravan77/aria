from server.models.schemas import StatusTransitionRequest, ApprovalRequest, ApprovalDecisionRequest


def test_request_schemas_do_not_accept_spoofable_actor_fields():
    assert "actor" not in StatusTransitionRequest.model_fields
    assert "requested_by" not in ApprovalRequest.model_fields
    assert "approver" not in ApprovalDecisionRequest.model_fields
