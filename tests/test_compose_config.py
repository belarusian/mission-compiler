"""Tests for the opt-in ``config`` bounds axis on compose().

Cycle 10, TICKET-025 (issue #33): ``compose(...)`` gains a keyword-only
``config: str | None = None`` param that selects proven bounds via
``bounds_for_config`` when set. When None (the default) the behavior is
byte-identical to before. Additive only; no existing signature changed.
"""

from __future__ import annotations

import pytest

from mission_compiler.bounds import bounds_for, bounds_for_config
from mission_compiler.compose import compose


def test_compose_config_none_is_byte_identical_to_default():
    for spoke in ("project-setup", "cycle-implementation"):
        a = compose("Build it.", spoke=spoke)
        b = compose("Build it.", spoke=spoke, config=None)
        assert a.render().encode() == b.render().encode()
        assert a.launch_script.encode() == b.launch_script.encode()


def test_compose_config_selects_llm_config_bounds():
    # single-llm-long-pass has outer_wall 10800 vs the cycle-implementation spoke's 3600.
    launch = compose(
        "Build it.", spoke="cycle-implementation", config="single-llm-long-pass"
    )
    expected = bounds_for_config("single-llm-long-pass")
    assert launch.bounds == expected
    assert launch.bounds.outer_wall == 10800
    # And it genuinely differs from the spoke-default bounds.
    assert launch.bounds != bounds_for("cycle-implementation")


def test_compose_config_2llm_fast_matches_table():
    launch = compose("Build it.", spoke="project-setup", config="2-llm-fast")
    assert launch.bounds == bounds_for_config("2-llm-fast")
    # 2-llm-fast is heavier than the project-setup spoke default (outer_wall 3600 vs 1800).
    assert launch.bounds.outer_wall == 3600
    assert launch.bounds != bounds_for("project-setup")


def test_compose_config_unknown_raises_value_error():
    with pytest.raises(ValueError):
        compose("Build it.", config="no-such-config")


def test_compose_config_render_reflects_selected_bounds():
    launch = compose(
        "Build it.", spoke="cycle-implementation", config="single-llm-long-pass"
    )
    rendered = launch.render()
    assert "outer wall (perl alarm): 10800s" in rendered


def test_compose_config_deterministic():
    a = compose("Build it.", spoke="cycle-implementation", config="2-llm-fast")
    b = compose("Build it.", spoke="cycle-implementation", config="2-llm-fast")
    assert a.render().encode() == b.render().encode()
    assert a.launch_script.encode() == b.launch_script.encode()
