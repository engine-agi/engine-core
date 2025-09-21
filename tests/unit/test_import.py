"""Test basic import of engine_core package."""

import pytest


def test_import_engine_core():
    """Test that engine_core can be imported."""
    import engine_core
    assert engine_core.__version__ == "1.0.0"
    assert engine_core.__author__ == "Engine Framework Team"


def test_import_core_modules():
    """Test that core modules can be imported."""
    from engine_core.core import agents, teams, workflows, tools, protocols, book

    # These should not raise ImportError
    assert agents is not None
    assert teams is not None
    assert workflows is not None
    assert tools is not None
    assert protocols is not None
    assert book is not None


def test_import_engine_types():
    """Test that engine types can be imported."""
    from engine_core import engine_types
    assert engine_types is not None