from app.version import VERSION, VERSION_LABEL


def test_version_label_is_readable_release_name():
    assert VERSION == "0.001.1"
    assert VERSION_LABEL == "V0.001.1"

