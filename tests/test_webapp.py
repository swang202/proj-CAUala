"""
Web-layer tests. Offline (offline=true) so they need no network and stay in CI.
Uses the Starlette/FastAPI TestClient bundled with fastapi.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from src.webapp import app  # noqa: E402

client = TestClient(app)


def test_index_serves_form():
    r = client.get("/")
    assert r.status_code == 200
    assert "CAUala" in r.text
    assert 'id="source"' in r.text and 'id="target"' in r.text


def _stream_events(source, target, **kw):
    params = {"source": source, "target": target, "offline": "true", **kw}
    r = client.get("/stream", params=params)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    events = []
    for line in r.text.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line[5:]))
    return events


def test_stream_emits_progress_then_report():
    events = _stream_events("PCSK9", "coronary artery disease")
    stages = [e["stage"] for e in events]
    # the pipeline milestones appear, in order, ending with done
    for expected in ("start", "harmonize", "stack", "assemble", "gate", "classify", "done"):
        assert expected in stages
    assert stages[-1] == "done"
    done = events[-1]
    assert done["verdict"]["tier"] == "causal_driver"
    assert done["verdict"]["archetype"] == "validated_driver"
    assert "<svg" in done["report_html"]  # the report (with spider chart) is delivered


def test_stream_reports_marker_case():
    events = _stream_events("HDL-C", "coronary artery disease")
    done = events[-1]
    assert done["stage"] == "done"
    assert done["verdict"]["tier"] == "refuted"
    assert done["verdict"]["archetype"] == "associated_noncausal"
