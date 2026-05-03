from app.version import VERSION, VERSION_LABEL


def test_version_label_is_readable_release_name():
    assert VERSION == "0.001.2"
    assert VERSION_LABEL == "V0.001.2"


def test_release_notes_exist_for_default_language():
    from app.version import release_notes_for

    notes = release_notes_for("de")

    assert notes["title"]
    assert notes["changes"]
