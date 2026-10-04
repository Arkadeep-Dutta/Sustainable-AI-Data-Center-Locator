import pytest
from siteselect.config import PROCESSED, ROOT

pytestmark = pytest.mark.skipif(not (PROCESSED / "features_res6.parquet").exists(), reason="feature store not built")
APP = str(ROOT / "app" / "streamlit_app.py")


def test_demo_default_view_is_final_recommendation():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=240)
    at.run()
    assert not at.exception
    assert at.sidebar.radio[0].value == "Final recommendation"
    text = " ".join(m.value for m in at.markdown) + " ".join(i.value for i in at.info)
    assert "Wyoming" in text and "King County" in text
    labels = [m.label for m in at.metric]
    assert "Final recommended site" in labels and "Model #1 (quantitative)" in labels
    assert len(at.dataframe) >= 2                     # top-5 table + sustainability table


def test_explore_view_reweights():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=240)
    at.run()
    at.sidebar.radio[0].set_value("Explore & re-weight").run()
    assert not at.exception
    at.sidebar.slider[2].set_value(35).run()          # raise Grid & Infrastructure weight -> rerank
    assert not at.exception
    assert len(at.dataframe) >= 1
