"""Pytest configuration file."""


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "live: mark test as requiring external services (deselect with '-m \"not live\"')")
