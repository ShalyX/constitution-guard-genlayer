# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from dataclasses import dataclass
from datetime import datetime, timezone

from genlayer import *


ERROR_EXPECTED = "[EXPECTED]"


@allow_storage
@dataclass
class Execution:
    proposal_id: str
    proposer: Address
    summary: str
    status: str
    started_at: u256
    finalized_at: u256


class GovernedExecutor(gl.Contract):
    """Example downstream sink that only finalizes after permit consumption."""

    constitution_guard: str
    executions: TreeMap[str, Execution]
    execution_order: DynArray[str]

    def __init__(self, constitution_guard: Address):
        self.constitution_guard = self._address_text(constitution_guard)

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _address_text(self, value) -> str:
        try:
            return value.as_hex.lower()
        except AttributeError:
            return str(value).strip().lower()

    def _guard(self):
        return gl.get_contract_at(Address(self.constitution_guard))

    def _get_execution(self, proposal_id: str) -> Execution:
        if proposal_id not in self.executions:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Execution not found")
        return self.executions[proposal_id]

    @gl.public.write
    def start_execution(self, proposal_id: str) -> None:
        if not proposal_id or len(proposal_id) > 100:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Invalid proposal ID")
        if proposal_id in self.executions:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Execution already started")
        caller = self._address_text(gl.message.sender_address)
        proposal = self._guard().view().get_proposal(proposal_id)
        if self._address_text(proposal["proposer"]) != caller:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Caller is not the proposer")
        if proposal["status"] != "approved" or proposal["consumed"]:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} No valid proposal permit")
        if self._address_text(proposal["executor"]) != self._address_text(gl.message.contract_address):
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Executor is not bound to proposal")
        self.executions[proposal_id] = Execution(
            proposal_id=proposal_id,
            proposer=Address(self._address_text(proposal["proposer"])),
            summary=proposal["execution_summary"],
            status="awaiting_permit",
            started_at=self._now(),
            finalized_at=0,
        )
        self.execution_order.append(proposal_id)
        self._guard().emit(on="finalized").consume_permit(proposal_id)

    @gl.public.write
    def finalize_execution(self, proposal_id: str) -> None:
        execution = self._get_execution(proposal_id)
        if execution.status != "awaiting_permit":
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Execution is not pending")
        proposal = self._guard().view().get_proposal(proposal_id)
        if proposal["status"] != "permit_consumed" or not proposal["consumed"]:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Permit has not been consumed")
        execution.status = "executed"
        execution.finalized_at = self._now()

    @gl.public.view
    def get_execution(self, proposal_id: str) -> dict:
        execution = self._get_execution(proposal_id)
        return {
            "proposal_id": execution.proposal_id,
            "proposer": execution.proposer.as_hex,
            "summary": execution.summary,
            "status": execution.status,
            "started_at": execution.started_at,
            "finalized_at": execution.finalized_at,
        }


