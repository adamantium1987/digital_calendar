"""Pytest configuration and fixtures"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary configuration directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config(temp_config_dir: Path, monkeypatch):
    """Mock configuration for tests"""
    from backend.config.settings import ConfigManager

    config = ConfigManager(str(temp_config_dir))
    monkeypatch.setattr('backend.config.settings.config', config)
    return config


@pytest.fixture
def flask_app(mock_config):
    """Create Flask app for testing"""
    from backend.app import create_app

    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(flask_app):
    """Create Flask test client"""
    return flask_app.test_client()
