"""layout.py's page-splitting rules, checked against small synthetic
groups rather than the real data files so a future edit to data/ can't
silently break coverage here."""

from fishguide import layout
from fishguide.models import Fish, Group


def _fish(key: str) -> Fish:
    return Fish(key=key, name=key.title(), size="medium", coords=[(0, 0)], about="", portrait={})


def _group(n_fish: int, max_entries_with_map: int = 5) -> Group:
    return Group(
        id="g",
        title="G",
        tier="B",
        layout="cluster",
        subtitle="",
        badges=[],
        cast="",
        view_box="0 0 100 251",
        map_caption="",
        map_alt="",
        fish=[_fish(f"f{i}") for i in range(n_fish)],
        max_entries_with_map=max_entries_with_map,
    )


def test_split_group_fits_on_one_page():
    pages = layout.split_group(_group(4, max_entries_with_map=5))
    assert len(pages) == 1
    assert not pages[0].is_continuation
    assert len(pages[0].fish) == 4


def test_split_group_spills_to_continuation():
    pages = layout.split_group(_group(7, max_entries_with_map=4))
    assert [p.is_continuation for p in pages] == [False, True]
    assert len(pages[0].fish) == 4
    assert len(pages[1].fish) == 3
    assert pages[1].continued_range == (5, 7)


def test_split_group_spans_multiple_continuation_pages():
    pages = layout.split_group(_group(13, max_entries_with_map=4))
    assert [len(p.fish) for p in pages] == [4, 6, 3]
    assert pages[1].continued_range == (5, 10)
    assert pages[2].continued_range == (11, 13)


def test_duo_and_feature_groups_never_split():
    g = _group(2)
    g.layout = "duo"
    assert len(layout.split_group(g)) == 1


def test_grid_cols():
    main_small = layout.split_group(_group(4))[0]
    main_big = layout.split_group(_group(5))[0]
    cont = layout.split_group(_group(9, max_entries_with_map=4))[1]
    assert layout.grid_cols(main_small) == 4
    assert layout.grid_cols(main_big) == 3
    assert layout.grid_cols(cont) == 3
