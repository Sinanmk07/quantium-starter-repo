"""Browser tests for the Pink Morsel Dash visualiser (dash[testing] + pytest)."""

from app import app


def test_header_present(dash_duo):
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal(
        "header.hero h1",
        "Pink Morsel sales visualiser",
        timeout=15,
    )


def test_visualisation_present(dash_duo):
    dash_duo.start_server(app)
    dash_duo.wait_for_element_by_id("sales-line", timeout=15)
    dash_duo.wait_for_element("#sales-line .js-plotly-plot", timeout=15)


def test_region_picker_present(dash_duo):
    dash_duo.start_server(app)
    dash_duo.wait_for_element_by_id("region-radio", timeout=15)
    inputs = dash_duo.find_elements("#region-radio input[type='radio']")
    assert len(inputs) == 5
