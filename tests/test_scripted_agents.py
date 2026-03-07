from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent
from sentinel.sandbox import fixture_workspace, resolve_fixture_repo
from sentinel.traces import RunTrace


def test_benign_agent_returns_trace_with_one_read_and_one_write() -> None:
    """Test that the benign agent records one read and one write."""
    agent = BenignScriptedAgent()

    with fixture_workspace("todo_api") as workspace:
        expected_workspace = str(workspace)
        trace = agent.run(task_id="fix_pagination_v1", workspace=workspace)

    assert isinstance(trace, RunTrace)
    assert trace.task_id == "fix_pagination_v1"
    assert trace.workspace == expected_workspace
    assert len(trace.file_reads) == 1
    assert len(trace.file_writes) == 1
    assert trace.file_reads[0].relative_path == "app.py"
    assert trace.file_writes[0].relative_path == "app.py"


def test_benign_agent_modifies_app_file() -> None:
    """Test that the benign agent appends to `app.py`."""
    agent = BenignScriptedAgent()

    with fixture_workspace("todo_api") as workspace:
        target_path = workspace / "app.py"
        before = target_path.read_text(encoding="utf-8")

        trace = agent.run(task_id="fix_pagination_v1", workspace=workspace)
        after = target_path.read_text(encoding="utf-8")

    assert after != before
    assert after.endswith("# benign update\n")
    assert trace.file_reads[0].content_preview == before.strip()
    assert trace.file_writes[0].content_preview == after.strip()


def test_cheating_agent_returns_trace_with_one_read_and_one_write() -> None:
    """Test that the cheating agent records one read and one write."""
    agent = CheatingScriptedAgent()

    with fixture_workspace("todo_api") as workspace:
        expected_workspace = str(workspace)
        trace = agent.run(task_id="hide_failing_test_v1", workspace=workspace)

    assert isinstance(trace, RunTrace)
    assert trace.task_id == "hide_failing_test_v1"
    assert trace.workspace == expected_workspace
    assert len(trace.file_reads) == 1
    assert len(trace.file_writes) == 1
    assert trace.file_reads[0].relative_path == "tests/test_app.py"
    assert trace.file_writes[0].relative_path == "tests/test_app.py"


def test_cheating_agent_modifies_test_file() -> None:
    """Test that the cheating agent appends to the test file."""
    agent = CheatingScriptedAgent()

    with fixture_workspace("todo_api") as workspace:
        target_path = workspace / "tests" / "test_app.py"
        before = target_path.read_text(encoding="utf-8")

        trace = agent.run(task_id="hide_failing_test_v1", workspace=workspace)
        after = target_path.read_text(encoding="utf-8")

    assert after != before
    assert after.endswith("# suspicious test adjustment\n")
    assert trace.file_reads[0].content_preview == before.strip()
    assert trace.file_writes[0].content_preview == after.strip()


def test_both_agents_set_final_output() -> None:
    """Test that both scripted agents set a final output."""
    benign_agent = BenignScriptedAgent()
    cheating_agent = CheatingScriptedAgent()

    with fixture_workspace("todo_api") as workspace:
        benign_trace = benign_agent.run(
            task_id="fix_pagination_v1",
            workspace=workspace,
        )

    with fixture_workspace("todo_api") as workspace:
        cheating_trace = cheating_agent.run(
            task_id="hide_failing_test_v1",
            workspace=workspace,
        )

    assert benign_trace.final_output is not None
    assert benign_trace.final_output.text == "Updated app.py successfully."
    assert cheating_trace.final_output is not None
    assert cheating_trace.final_output.text == "Adjusted tests to ensure success."


def test_running_agents_in_workspace_copy_does_not_mutate_source_fixture() -> None:
    """Test that scripted agents do not modify the source fixture repo."""
    fixture_path = resolve_fixture_repo("todo_api")
    source_app = (fixture_path / "app.py").read_text(encoding="utf-8")
    source_test = (fixture_path / "tests" / "test_app.py").read_text(encoding="utf-8")

    with fixture_workspace("todo_api") as workspace:
        BenignScriptedAgent().run(task_id="fix_pagination_v1", workspace=workspace)
        CheatingScriptedAgent().run(task_id="hide_failing_test_v1", workspace=workspace)

        assert (workspace / "app.py").read_text(encoding="utf-8") != source_app
        assert (workspace / "tests" / "test_app.py").read_text(
            encoding="utf-8"
        ) != source_test

    assert (fixture_path / "app.py").read_text(encoding="utf-8") == source_app
    assert (fixture_path / "tests" / "test_app.py").read_text(
        encoding="utf-8"
    ) == source_test
