"""Smoke test: verify the package imports cleanly."""


def test_import_mission_compiler():
    import mission_compiler

    assert mission_compiler.__version__ == "0.1.0"
