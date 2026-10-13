import sys

import pytest


CONTRACT = "contracts/governed_executor.py"
GUARD = "0x3333333333333333333333333333333333333333"


def deploy(direct_deploy, direct_vm):
    direct_vm.sender = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    return direct_deploy(CONTRACT, GUARD, sdk_version="v0.2.16")


class FakeGuard:
    def __init__(self, proposer):
        self.proposal = {
            "proposer": proposer,
            "execution_summary": "Fund the public RPC failover.",
            "executor": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "status": "approved",
            "consumed": False,
        }
        self.queued_proposals = []

    def view(self):
        return self

    def get_proposal(self, proposal_id):
        return self.proposal

    def emit(self, on):
        assert on == "finalized"
        return self

    def consume_permit(self, proposal_id):
        self.queued_proposals.append(proposal_id)


def test_executor_finalizes_only_after_guard_permit_consumption(
    direct_deploy, direct_vm, direct_bob
):
    executor = deploy(direct_deploy, direct_vm)
    from genlayer.py.types import Address

    fake_guard = FakeGuard(Address(direct_bob))
    fake_guard.proposal["executor"] = "0x" + direct_vm._contract_address.hex()
    module = sys.modules[executor._instance.__class__.__module__]
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.gl, "get_contract_at", lambda address: fake_guard)

    try:
        direct_vm.sender = direct_bob
        executor.start_execution("upgrade-1")
        assert fake_guard.queued_proposals == ["upgrade-1"]
        assert executor.get_execution("upgrade-1")["status"] == "awaiting_permit"

        with direct_vm.expect_revert("Permit has not been consumed"):
            executor.finalize_execution("upgrade-1")

        fake_guard.proposal["status"] = "permit_consumed"
        fake_guard.proposal["consumed"] = True
        executor.finalize_execution("upgrade-1")
        assert executor.get_execution("upgrade-1")["status"] == "executed"
    finally:
        monkeypatch.undo()


def test_executor_rejects_wrong_proposer_and_denied_proposal(direct_deploy, direct_vm, direct_bob):
    executor = deploy(direct_deploy, direct_vm)
    from genlayer.py.types import Address

    fake_guard = FakeGuard(Address(direct_bob))
    fake_guard.proposal["status"] = "rejected"
    module = sys.modules[executor._instance.__class__.__module__]
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.gl, "get_contract_at", lambda address: fake_guard)

    try:
        direct_vm.sender = direct_bob
        with direct_vm.expect_revert("No valid proposal permit"):
            executor.start_execution("rejected")
        fake_guard.proposal["status"] = "approved"
        direct_vm.sender = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        with direct_vm.expect_revert("Caller is not the proposer"):
            executor.start_execution("wrong-proposer")
    finally:
        monkeypatch.undo()


