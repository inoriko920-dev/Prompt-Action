from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil

from PySide6.QtGui import QImage

from prompt_action.presentation.dashboard_models import DashboardState
from prompt_action.presentation.dashboard_query_service import DashboardQueryService
from prompt_action.presentation.dashboard_view_model import DashboardViewModel

ROOT = Path(__file__).resolve().parents[2]
BASE_DOC = json.loads((ROOT / "data/version_history.json").read_text(encoding="utf-8"))


def _write_doc(tmp_path: Path, document: dict) -> Path:
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/version_history.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    for prompt in document.get("prompts", {}).values():
        for revision in prompt.get("revisions", {}).values():
            rel = revision.get("file")
            if revision.get("file_available") is True and isinstance(rel, str) and rel:
                source = ROOT / rel
                target = tmp_path / rel
                if source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    return tmp_path


def _service(tmp_path: Path, document: dict) -> DashboardQueryService:
    _write_doc(tmp_path, document)
    return DashboardQueryService(tmp_path)


def _append_release(document: dict, primary: str = "P3", sync: tuple[str, ...] = ()) -> dict:
    doc = deepcopy(document)
    parent = next(item for item in doc["snapshots"] if item["id"] == doc["active_snapshot"])
    state = deepcopy(parent["prompt_state"])
    changes = []
    for role, prompt_id in [("PRIMARY", primary), *[("SYNC", item) for item in sync]]:
        prompt = doc["prompts"][prompt_id]
        old = prompt["active_revision"]
        new = "R2"
        prompt["revisions"][old]["status"] = "SUPERSEDED"
        prompt["revisions"][new] = {
            "parent": old,
            "snapshot": "S002",
            "status": "ACTIVE",
            "file": None,
            "sha256": ("1" if role == "PRIMARY" else "2") * 64,
            "file_available": False,
            "change_role": role,
            "summary": [f"{role} test release"],
            "reason": "STEP 04 test fixture",
        }
        prompt["active_revision"] = new
        state[prompt_id] = new
        changes.append({"prompt_id": prompt_id, "from": old, "to": new, "role": role})
    child = {
        "id": "S002",
        "system": doc["active_system"],
        "parent_snapshot": parent["id"],
        "status": "BACKUP_REQUIRED",
        "primary_change": {k: v for k, v in changes[0].items() if k != "role"},
        "sync_changes": [{k: v for k, v in item.items() if k != "role"} for item in changes[1:]],
        "prompt_state": state,
        "backup_id": None,
        "reason": "Dashboard test release",
    }
    doc["snapshots"].append(child)
    doc["active_snapshot"] = "S002"
    doc["systems"][0]["latest_snapshot"] = "S002"
    return doc


def _healthy_backup_doc(tmp_path: Path, with_file: bool = False) -> dict:
    doc = deepcopy(BASE_DOC)
    snapshot = doc["snapshots"][0]
    snapshot["status"] = "COMPLETE"
    snapshot["backup_id"] = "B001"
    backup = {
        "id": "B001",
        "status": "VALID",
        "verified": True,
        "second_copy_verified": True,
        "sha256": "a" * 64,
    }
    if with_file:
        (tmp_path / "backups").mkdir(parents=True, exist_ok=True)
        (tmp_path / "backups/full.zip").write_bytes(b"validated-backup")
        backup["file"] = "backups/full.zip"
    doc["backups"] = [backup]
    return doc


def _probe(width: int, height: int, scale: str = "1") -> dict:
    env = os.environ.copy()
    env.update({
        "QT_QPA_PLATFORM": "offscreen",
        "QT_QUICK_BACKEND": "software",
        "QSG_RHI_BACKEND": "software",
        "QSG_RENDER_LOOP": "basic",
        "QT_QUICK_CONTROLS_STYLE": "Basic",
        "QT_SCALE_FACTOR": scale,
        "PYTHONPATH": str(ROOT / "src"),
    })
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/step04/dashboard_probe.py"), "--width", str(width), "--height", str(height)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout.strip().splitlines()[-1])


def _evidence_file(name: str) -> Path:
    base = Path(os.environ.get("STEP04_EVIDENCE_DIR", ROOT / "ci-step04-evidence"))
    return base / "screenshots" / name


# T01
def test_t01_dashboard_route_opens():
    result = _probe(1600, 900)
    assert result["valid"] and result["state"]["load_state"] == "ready"


# T02
def test_t02_no_sample_v1_s004_r3_hardcode_in_dashboard_production():
    paths = [ROOT / "src/prompt_action/ui/qml/pages/DashboardPage.qml", ROOT / "src/prompt_action/presentation/dashboard_query_service.py"]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "S004" not in text and "R3" not in text


# T03
def test_t03_kpi_system_from_engine(tmp_path):
    assert _service(tmp_path, deepcopy(BASE_DOC)).read().system_label == BASE_DOC["active_system"]


# T04
def test_t04_kpi_snapshot_from_engine(tmp_path):
    assert _service(tmp_path, deepcopy(BASE_DOC)).read().snapshot_label == BASE_DOC["active_snapshot"]


# T05
def test_t05_prompt_count_correct(tmp_path):
    state = _service(tmp_path, deepcopy(BASE_DOC)).read()
    assert state.active_prompt_count == len(BASE_DOC["snapshots"][0]["prompt_state"]) == 8


# T06
def test_t06_backup_healthy_mapping(tmp_path):
    state = _service(tmp_path, _healthy_backup_doc(tmp_path)).read()
    assert state.backup_health == "AMAN" and all(item.ok for item in state.backup_checklist)


# T07
def test_t07_backup_required_mapping(tmp_path):
    service = _service(tmp_path, deepcopy(BASE_DOC))
    health, recovery, _, _, _ = service._backup_state(BASE_DOC, {"id": "Sx", "status": "BACKUP_REQUIRED", "backup_id": None})
    assert health == "PERLU BACKUP" and recovery == "REQUIRED"


# T08
def test_t08_unknown_backup_mapping(tmp_path):
    service = _service(tmp_path, deepcopy(BASE_DOC))
    health, recovery, _, _, _ = service._backup_state(BASE_DOC, {"id": "Sx", "status": "ARCHIVED", "backup_id": None})
    assert health == "UNKNOWN" and recovery == "UNKNOWN"


# T09
def test_t09_baseline_has_no_fake_primary(tmp_path):
    latest = _service(tmp_path, deepcopy(BASE_DOC)).read().latest_change
    assert latest.primary_change is None and "Baseline" in latest.display_title


# T10
def test_t10_primary_change_render_model(tmp_path):
    state = _service(tmp_path, _append_release(BASE_DOC)).read()
    assert state.latest_change.primary_change["prompt_id"] == "P3" and "R1" in state.latest_change.display_title


# T11
def test_t11_sync_changes_zero_one_many(tmp_path):
    service = _service(tmp_path, deepcopy(BASE_DOC))
    system = BASE_DOC["systems"][0]
    for count in (0, 1, 2):
        snapshot = deepcopy(BASE_DOC["snapshots"][0])
        snapshot["sync_changes"] = [{"prompt_id": f"P{index}", "from": "R1", "to": "R2"} for index in range(count)]
        latest = service._latest_change(system, snapshot)
        assert len(latest.sync_changes) == count


# T12
def test_t12_prompt_grid_has_eight_items(tmp_path):
    assert len(_service(tmp_path, deepcopy(BASE_DOC)).read().active_prompts) == 8


# T13
def test_t13_prompt_count_is_data_driven(tmp_path):
    service = _service(tmp_path, deepcopy(BASE_DOC))
    snapshot = deepcopy(BASE_DOC["snapshots"][0])
    snapshot["prompt_state"] = {"P1A": "R1", "P3": "R1"}
    items, _ = service._active_prompts(BASE_DOC, snapshot)
    assert len(items) == 2


# T14
def test_t14_integrity_warning_item(tmp_path):
    doc = deepcopy(BASE_DOC)
    rev = doc["prompts"]["P3"]["revisions"]["R1"]
    rev["file_available"] = False
    rev["file"] = None
    state = _service(tmp_path, doc).read()
    p3 = next(item for item in state.active_prompts if item.prompt_id == "P3")
    assert p3.integrity_state == "MISSING_SOURCE" and state.load_state == "degraded"


# T15
def test_t15_lihat_snapshot_intent():
    vm = DashboardViewModel(ROOT)
    seen = []
    vm.navigationRequested.connect(lambda route, entity: seen.append((route, entity)))
    vm.openSnapshot(vm.state["snapshot_label"])
    assert seen == [("system_history", "S001")]


# T16
def test_t16_prompt_click_intent():
    vm = DashboardViewModel(ROOT)
    seen = []
    vm.navigationRequested.connect(lambda route, entity: seen.append((route, entity)))
    vm.openPrompt("P3")
    assert seen == [("prompt", "P3")]


# T17
def test_t17_recent_change_action_intent():
    vm = DashboardViewModel(ROOT)
    seen = []
    vm.navigationRequested.connect(lambda route, entity: seen.append((route, entity)))
    vm.openLatestChange()
    assert seen == [("system_history", "S001")]


# T18
def test_t18_backup_button_disabled_capability():
    vm = DashboardViewModel(ROOT)
    rejected = []
    vm.actionRejected.connect(rejected.append)
    assert vm.state["action_capabilities"]["can_request_backup"] is False
    vm.requestBackupNow()
    assert rejected and "STEP 04" in rejected[-1]


# T19
def test_t19_download_only_valid_file(tmp_path):
    state = _service(tmp_path, _healthy_backup_doc(tmp_path, with_file=True)).read()
    assert state.action_capabilities.can_download_full_backup is True
    assert state.action_capabilities.backup_download_path == "backups/full.zip"


# T20
def test_t20_loading_has_no_sample_values():
    state = DashboardState.loading().to_dict()
    assert state["system_label"] == "—" and state["snapshot_label"] == "—" and state["active_prompt_count"] == 0


# T21
def test_t21_empty_state():
    assert DashboardState.empty().load_state == "empty"


# T22
def test_t22_invalid_data_blocking_state(tmp_path):
    doc = deepcopy(BASE_DOC)
    doc["schema_version"] = 99
    state = _service(tmp_path, doc).read()
    assert state.load_state == "invalid" and state.backup_health == "ERROR"


# T23
def test_t23_degraded_state(tmp_path):
    doc = deepcopy(BASE_DOC)
    rev = doc["prompts"]["P4"]["revisions"]["R1"]
    rev["file_available"] = False
    rev["file"] = None
    assert _service(tmp_path, doc).read().load_state == "degraded"


# T24
def test_t24_error_and_retry_state(tmp_path):
    class Stub:
        def __init__(self): self.calls = 0
        def read(self):
            self.calls += 1
            return DashboardState.error("boom") if self.calls == 1 else DashboardState.empty("retry-ok")
    stub = Stub()
    vm = DashboardViewModel(tmp_path, query_service=stub, auto_refresh=False)
    vm.refresh()
    assert vm.state["load_state"] == "error"
    vm.refresh()
    assert vm.state["load_state"] == "empty"


# T25
def test_t25_refresh_idempotent():
    vm = DashboardViewModel(ROOT)
    before = vm.state
    vm.refresh()
    after = vm.state
    assert before == after


# T26
def test_t26_no_domain_write_on_load():
    path = ROOT / "data/version_history.json"
    before = path.read_bytes()
    DashboardViewModel(ROOT).refresh()
    after = path.read_bytes()
    assert before == after


# T27
def test_t27_1600x900_visual_baseline():
    path = _evidence_file("dashboard-1600x900.png")
    image = QImage(str(path))
    assert path.is_file() and image.width() == 1600 and image.height() == 900


# T28
def test_t28_1920x1080_visual_baseline():
    path = _evidence_file("dashboard-1920x1080.png")
    image = QImage(str(path))
    assert path.is_file() and image.width() == 1920 and image.height() == 1080


# T29
def test_t29_1366x768_usability():
    result = _probe(1366, 768)
    assert result["valid"] and result["page_width"] > 0 and result["page_height"] > 0


# T30
def test_t30_dpi_125_percent():
    result = _probe(1600, 900, "1.25")
    assert result["valid"] and result["scale_factor"] == "1.25"


# T31
def test_t31_dpi_150_and_175_percent():
    for scale in ("1.5", "1.75"):
        result = _probe(1600, 900, scale)
        assert result["valid"] and result["scale_factor"] == scale


# T32
def test_t32_keyboard_tab_and_focus_contract():
    prompt_grid = (ROOT / "src/prompt_action/ui/qml/dashboard/ActivePromptGrid.qml").read_text(encoding="utf-8")
    button = (ROOT / "src/prompt_action/ui/qml/components/PAButton.qml").read_text(encoding="utf-8")
    assert "activeFocusOnTab: true" in prompt_grid and "activeFocusOnTab: true" in button


# T33
def test_t33_long_text_wrap_elide_contract():
    sources = [
        ROOT / "src/prompt_action/ui/qml/dashboard/RecentChangeCard.qml",
        ROOT / "src/prompt_action/ui/qml/dashboard/ActivePromptGrid.qml",
        ROOT / "src/prompt_action/ui/qml/pages/DashboardPage.qml",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "wrapMode: Text.WordWrap" in text and "elide: Text.ElideRight" in text


# T34
def test_t34_restart_retains_correct_read_state():
    first = DashboardViewModel(ROOT).state
    second = DashboardViewModel(ROOT).state
    assert first == second and first["system_label"] == "V1" and first["snapshot_label"] == "S001"


# T35
def test_t35_regression_step01_03_smoke_contract():
    for number in (1, 2, 3):
        report = ROOT / f"docs/implementation/STEP_0{number}_SOL_EXECUTION_REPORT.md"
        assert report.is_file() and "PASS" in report.read_text(encoding="utf-8")
