from prompt_action import APP_VERSION


def test_t01_import_package():
    assert APP_VERSION == "0.1.0-dev"
