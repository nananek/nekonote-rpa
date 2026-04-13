"""nekonote - Python RPA toolkit.

Synchronous API modules for scripting::

    from nekonote import browser, desktop, window, log

    browser.open()
    browser.navigate("https://example.com")
    browser.click("#submit")
    browser.close()
"""

from nekonote import ai  # noqa: F401
from nekonote import browser  # noqa: F401
from nekonote import db  # noqa: F401
from nekonote import desktop  # noqa: F401
from nekonote import excel  # noqa: F401
from nekonote import file  # noqa: F401
from nekonote import http  # noqa: F401
from nekonote import log  # noqa: F401
from nekonote import pdf  # noqa: F401
from nekonote import retry  # noqa: F401
from nekonote import text  # noqa: F401
from nekonote import window  # noqa: F401
