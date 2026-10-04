import pytest
from siteselect.config import PROCESSED, ROOT

pytestmark = pytest.mark.skipif(not (PROCESSED / "features_res6.parquet").exists(), reason="feature store not built")


def test_streamlit_app_runs():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=240)
    at.run()
    assert not at.exception
    at.sidebar.slider[2].set_value(35).run()      # raise Grid & Infrastructure weight -> rerank
    assert not at.exception
    assert len(at.dataframe) >= 1
