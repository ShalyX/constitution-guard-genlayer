import json
import time


CONTRACT = "contracts/constitution_guard.py"
EXECUTOR = "0x2222222222222222222222222222222222222222"
CONSTITUTION_SOURCE = "https://dao.example.org/constitution"
EVIDENCE_SOURCE = "https://dao.example.org/proposals/upgrade-1"
REFERENCE_SOURCE = "https://dao.example.org/resolutions/12"
CLAUSES = json.dumps(
    [
        {"id": "budget", "text": "The proposal must stay within the published treasury budget."},
        {"id": "disclosure", "text": "The proposal must disclose material implementation and security risks."},
        {"id": "mandate", "text": "The proposal must advance the DAO's public infrastructure mandate."},
    ]
)


def address(account) -> str:
    return f"0x{account.hex()}"


def deploy(direct_deploy):
    return direct_deploy(CONTRACT, sdk_version="v0.2.16")


def create_default_constitution(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    contract.create_constitution(
        "dao-constitution",
        "Northstar DAO Constitution",
        "Rules for approving treasury proposals that affect public infrastructure.",
        CLAUSES,
        CONSTITUTION_SOURCE,
    )


def submit_default_proposal(contract, direct_vm, direct_bob, proposal_id="upgrade-1"):
    direct_vm.sender = direct_bob
    contract.submit_proposal(
        proposal_id,
        "dao-constitution",
        "Fund the public RPC failover",
        "Allocate the published treasury amount to a redundant public RPC deployment.",
        "Transfer the approved budget to the governed treasury executor.",
        EVIDENCE_SOURCE,
        REFERENCE_SOURCE,
        int(time.time()) + 3600,
        EXECUTOR,
    )


def approve_review():
    return json.dumps(
        {
            "decision": "approved",
            "clauses": [
                {"id": "budget", "state": "satisfied"},
                {"id": "disclosure", "state": "satisfied"},
                {"id": "mandate", "state": "satisfied"},
            ],
            "reason_codes": [],
            "confidence_band": "high",
            "rationale": "The constitution, proposal evidence, and prior resolution support every clause.",
        }
    )


def test_non_approved_review_gets_deterministic_reason_code(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    parsed = contract._parse_review(
        {
            "decision": "rejected",
            "clauses": [
                {"id": "budget", "state": "violated"},
                {"id": "disclosure", "state": "satisfied"},
                {"id": "mandate", "state": "satisfied"},
            ],
            "reason_codes": [],
            "confidence_band": "high",
            "rationale": "The proposal exceeds the published treasury budget.",
        },
        ["budget", "disclosure", "mandate"],
    )
    assert parsed["decision"] == "rejected"
    assert parsed["reason_codes"] == "CONFLICT_WITH_CLAUSE"


def test_duplicate_and_unknown_non_approval_reasons_are_normalized(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    parsed = contract._parse_review(
        {
            "decision": "needs_human_review",
            "clauses": [
                {"id": "budget", "state": "unclear"},
                {"id": "disclosure", "state": "satisfied"},
                {"id": "mandate", "state": "satisfied"},
            ],
            "reason_codes": ["ambiguous scope", "AMBIGUOUS_SCOPE", "model_guess"],
            "confidence_band": "low",
            "rationale": "The available material does not resolve the budget scope.",
        },
        ["budget", "disclosure", "mandate"],
    )
    assert parsed["reason_codes"] == "AMBIGUOUS_SCOPE|OTHER"


def mock_sources(direct_vm):
    direct_vm.mock_web(
        r"https://dao\.example\.org/constitution",
        {"status": 200, "body": "Northstar constitution: published budget, disclosure, and infrastructure mandate."},
    )
    direct_vm.mock_web(
        r"https://dao\.example\.org/proposals/upgrade-1",
        {"status": 200, "body": "Proposal evidence: budget allocation, risk disclosure, and public RPC implementation plan."},
    )
    direct_vm.mock_web(
        r"https://dao\.example\.org/resolutions/12",
        {"status": 200, "body": "Resolution 12: public infrastructure proposals may fund redundant RPC capacity."},
    )


def test_constitution_and_proposal_bind_versions_and_sources(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    submit_default_proposal(contract, direct_vm, direct_bob)

    constitution = contract.get_constitution("dao-constitution")
    proposal = contract.get_proposal("upgrade-1")
    assert constitution["version"] == 1
    assert constitution["active"] is True
    assert proposal["constitution_version"] == 1
    assert proposal["status"] == "pending"
    assert proposal["evidence_urls"] == EVIDENCE_SOURCE
    assert proposal["reference_urls"] == REFERENCE_SOURCE


def test_complete_consensus_issues_one_use_permit_and_consumes_only_by_executor(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    submit_default_proposal(contract, direct_vm, direct_bob)
    mock_sources(direct_vm)
    direct_vm.mock_llm(r"(?s).*public RPC.*", approve_review())

    direct_vm.sender = direct_alice
    contract.evaluate_proposal("upgrade-1")
    proposal = contract.get_proposal("upgrade-1")
    assert proposal["status"] == "approved"
    assert proposal["decision"] == "approved"
    assert proposal["reason_codes"] == ""
    assert proposal["permit_nonce"] == 1
    assert json.loads(proposal["passed_clause_ids_json"]) == ["budget", "disclosure", "mandate"]
    assert CONSTITUTION_SOURCE in proposal["source_snapshot"]
    assert EVIDENCE_SOURCE in proposal["source_snapshot"]

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Caller is not the designated executor"):
        contract.consume_permit("upgrade-1")

    direct_vm.sender = bytes.fromhex(EXECUTOR[2:])
    assert contract.is_permit_valid("upgrade-1") is True
    contract.consume_permit("upgrade-1")
    assert contract.get_proposal("upgrade-1")["status"] == "permit_consumed"
    with direct_vm.expect_revert("Proposal has no active permit"):
        contract.consume_permit("upgrade-1")


def test_missing_source_fails_closed_even_if_model_claims_approval(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    submit_default_proposal(contract, direct_vm, direct_bob, proposal_id="missing-source")
    direct_vm.mock_web(r"https://dao\.example\.org/constitution", {"status": 503, "body": "offline"})
    direct_vm.mock_web(r"https://dao\.example\.org/proposals/upgrade-1", {"status": 200, "body": "Evidence"})
    direct_vm.mock_web(r"https://dao\.example\.org/resolutions/12", {"status": 200, "body": "Resolution"})
    direct_vm.mock_llm(r"(?s).*Evidence.*", approve_review())

    direct_vm.sender = direct_alice
    contract.evaluate_proposal("missing-source")
    proposal = contract.get_proposal("missing-source")
    assert proposal["status"] == "insufficient_evidence"
    assert proposal["decision"] == "needs_human_review"
    assert proposal["reason_codes"] == "SOURCE_FAILURE"
    assert proposal["permit_nonce"] == 0
    assert proposal["consumed"] is False


def test_incomplete_clause_partition_is_rejected_by_parser(
    direct_vm, direct_deploy, direct_alice
):
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("every clause must be classified exactly once"):
        contract._parse_review(
            {
                "decision": "approved",
                "clauses": [{"id": "budget", "state": "satisfied"}],
                "reason_codes": [],
                "confidence_band": "high",
                "rationale": "Incomplete result.",
            },
            ["budget", "disclosure", "mandate"],
        )


def test_constitution_update_invalidates_pending_proposal(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    submit_default_proposal(contract, direct_vm, direct_bob, proposal_id="stale-proposal")
    direct_vm.sender = direct_alice
    contract.update_constitution(
        "dao-constitution",
        "Only security remediation is allowed this quarter.",
        CLAUSES,
        CONSTITUTION_SOURCE,
        True,
    )
    contract.evaluate_proposal("stale-proposal")
    proposal = contract.get_proposal("stale-proposal")
    assert proposal["status"] == "invalidated"
    assert proposal["reason_codes"] == "CONSTITUTION_CHANGED"
    assert proposal["permit_nonce"] == 0


def test_constitution_update_revokes_active_approved_permit(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    submit_default_proposal(contract, direct_vm, direct_bob, proposal_id="approved-before-update")
    direct_vm.mock_web(r"https://dao\.example\.org/constitution", {"status": 200, "body": "Constitution"})
    direct_vm.mock_web(r"https://dao\.example\.org/proposals/upgrade-1", {"status": 200, "body": "Evidence"})
    direct_vm.mock_web(r"https://dao\.example\.org/resolutions/12", {"status": 200, "body": "Resolution"})
    direct_vm.mock_llm(r"(?s).*Evidence.*", approve_review())

    direct_vm.sender = direct_alice
    contract.evaluate_proposal("approved-before-update")
    assert contract.get_proposal("approved-before-update")["status"] == "approved"

    contract.update_constitution(
        "dao-constitution",
        "Only security remediation is allowed this quarter.",
        CLAUSES,
        CONSTITUTION_SOURCE,
        True,
    )
    proposal = contract.get_proposal("approved-before-update")
    assert proposal["status"] == "invalidated"
    assert proposal["decision"] == "rejected"
    assert proposal["reason_codes"] == "CONSTITUTION_CHANGED"
    assert proposal["consumed"] is False


def test_expiry_is_rejected_at_submission(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_deploy)
    create_default_constitution(contract, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("valid_until must be in the future"):
        contract.submit_proposal(
            "expired",
            "dao-constitution",
            "Expired proposal",
            "This proposal is already expired.",
            "No execution.",
            EVIDENCE_SOURCE,
            "",
            1,
            EXECUTOR,
        )


