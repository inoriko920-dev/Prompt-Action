from __future__ import annotations

from pathlib import Path

import pytest

from prompt_action.domain.errors import ReleaseWorkflowError
from prompt_action.services.release_recovery import ReleaseRecoveryService
from prompt_action.services.release_service import ReleaseService


def test_partial_primary_placement_cannot_be_false_aborted(
    project: Path,
    changed_p3: Path,
    changed_p4: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    service = ReleaseService(project)
    plan = service.plan_release(
        primary_prompt_id="P3",
        primary_source=changed_p3,
        sync=[{"prompt_id": "P4", "source": str(changed_p4), "reason": "compatibility sync"}],
        reason="partial placement failure injection",
    )
    original = service.release_repository.place_new_file
    calls = {"count": 0}

    def fail_second(target, payload, expected_sha256):
        calls["count"] += 1
        if calls["count"] == 2:
            raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", "injected second placement failure")
        return original(target, payload, expected_sha256)

    monkeypatch.setattr(service.release_repository, "place_new_file", fail_second)
    with pytest.raises(ReleaseWorkflowError) as exc_info:
        service.commit_release(plan, plan.confirmation_token)
    assert exc_info.value.code == "RECOVERY_REQUIRED"

    recovery = ReleaseRecoveryService(project)
    pending = recovery.inspect_pending_transaction()
    assert pending is not None
    assert pending.phase == "RECOVERY_REQUIRED"
    assert (project / plan.primary.target_relative).is_file()
    assert not (project / plan.sync[0].target_relative).exists()

    result = recovery.recover_transaction(pending.txn_id, "abort")
    assert result.phase == "ABORTED"
    assert not (project / plan.primary.target_relative).exists()
    assert not (project / plan.sync[0].target_relative).exists()
