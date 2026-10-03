from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from prompt_action.data.repository import SaveResult, VersionRepository
from prompt_action.domain.errors import ReleasePlanError, ValidationBlockedError
from prompt_action.domain.ids import next_revision_id, next_snapshot_id, parse_snapshot_id
from prompt_action.domain.models import ValidationReport
from prompt_action.domain.validation import sha256_file

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class PlannedRevision:
    prompt_id: str
    role: str
    from_revision: str
    to_revision: str
    file: str | None
    sha256: str | None
    file_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id, "role": self.role,
            "from": self.from_revision, "to": self.to_revision,
            "file": self.file, "sha256": self.sha256,
            "file_available": self.file_available,
        }


@dataclass(frozen=True, slots=True)
class ReleasePlan:
    expected_app_data_revision: int
    app_version: str
    system: str
    parent_snapshot: str
    snapshot_id: str
    primary: PlannedRevision
    sync: tuple[PlannedRevision, ...]
    prompt_state: dict[str, str]
    committable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_app_data_revision": self.expected_app_data_revision,
            "app_version": self.app_version,
            "system": self.system,
            "parent_snapshot": self.parent_snapshot,
            "snapshot_id": self.snapshot_id,
            "primary": self.primary.to_dict(),
            "sync": [item.to_dict() for item in self.sync],
            "prompt_state": dict(self.prompt_state),
            "committable": self.committable,
            "resulting_status": "BACKUP_REQUIRED",
        }


class VersionEngine:
    def __init__(self, repository: VersionRepository):
        self.repository = repository

    def validate_all(self) -> ValidationReport:
        return self.repository.validate(self.repository.load())

    def _document(self) -> dict[str, Any]:
        state = self.repository.load()
        report = self.repository.validate(state)
        if not report.is_valid:
            raise ValidationBlockedError("Current canonical state is invalid")
        return state.document

    def get_active_context(self) -> dict[str, Any]:
        doc = self._document()
        snapshot = next(item for item in doc["snapshots"] if item["id"] == doc["active_snapshot"])
        system = next(item for item in doc["systems"] if item["id"] == doc["active_system"])
        return {
            "app_version": doc["app_version"],
            "app_data_revision": doc["app_data_revision"],
            "system": deepcopy(system),
            "snapshot": deepcopy(snapshot),
        }

    def get_system_history(self) -> list[dict[str, Any]]:
        doc = self._document()
        return sorted((deepcopy(x) for x in doc["systems"]), key=lambda x: int(x["id"][1:]))

    def get_snapshot_chain(self, system: str) -> list[dict[str, Any]]:
        doc = self._document()
        return sorted(
            (deepcopy(x) for x in doc["snapshots"] if x.get("system") == system),
            key=lambda x: parse_snapshot_id(x["id"]),
        )

    def get_prompt_history(self, prompt: str, system: str | None = None) -> list[dict[str, Any]]:
        doc = self._document()
        if prompt not in doc["prompts"]:
            raise KeyError(prompt)
        result=[]
        for rid, rev in doc["prompts"][prompt]["revisions"].items():
            snapshot = next((s for s in doc["snapshots"] if s["id"] == rev["snapshot"]), None)
            if system is None or (snapshot and snapshot.get("system") == system):
                result.append({"revision":rid, **deepcopy(rev)})
        return sorted(result, key=lambda x:int(x["revision"][1:]))

    def compare_revisions(self, prompt: str, a: str, b: str) -> dict[str, Any]:
        doc = self._document()
        revisions = doc["prompts"][prompt]["revisions"]
        if a not in revisions or b not in revisions:
            raise KeyError(f"Unknown revision for {prompt}: {a}, {b}")
        left, right = revisions[a], revisions[b]
        return {
            "prompt_id": prompt, "a": a, "b": b,
            "same_sha256": left.get("sha256") == right.get("sha256"),
            "a_record": deepcopy(left), "b_record": deepcopy(right),
        }

    def _verify_active_source(self, document: dict[str, Any], prompt_id: str, revision_id: str, revision: dict[str, Any]) -> None:
        if revision.get("file_available") is True:
            file_value = revision.get("file")
            if not isinstance(file_value, str):
                raise ReleasePlanError(f"Active source {prompt_id}:{revision_id} has no physical path")
            path=(self.repository.project_root/file_value).resolve()
            try: path.relative_to(self.repository.project_root)
            except ValueError as exc: raise ReleasePlanError("Active source path escapes project root") from exc
            if not path.is_file() or sha256_file(path) != revision.get("sha256"):
                raise ReleasePlanError(f"Active source {prompt_id}:{revision_id} failed file/hash verification")
            return
        integrity=document.get("integrity",{})
        protected=integrity.get("protected_prompt_hashes",{}) if isinstance(integrity,dict) else {}
        sha=revision.get("sha256")
        is_verified_baseline=(
            revision.get("change_role")=="BASELINE" and
            integrity.get("baseline_verification")=="STEP_00_PASS" and
            isinstance(sha,str) and _SHA_RE.fullmatch(sha) is not None and
            protected.get(prompt_id)==sha
        )
        if not is_verified_baseline:
            raise ReleasePlanError(
                f"Active source {prompt_id}:{revision_id} is not materialized and is not a verified STEP 00 baseline"
            )

    @staticmethod
    def _normalize_change(change: Any) -> tuple[str, str | None]:
        if isinstance(change, str): return change, None
        if isinstance(change, dict) and isinstance(change.get("prompt_id"), str):
            file_value=change.get("file")
            if file_value is not None and not isinstance(file_value,str):
                raise ReleasePlanError("Change file must be a project-relative string or null")
            return change["prompt_id"], file_value
        raise ReleasePlanError("Each change must be a prompt ID or {prompt_id,file} object")

    def plan_release(self, change_set: dict[str, Any]) -> ReleasePlan:
        doc=self._document()
        primary_raw=change_set.get("primary")
        primary_id, primary_file=self._normalize_change(primary_raw)
        sync_raw=change_set.get("sync",[]) or []
        if not isinstance(sync_raw,list): raise ReleasePlanError("sync must be a list")
        sync_pairs=[self._normalize_change(item) for item in sync_raw]
        ids=[primary_id]+[p for p,_ in sync_pairs]
        if len(set(ids)) != len(ids): raise ReleasePlanError("PRIMARY/SYNC prompt IDs must be unique")
        if any(pid not in doc["prompts"] for pid in ids): raise ReleasePlanError("Change set references unknown prompt")
        system=doc["active_system"]; parent_id=doc["active_snapshot"]
        parent=next(x for x in doc["snapshots"] if x["id"]==parent_id)
        existing_snapshots=[x["id"] for x in doc["snapshots"] if x.get("system")==system]
        snapshot_id=next_snapshot_id(existing_snapshots)
        next_state=deepcopy(parent["prompt_state"])

        def plan_one(pid: str, role: str, file_value: str | None) -> PlannedRevision:
            prompt=doc["prompts"][pid]; from_rev=prompt["active_revision"]
            active=prompt["revisions"][from_rev]
            self._verify_active_source(doc,pid,from_rev,active)
            to_rev=next_revision_id(list(prompt["revisions"]))
            file_available=False; digest=None; relative=None
            if file_value:
                candidate=(self.repository.project_root/file_value).resolve()
                try: relative=str(candidate.relative_to(self.repository.project_root)).replace('\\','/')
                except ValueError as exc: raise ReleasePlanError(f"Candidate for {pid} escapes project root") from exc
                if not candidate.is_file(): raise ReleasePlanError(f"Candidate file for {pid} does not exist: {file_value}")
                digest=sha256_file(candidate); file_available=True
                if digest == active.get("sha256"):
                    raise ReleasePlanError(f"Candidate bytes for {pid} are unchanged; revision must not increase")
            next_state[pid]=to_rev
            return PlannedRevision(pid,role,from_rev,to_rev,relative,digest,file_available)

        primary=plan_one(primary_id,"PRIMARY",primary_file)
        sync=tuple(plan_one(pid,"SYNC",file_value) for pid,file_value in sync_pairs)
        committable=all(x.file_available for x in (primary,*sync))
        return ReleasePlan(doc["app_data_revision"],doc["app_version"],system,parent_id,snapshot_id,primary,sync,next_state,committable)

    def commit_release(self, plan: ReleasePlan) -> SaveResult:
        if not plan.committable:
            raise ReleasePlanError("Release plan is preview-only because one or more target revision files are unavailable")
        current=self.repository.load(); doc=deepcopy(current.document)
        if current.app_data_revision != plan.expected_app_data_revision:
            raise ReleasePlanError("Canonical state changed after planning")
        if doc["app_version"] != plan.app_version or doc["active_system"] != plan.system or doc["active_snapshot"] != plan.parent_snapshot:
            raise ReleasePlanError("Active context changed after planning")
        changes=(plan.primary,*plan.sync)
        for item in changes:
            prompt=doc["prompts"][item.prompt_id]
            if prompt["active_revision"] != item.from_revision:
                raise ReleasePlanError(f"Active revision changed after planning for {item.prompt_id}")
            prompt["revisions"][item.from_revision]["status"]="SUPERSEDED"
            prompt["revisions"][item.to_revision]={
                "parent":item.from_revision,"snapshot":plan.snapshot_id,"status":"ACTIVE",
                "file":item.file,"sha256":item.sha256,"file_available":True,
                "change_role":item.role,"summary":[f"Released as {item.role} change in {plan.snapshot_id}."],
                "reason":"Committed from validated STEP 02 release plan."
            }
            prompt["active_revision"]=item.to_revision
        doc["snapshots"].append({
            "id":plan.snapshot_id,"system":plan.system,"parent_snapshot":plan.parent_snapshot,
            "status":"BACKUP_REQUIRED",
            "primary_change":{"prompt_id":plan.primary.prompt_id,"from":plan.primary.from_revision,"to":plan.primary.to_revision},
            "sync_changes":[{"prompt_id":x.prompt_id,"from":x.from_revision,"to":x.to_revision} for x in plan.sync],
            "prompt_state":deepcopy(plan.prompt_state),"backup_id":None,
        })
        doc["active_snapshot"]=plan.snapshot_id
        system=next(x for x in doc["systems"] if x["id"]==plan.system); system["latest_snapshot"]=plan.snapshot_id
        doc["app_data_revision"] += 1
        report=self.repository.validate(doc)
        if not report.is_valid:
            raise ValidationBlockedError("Proposed release violates canonical invariants")
        return self.repository.save(doc, expected_revision=plan.expected_app_data_revision)
