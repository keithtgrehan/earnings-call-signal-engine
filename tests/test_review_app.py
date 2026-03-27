from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_app_module(module_name: str):
    module_path = Path(__file__).resolve().parents[1] / "app" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"review_app_{module_name}", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_app_index_renders() -> None:
    server = _load_app_module("server")
    app = server.create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Earnings Call Review Lab" in text
    assert "Deterministic only" in text
    assert "Run the existing deterministic pipeline" in text


def test_site_app_index_renders() -> None:
    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Earnings Call Signal Engine" in text
    assert "Evidence-backed reviewer workspace" in text
    assert "Raw source vs extracted signal" in text
    assert "Netflix Q1 2022" in text
    assert "Meta Platforms" in text
    assert "Q3 2022" in text
    assert "NVIDIA" in text
    assert 'action="/analyze"' in text
    assert 'name="view_mode" value="input"' in text


def test_site_app_direct_demo_urls_render_expected_cases() -> None:
    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    expected = {
        "netflix_q1_2022": "Netflix Q1 2022",
        "meta_q3_2022": "Meta Q3 2022",
        "nvidia_q4_fy2024": "NVIDIA Q4 FY24",
    }

    for case_id, expected_title in expected.items():
        response = client.get(f"/?mode=demo&demo_case={case_id}")

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert expected_title in text
        assert f'value="{case_id}" selected' in text
        assert "Raw source vs extracted signal" in text


def test_site_app_demo_mode_get_does_not_start_analysis(monkeypatch) -> None:
    import earnings_call_sentiment.web_backend as web_backend

    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    def fail_prepare(*args, **kwargs):
        raise AssertionError("demo GET should not prepare a live run")

    monkeypatch.setattr(web_backend, "prepare_review_run", fail_prepare)

    response = client.get("/?mode=demo&demo_case=meta_q3_2022")

    assert response.status_code == 200
    assert "Meta Q3 2022" in response.get_data(as_text=True)


def test_site_app_analyze_error_keeps_demo_load_on_index_and_input_mode() -> None:
    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    response = client.post(
        "/analyze",
        data={
            "source_mode": "document",
            "selected_demo_case": "nvidia_q4_fy2024",
            "view_mode": "demo",
            "document_text": "",
        },
    )

    assert response.status_code == 400
    text = response.get_data(as_text=True)
    assert 'form class="demo-picker" method="get" action="/"' in text
    assert 'action="/analyze"' in text
    assert 'name="view_mode" value="input"' in text
    assert "Real input review" in text
    assert "Raw source vs extracted signal" not in text
    assert 'value="nvidia_q4_fy2024" selected' in text


def test_site_app_input_mode_renders_history() -> None:
    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    response = client.get("/?mode=input")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Recent local runs" in text
    assert "Real input review" in text


def test_site_app_review_route_preserves_selected_demo_case_for_history_view(tmp_path: Path) -> None:
    from earnings_call_sentiment.web_backend import create_review_app

    project_root = Path(__file__).resolve().parents[1]
    output_root = tmp_path / "outputs"
    app = create_review_app(
        template_dir=project_root / "app" / "templates",
        static_dir=project_root / "app" / "static",
        repo_root=project_root,
        output_root=output_root,
    )
    client = app.test_client()

    run_dir = output_root / "demo-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_meta.json").write_text('{"symbol":"DEMO","event_dt":"2026-03-27T10:00:00+01:00"}', encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "report.md").write_text("# Report", encoding="utf-8")

    response = client.get("/review/demo-run?mode=input&demo_case=nvidia_q4_fy2024")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'value="nvidia_q4_fy2024" selected' in text
    assert "Current run outputs" in text


def test_site_app_serves_demo_case_artifact() -> None:
    site_server = _load_app_module("site_server")
    app = site_server.create_app()
    client = app.test_client()

    response = client.get("/demo-cases/netflix_q1_2022/demo/evidence_rows/netflix_q1_2022_evidence_rows.json")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "transcript_growth_headwinds" in text


def test_site_app_demo_case_with_missing_optional_audio_still_renders(tmp_path: Path) -> None:
    from earnings_call_sentiment.web_backend import create_review_app

    repo_root = tmp_path
    case_id = "demo_case"
    case_root = repo_root / "data" / "demo_cases" / case_id
    (case_root / "demo" / "fixtures").mkdir(parents=True)
    (case_root / "demo" / "summary").mkdir(parents=True)
    (case_root / "demo" / "evidence_rows").mkdir(parents=True)

    fixture = {
        "case_id": case_id,
        "company": "Demo Co",
        "quarter": "Q1 2026",
        "case_status": "ready",
        "preview_row_ids": ["row_1"],
        "notes": ["Transcript-first demo fixture."],
        "artifact_paths": {
            "summary": "demo/summary/demo_case_summary.json",
            "market_context": "demo/summary/demo_case_market_context.json",
            "evidence_rows": "demo/evidence_rows/demo_case_evidence_rows.json",
            "joined_qa_audio_review": "processed/joined_review/joined_qa_audio_review.json",
        },
    }
    summary = {
        "display_name": "Demo Co Q1 2026",
        "headline_counts": {"audio_review_moments": 0},
        "top_summary_points": ["Transcript-first package ready."],
        "limitations": ["Audio support is unavailable for this case."],
    }
    market_context = {
        "panel_title": "Market context",
        "key_extracted_signals": ["Prepared remarks stayed cautious."],
        "market_reaction_window": {
            "start_date": "2026-01-01",
            "end_date": "2026-01-02",
            "reaction_magnitude_pct": -0.4,
        },
        "market_reaction_note": "Context only.",
        "source": {"primary_url": "", "secondary_url": ""},
        "caveat": "Contextual sanity-check evidence only.",
    }
    evidence_rows = {
        "rows": [
            {
                "row_id": "row_1",
                "case_id": case_id,
                "source_type": "transcript",
                "source_excerpt": "We remain cautious.",
                "source_section_or_speaker": "Prepared remarks",
                "extracted_signal": "Management used cautious language.",
                "plain_english_label": "Cautious language",
                "why_it_matters": "Supports a conservative read.",
                "ambiguity_note": "No formal withdrawal language is present.",
                "review_priority": "high",
                "has_audio_support": False,
                "audio_row_id": "",
                "audio_summary": "",
                "optional_timestamp": "",
                "display_order": 1,
            }
        ]
    }

    (case_root / "demo" / "fixtures" / f"{case_id}_fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    (case_root / "demo" / "summary" / "demo_case_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (case_root / "demo" / "summary" / "demo_case_market_context.json").write_text(
        json.dumps(market_context),
        encoding="utf-8",
    )
    (case_root / "demo" / "evidence_rows" / "demo_case_evidence_rows.json").write_text(
        json.dumps(evidence_rows),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    app = create_review_app(
        template_dir=project_root / "app" / "templates",
        static_dir=project_root / "app" / "static",
        repo_root=repo_root,
    )
    client = app.test_client()

    response = client.get(f"/?mode=demo&demo_case={case_id}")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Demo Co" in text
    assert "Audio support not available for this case." in text


def test_review_app_document_post_uses_review_workflow(monkeypatch, tmp_path: Path) -> None:
    import earnings_call_sentiment.web_backend as web_backend
    from earnings_call_sentiment.review_workflow import ReviewRun

    server = _load_app_module("server")
    app = server.create_app()
    review_run = ReviewRun(
        run_id="demo-run",
        cache_dir=tmp_path / "cache",
        out_dir=tmp_path / "outputs",
        input_dir=tmp_path / "outputs" / "inputs",
    )
    review_run.input_dir.mkdir(parents=True, exist_ok=True)
    review_run.out_dir.mkdir(parents=True, exist_ok=True)

    called: dict[str, object] = {}

    def fake_prepare_review_run(*, repo_root, source_label, cache_base=None, out_base=None):
        called["source_label"] = source_label
        return review_run

    def fake_run_document_review(**kwargs):
        called["document_text"] = kwargs["text"]
        (review_run.out_dir / "metrics.json").write_text("{}", encoding="utf-8")
        (review_run.out_dir / "report.md").write_text("# Report", encoding="utf-8")
        (review_run.out_dir / "transcript.txt").write_text("text", encoding="utf-8")
        return {"run_id": review_run.run_id}

    def fake_load_artifact_bundle(arg):
        assert arg == review_run
        return {
            "run_id": review_run.run_id,
            "out_dir": str(review_run.out_dir),
            "artifacts": {"metrics.json": str(review_run.out_dir / 'metrics.json')},
            "tables": {},
            "json": {"metrics.json": {"sentiment_mean": 0.0}},
            "text": {"report.md": "# Report", "transcript.txt": "text"},
        }

    def fake_start_review_job(*, review_run, form_state, payload):
        fake_run_document_review(text=payload["document_text"])
        web_backend._set_job_state(
            review_run.run_id,
            status="complete",
            finished_at="2026-03-11T09:05:00",
        )

    monkeypatch.setattr(web_backend, "prepare_review_run", fake_prepare_review_run)
    monkeypatch.setattr(web_backend, "load_artifact_bundle", fake_load_artifact_bundle)
    monkeypatch.setattr(web_backend, "_start_review_job", fake_start_review_job)

    client = app.test_client()
    response = client.post(
        "/analyze",
        data={
            "source_mode": "document",
            "analysis_mode": "deterministic",
            "symbol": "TEST",
            "event_dt": "2026-03-11T09:00:00-05:00",
            "document_text": "We raised revenue guidance for the year.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["Location"].startswith("/review/demo-run")
    assert "mode=input" in response.headers["Location"]

    review_response = client.get("/review/demo-run")
    assert review_response.status_code == 200
    text = review_response.get_data(as_text=True)
    assert "demo-run" in text
    assert called["document_text"] == "We raised revenue guidance for the year."
