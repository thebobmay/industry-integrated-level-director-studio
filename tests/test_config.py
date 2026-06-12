"""Tests for environment loading precedence.

The key behavior: the local .env must override a value already present in the
process environment, so a stale system credential cannot shadow the project's own
configuration.
"""

from __future__ import annotations

import os

from ai_level_director.config import load_environment


def test_load_environment_overrides_process_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AILD_TEST_VAR", "stale-system-value")
    env_file = tmp_path / ".env"
    env_file.write_text("AILD_TEST_VAR=local-env-value\n", encoding="utf-8")

    load_environment(env_file, override=True)
    assert os.environ["AILD_TEST_VAR"] == "local-env-value"


def test_load_environment_without_override_keeps_process_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AILD_TEST_VAR", "stale-system-value")
    env_file = tmp_path / ".env"
    env_file.write_text("AILD_TEST_VAR=local-env-value\n", encoding="utf-8")

    load_environment(env_file, override=False)
    assert os.environ["AILD_TEST_VAR"] == "stale-system-value"
