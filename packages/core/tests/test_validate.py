"""validate.py's build-blocking checks, exercised against seeded bad
data -- each test breaks exactly one rule so a failure here points at
the right check."""

import pytest
from fishguide import validate
from fishguide.models import Fish, Group


def _fish(key: str, coords=(50, 100)) -> Fish:
    return Fish(
        key=key,
        name=key.title(),
        size="medium",
        coords=[coords],
        about="x",
        portrait={"body_color": "#fff"},
    )


def _group(fish, view_box="0 0 100 251", **kw) -> Group:
    return Group(
        id=kw.pop("id", "g"),
        title="G",
        tier="B",
        layout="cluster",
        subtitle="",
        badges=[],
        cast="",
        view_box=view_box,
        map_caption="",
        map_alt="",
        fish=fish,
        **kw,
    )


def test_clean_group_has_no_errors():
    g = _group([_fish("a"), _fish("b", coords=(60, 100))])
    assert validate.validate_all([g]) == []


def test_marker_too_low_fails_safe_area():
    g = _group([_fish("a", coords=(50, 10))])  # y < 18
    errors = validate.check_marker_safe_area(g)
    assert any("y=10" in e for e in errors)


def test_marker_too_high_fails_safe_area():
    g = _group([_fish("a", coords=(50, 230))])  # y > 225
    errors = validate.check_marker_safe_area(g)
    assert any("y=230" in e for e in errors)


def test_marker_too_close_to_view_box_edge_fails():
    g = _group([_fish("a", coords=(2, 100))], view_box="0 0 100 251")  # x < vx+12
    errors = validate.check_marker_safe_area(g)
    assert any("x=2" in e for e in errors)


def test_view_box_height_must_be_251():
    g = _group([_fish("a")], view_box="0 0 100 200")
    assert any("!= 251" in e for e in validate.check_view_box_height(g))


def test_duplicate_fish_key_across_groups():
    g1 = _group([_fish("shared")], id="g1")
    g2 = _group([_fish("shared")], id="g2")
    errors = validate.check_unique_fish([g1, g2])
    assert any("shared" in e for e in errors)


def test_empty_portrait_is_fine():
    """No portrait at all is the expected shape for a fish with a real
    wiki picture -- see render.make_fish_pic."""
    f = _fish("a")
    f.portrait = {}
    g = _group([f])
    assert validate.check_portrait_shape(g) == []


def test_portrait_missing_body_color_is_an_error():
    f = _fish("a")
    f.portrait = {"shape": "oval"}  # started, but no body_color
    g = _group([f])
    errors = validate.check_portrait_shape(g)
    assert any("a" in e for e in errors)


def test_validate_or_raise_raises_on_errors():
    g = _group([_fish("a", coords=(50, 10))])
    with pytest.raises(validate.ValidationError):
        validate.validate_or_raise([g])
