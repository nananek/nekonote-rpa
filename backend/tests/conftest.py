"""Shared fixtures for nekonote tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_browser_state():
    """Reset browser module globals between tests."""
    import nekonote.browser as b

    b._pw = None
    b._browser = None
    b._context = None
    b._page = None
    yield
    b._pw = None
    b._browser = None
    b._context = None
    b._page = None


@pytest.fixture(autouse=True)
def _reset_runtime():
    """Reset runtime output config between tests."""
    from nekonote._runtime import configure_output

    configure_output(format="human", verbose=False)
    yield
