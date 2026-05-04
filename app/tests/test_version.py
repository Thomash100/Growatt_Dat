from app.version import RELEASE_CHANNEL, VERSION, VERSION_LABEL


def test_version_label_is_readable_release_name():
    assert VERSION == "0.001.9"
    assert VERSION_LABEL == "V0.001.9"
    assert RELEASE_CHANNEL == "stable"


def test_release_notes_exist_for_default_language():
    from app.version import release_notes_for

    notes = release_notes_for("de")

    assert notes["title"]
    assert notes["groups"]
