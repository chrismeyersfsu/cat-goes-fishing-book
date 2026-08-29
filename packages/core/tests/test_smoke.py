"""Each package tests only itself; run via ./packages/core/ci.sh.

Fake external HTTP at one request-function seam (monkeypatch a module's
_get/_post) against fixture files; keep parsers pure so they test
without I/O.
"""

from fishguide import cli


def test_cli_runs(capsys):
    cli.main([])
    assert "fishguide" in capsys.readouterr().out
