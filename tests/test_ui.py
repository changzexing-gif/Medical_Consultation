from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "app.py", *sorted((ROOT / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES, ids=lambda path: path.name)
def test_streamlit_page_smoke(page):
    app = AppTest.from_file(str(page), default_timeout=30)
    app.run()
    assert not app.exception, [str(item.value) for item in app.exception]
