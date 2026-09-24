from __future__ import annotations

from biased_decisions import cli


def test_list_includes_regulated_tasks_and_cues(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "has_record", lambda *args, **kwargs: False)
    args = cli.build_parser().parse_args(["--root", str(tmp_path), "list"])
    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "qpain-treatment" in output
    assert "civil-comments-moderation" in output
    assert "sexual-orientation" in output
    assert "veteran-status" in output


def test_score_accepts_regulated_task_and_registered_cue():
    args = cli.build_parser().parse_args(
        ["score", "kev", "qpain-treatment", "--cue", "race"])
    assert args.task == "qpain-treatment" and args.cue == "race"


def test_answer_stays_limited_to_supported_preflight_tasks():
    parser = cli.build_parser()
    try:
        parser.parse_args(["answer", "kev", "qpain-treatment", "--cue", "race"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("regulated scoring task unexpectedly enabled answer preflight")
