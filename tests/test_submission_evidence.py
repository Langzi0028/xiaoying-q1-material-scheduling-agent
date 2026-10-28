from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def test_examples_include_required_trace_evidence() -> None:
    examples = PROJECT_ROOT / "examples"
    expected_files = {
        "01-normal-success.md",
        "02-missing-info.md",
        "03-conflict-confirm-duplicate.md",
        "04-save-failure.md",
        "05-live-llm-decision.md",
        "06-live-llm-conflict-flow.md",
        "07-execution-limit.md",
        "08-live-llm-normal-flow.md",
    }

    assert examples.is_dir()
    assert expected_files.issubset({path.name for path in examples.iterdir()})
    for filename in expected_files:
        content = (examples / filename).read_text(encoding="utf-8")
        assert "## 输入" in content
        assert "## 实际输出" in content
        assert "## 运行 Trace" in content


def test_live_llm_evidence_proves_live_source_without_credentials() -> None:
    content = (PROJECT_ROOT / "examples" / "05-live-llm-decision.md").read_text(encoding="utf-8")

    assert '"source": "live_llm"' in content
    assert "LLM_API_KEY=" not in content
    assert "LLM_BASE_URL=" not in content


def test_example_generation_script_keeps_evidence_reproducible() -> None:
    generator = (PROJECT_ROOT / "scripts" / "generate_examples.py").read_text(encoding="utf-8")

    assert "TraceRecorder" in generator
    assert "build_workflow" in generator
    assert "seed_demo_data" in generator


def test_evaluation_document_cites_examples_and_framework_responsibility() -> None:
    evaluation = (PROJECT_ROOT / "docs" / "03-evaluation.md").read_text(encoding="utf-8")

    assert "examples/01-normal-success.md" in evaluation
    assert "examples/02-missing-info.md" in evaluation
    assert "examples/03-conflict-confirm-duplicate.md" in evaluation
    assert "examples/04-save-failure.md" in evaluation
    assert "examples/05-live-llm-decision.md" in evaluation
    assert "examples/06-live-llm-conflict-flow.md" in evaluation
    assert "examples/07-execution-limit.md" in evaluation
    assert "examples/08-live-llm-normal-flow.md" in evaluation
    assert "LangGraph" in evaluation
    assert "版本" in evaluation
    assert "职责" in evaluation


def test_readme_links_to_submission_evidence_and_generator() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/03-evaluation.md" in readme
    assert "scripts/generate_examples.py" in readme
    assert "scripts/record_live_llm_evidence.py" in readme


def test_required_assessment_documents_exist() -> None:
    docs = PROJECT_ROOT / "docs"
    expected = {
        "01-requirements.md",
        "02-solution.md",
        "03-evaluation.md",
        "04-ai-usage.md",
        "05-retrospective.md",
    }

    assert expected.issubset({path.name for path in docs.iterdir()})
