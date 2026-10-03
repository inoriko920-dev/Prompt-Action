from __future__ import annotations

import re
from typing import Any, Iterable

from .ids import parse_revision_id, parse_snapshot_id, parse_system_id
from .models import Severity, ValidationReport


def _index_unique(items: Iterable[dict[str, Any]], *, id_key: str, entity_kind: str, report: ValidationReport) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        path = f"{entity_kind}[{index}]"
        if not isinstance(item, dict):
            report.add("SCHEMA-ENTITY-TYPE", Severity.BLOCKING, entity_kind, path, "Entity must be an object.")
            continue
        entity_id = item.get(id_key)
        if not isinstance(entity_id, str) or not entity_id:
            report.add("SCHEMA-ENTITY-ID", Severity.BLOCKING, entity_kind, f"{path}.{id_key}", "Entity ID must be a non-empty string.")
            continue
        if entity_id in result:
            report.add("REF-DUPLICATE-ID", Severity.BLOCKING, entity_id, path, f"Duplicate {entity_kind} ID: {entity_id}")
            continue
        result[entity_id] = item
    return result


def _detect_snapshot_cycles(snapshots: dict[str, dict[str, Any]], report: ValidationReport) -> None:
    for start in snapshots:
        seen: set[str] = set()
        current: str | None = start
        while current is not None and current in snapshots:
            if current in seen:
                report.add("GRAPH-SNAPSHOT-CYCLE", Severity.BLOCKING, start, f"snapshots.{start}.parent_snapshot", "Snapshot parent graph contains a cycle.")
                break
            seen.add(current)
            parent = snapshots[current].get("parent_snapshot")
            current = parent if isinstance(parent, str) else None


def _detect_revision_cycles(prompt_id: str, revisions: dict[str, Any], report: ValidationReport) -> None:
    for start in revisions:
        seen: set[str] = set()
        current: str | None = start
        while current is not None and current in revisions:
            if current in seen:
                report.add("GRAPH-REVISION-CYCLE", Severity.BLOCKING, f"{prompt_id}:{start}", f"prompts.{prompt_id}.revisions.{start}.parent", "Revision parent graph contains a cycle.")
                break
            seen.add(current)
            revision = revisions[current]
            parent = revision.get("parent") if isinstance(revision, dict) else None
            current = parent if isinstance(parent, str) else None


def _validate_change_record(snapshot_id: str, path_suffix: str, change: dict[str, Any], parent_state: dict[str, Any], child_state: dict[str, Any], report: ValidationReport) -> None:
    pid = change.get("prompt_id")
    if pid not in parent_state or pid not in child_state:
        report.add("REF-CHANGE-PROMPT", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.{path_suffix}.prompt_id", "Change references a Prompt not present in the Snapshot state.")
        return
    if change.get("from") != parent_state.get(pid):
        report.add("INV-07", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.{path_suffix}.from", f"Declared from={change.get('from')!r}; parent state is {parent_state.get(pid)!r}.")
    if change.get("to") != child_state.get(pid):
        report.add("INV-08", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.{path_suffix}.to", f"Declared to={change.get('to')!r}; child state is {child_state.get(pid)!r}.")


def validate_references_graph_domain(document: dict[str, Any], report: ValidationReport) -> None:
    systems = _index_unique(document.get("systems", []), id_key="id", entity_kind="systems", report=report)
    snapshots = _index_unique(document.get("snapshots", []), id_key="id", entity_kind="snapshots", report=report)
    _index_unique(document.get("backups", []), id_key="id", entity_kind="backups", report=report)
    prompts = document.get("prompts", {}) if isinstance(document.get("prompts"), dict) else {}

    active_systems: list[str] = []
    for system_id, system in systems.items():
        try:
            parse_system_id(system_id)
        except ValueError as exc:
            report.add("SCHEMA-SYSTEM-ID", Severity.BLOCKING, system_id, f"systems.{system_id}.id", str(exc))
        if system.get("status") == "ACTIVE":
            active_systems.append(system_id)
        parent_system = system.get("parent_system")
        if parent_system is not None and parent_system not in systems:
            report.add("REF-SYSTEM-PARENT", Severity.BLOCKING, system_id, f"systems.{system_id}.parent_system", "parent_system does not exist.")
        if system.get("generation_reason") == "PROMPT_REVISION_ONLY":
            report.add("INV-13", Severity.BLOCKING, system_id, f"systems.{system_id}.generation_reason", "A new System cannot be created only because one prompt revision changed.")
    if len(active_systems) != 1:
        report.add("INV-01", Severity.BLOCKING, "systems", "systems[*].status", f"Exactly one ACTIVE System is required; found {len(active_systems)}.")

    active_system = document.get("active_system")
    if active_system not in systems:
        report.add("REF-ACTIVE-SYSTEM", Severity.BLOCKING, str(active_system), "active_system", "active_system does not reference an existing System.")
    elif systems[active_system].get("status") != "ACTIVE":
        report.add("INV-01", Severity.BLOCKING, str(active_system), "active_system", "active_system must point to the ACTIVE System.")

    snapshots_by_system: dict[str, list[str]] = {}
    for snapshot_id, snapshot in snapshots.items():
        try:
            parse_snapshot_id(snapshot_id)
        except ValueError as exc:
            report.add("SCHEMA-SNAPSHOT-ID", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.id", str(exc))
        system_id = snapshot.get("system")
        if system_id not in systems:
            report.add("REF-SNAPSHOT-SYSTEM", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.system", "Snapshot references a missing System.")
        elif isinstance(system_id, str):
            snapshots_by_system.setdefault(system_id, []).append(snapshot_id)
        parent = snapshot.get("parent_snapshot")
        if parent is not None:
            if parent not in snapshots:
                report.add("INV-03", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.parent_snapshot", "Non-baseline snapshot parent does not exist.")
            else:
                if snapshots[parent].get("system") != system_id:
                    report.add("REF-SNAPSHOT-PARENT-SYSTEM", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.parent_snapshot", "Snapshot parent must belong to the same System.")
                try:
                    if parse_snapshot_id(parent) >= parse_snapshot_id(snapshot_id):
                        report.add("INV-04", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.parent_snapshot", "Snapshot ID must increase monotonically after its parent.")
                except ValueError:
                    pass
        prompt_state = snapshot.get("prompt_state")
        if not isinstance(prompt_state, dict):
            report.add("SCHEMA-PROMPT-STATE", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.prompt_state", "Snapshot prompt_state must be an object.")
        elif set(prompt_state) != set(prompts):
            report.add("REF-PROMPT-STATE-COVERAGE", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.prompt_state", "Snapshot prompt_state must contain exactly all canonical prompt IDs.")

    _detect_snapshot_cycles(snapshots, report)

    active_snapshot = document.get("active_snapshot")
    if active_snapshot not in snapshots:
        report.add("INV-02", Severity.BLOCKING, str(active_snapshot), "active_snapshot", "active_snapshot does not exist.")
    else:
        snapshot = snapshots[active_snapshot]
        if snapshot.get("system") != active_system:
            report.add("INV-02", Severity.BLOCKING, str(active_snapshot), "active_snapshot", "active_snapshot must belong to active_system.")
        if snapshot.get("status") == "DRAFT":
            report.add("INV-12", Severity.BLOCKING, str(active_snapshot), "active_snapshot", "A DRAFT snapshot cannot become active.")

    for system_id, system in systems.items():
        first_snapshot = system.get("first_snapshot")
        latest_snapshot = system.get("latest_snapshot")
        for field, value in (("first_snapshot", first_snapshot), ("latest_snapshot", latest_snapshot)):
            if value not in snapshots or snapshots.get(value, {}).get("system") != system_id:
                report.add("REF-SYSTEM-SNAPSHOT", Severity.BLOCKING, system_id, f"systems.{system_id}.{field}", f"{field} must reference a Snapshot in the same System.")
        ids = snapshots_by_system.get(system_id, [])
        if ids:
            try:
                minimum = min(ids, key=parse_snapshot_id)
                maximum = max(ids, key=parse_snapshot_id)
                if first_snapshot != minimum:
                    report.add("INV-04", Severity.BLOCKING, system_id, f"systems.{system_id}.first_snapshot", f"first_snapshot should be {minimum}.")
                if latest_snapshot != maximum:
                    report.add("INV-04", Severity.BLOCKING, system_id, f"systems.{system_id}.latest_snapshot", f"latest_snapshot should be {maximum}.")
            except ValueError:
                pass

    for prompt_id, prompt in prompts.items():
        if not isinstance(prompt, dict):
            report.add("SCHEMA-PROMPT", Severity.BLOCKING, prompt_id, f"prompts.{prompt_id}", "Prompt record must be an object.")
            continue
        revisions = prompt.get("revisions")
        if not isinstance(revisions, dict) or not revisions:
            report.add("SCHEMA-REVISIONS", Severity.BLOCKING, prompt_id, f"prompts.{prompt_id}.revisions", "Prompt must contain at least one revision.")
            continue
        for revision_id, revision in revisions.items():
            try:
                parse_revision_id(revision_id)
            except ValueError as exc:
                report.add("SCHEMA-REVISION-ID", Severity.BLOCKING, f"{prompt_id}:{revision_id}", f"prompts.{prompt_id}.revisions.{revision_id}", str(exc))
            if not isinstance(revision, dict):
                report.add("SCHEMA-REVISION", Severity.BLOCKING, f"{prompt_id}:{revision_id}", f"prompts.{prompt_id}.revisions.{revision_id}", "Revision record must be an object.")
                continue
            parent = revision.get("parent")
            if parent is not None and parent not in revisions:
                report.add("REF-REVISION-PARENT", Severity.BLOCKING, f"{prompt_id}:{revision_id}", f"prompts.{prompt_id}.revisions.{revision_id}.parent", "Revision parent does not exist for this Prompt.")
            elif parent is not None:
                try:
                    if parse_revision_id(parent) >= parse_revision_id(revision_id):
                        report.add("INV-05", Severity.BLOCKING, f"{prompt_id}:{revision_id}", f"prompts.{prompt_id}.revisions.{revision_id}.parent", "Revision number must increase after its parent.")
                except ValueError:
                    pass
            revision_snapshot = revision.get("snapshot")
            if revision_snapshot not in snapshots:
                report.add("REF-REVISION-SNAPSHOT", Severity.BLOCKING, f"{prompt_id}:{revision_id}", f"prompts.{prompt_id}.revisions.{revision_id}.snapshot", "Revision snapshot does not exist.")
        _detect_revision_cycles(prompt_id, revisions, report)
        active_revision = prompt.get("active_revision")
        if active_revision not in revisions:
            report.add("REF-ACTIVE-REVISION", Severity.BLOCKING, prompt_id, f"prompts.{prompt_id}.active_revision", "active_revision does not exist.")
        if active_snapshot in snapshots:
            expected = snapshots[active_snapshot].get("prompt_state", {}).get(prompt_id)
            if active_revision != expected:
                report.add("INV-06", Severity.BLOCKING, prompt_id, f"prompts.{prompt_id}.active_revision", f"active_revision={active_revision!r} does not match active snapshot state={expected!r}.")

    for snapshot_id, snapshot in snapshots.items():
        parent_id = snapshot.get("parent_snapshot")
        if parent_id is None or parent_id not in snapshots:
            continue
        parent_state = snapshots[parent_id].get("prompt_state", {})
        child_state = snapshot.get("prompt_state", {})
        if not isinstance(parent_state, dict) or not isinstance(child_state, dict):
            continue
        changed = {pid for pid in prompts if parent_state.get(pid) != child_state.get(pid)}
        declared: set[str] = set()
        primary = snapshot.get("primary_change")
        if isinstance(primary, dict):
            pid = primary.get("prompt_id")
            if isinstance(pid, str):
                declared.add(pid)
            _validate_change_record(snapshot_id, "primary_change", primary, parent_state, child_state, report)
        elif primary is not None:
            report.add("SCHEMA-PRIMARY", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.primary_change", "primary_change must be an object or null.")
        sync_changes = snapshot.get("sync_changes", [])
        if not isinstance(sync_changes, list):
            report.add("SCHEMA-SYNC", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.sync_changes", "sync_changes must be a list.")
            sync_changes = []
        for index, change in enumerate(sync_changes):
            if not isinstance(change, dict):
                report.add("SCHEMA-SYNC", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.sync_changes[{index}]", "SYNC change must be an object.")
                continue
            pid = change.get("prompt_id")
            if isinstance(pid, str):
                if pid in declared:
                    report.add("INV-09", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.sync_changes[{index}]", "A prompt cannot be declared more than once in a snapshot change set.")
                declared.add(pid)
            _validate_change_record(snapshot_id, f"sync_changes[{index}]", change, parent_state, child_state, report)
        if changed != declared:
            report.add("INV-09", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.prompt_state", f"Actual revision changes {sorted(changed)} differ from declared PRIMARY/SYNC {sorted(declared)}.")

    app_version = document.get("app_version")
    if isinstance(app_version, str) and (app_version == document.get("active_system") or app_version == document.get("active_snapshot") or re.fullmatch(r"R[1-9][0-9]*", app_version)):
        report.add("INV-14", Severity.BLOCKING, "root", "app_version", "App Version must remain separate from System/Snapshot/Revision IDs.")
