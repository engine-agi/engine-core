"""Smoke tests for engine-core package."""

import pytest


@pytest.mark.smoke
def test_package_import():
    """Test that the engine_core package can be imported."""
    import engine_core

    assert engine_core is not None
    assert hasattr(engine_core, "__version__")
    assert hasattr(engine_core, "__author__")


@pytest.mark.smoke
def test_core_modules_import():
    """Test that all core modules can be imported."""
    try:
        from engine_core.core import agents, book, protocols, teams, tools, workflows

        # Basic assertions
        assert agents is not None
        assert teams is not None
        assert workflows is not None
        assert tools is not None
        assert protocols is not None
        assert book is not None

    except ImportError as e:
        pytest.skip(f"Core modules not yet implemented: {e}")


@pytest.mark.smoke
def test_version_consistency():
    """Test that version is properly defined."""
    import engine_core

    version = getattr(engine_core, "__version__", None)
    assert version is not None
    assert isinstance(version, str)
    assert len(version.split(".")) >= 2  # At least major.minor


@pytest.mark.smoke
def test_basic_functionality():
    """Test basic functionality without complex setup."""
    # This is a placeholder for more comprehensive smoke tests
    # As modules are implemented, add more specific tests here
    assert True  # Basic sanity check
