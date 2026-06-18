"""Tests for the title classifier — season, quality, subgroup extraction."""

from youvedio.crawler.classifier import (
    classify,
    group_by_season,
    group_by_subgroup,
    relevance_sort,
)
from youvedio.models import TorrentResult


def _make(title: str) -> TorrentResult:
    return TorrentResult.create(source="test", title=title, magnet="")


class TestClassify:
    def test_extract_season_from_sxx_eyy(self):
        r = classify(_make("[Subs] Show S02E05 1080p"))
        assert r.season == 2
        assert r.episode == 5

    def test_extract_season_from_season_word(self):
        r = classify(_make("Show Season 2 1080p"))
        assert r.season == 2

    def test_extract_season_chinese(self):
        r = classify(_make("Show 第3季 1080p"))
        assert r.season == 3

    def test_extract_season_standalone(self):
        r = classify(_make("[Group] Show S04 1080p BluRay"))
        assert r.season == 4

    def test_extract_season_part(self):
        r = classify(_make("[Group] Show Part 2 1080p"))
        assert r.season == 2

    def test_no_season(self):
        r = classify(_make("Random video file without metadata"))
        assert r.season is None

    def test_extract_1080p(self):
        r = classify(_make("[Subs] Show S01 1080p"))
        assert r.quality == "1080P"

    def test_extract_4k(self):
        r = classify(_make("[Subs] Show S01 4K"))
        assert r.quality == "4K"

    def test_extract_2160p(self):
        r = classify(_make("[Subs] Show S01 2160p"))
        assert r.quality == "2160P"

    def test_quality_uppercase(self):
        r = classify(_make("[Subs] Show S01 1080P"))
        assert r.quality == "1080P"

    def test_no_quality(self):
        r = classify(_make("[Subs] Show S01"))
        assert r.quality is None

    def test_subgroup_from_brackets(self):
        r = classify(_make("[FBI] Show S01 1080p"))
        assert r.subgroup == "FBI"

    def test_subgroup_with_spaces(self):
        r = classify(_make("[Sub Group Name] Show S01 1080p"))
        assert r.subgroup == "Sub Group Name"

    def test_no_subgroup(self):
        r = classify(_make("Show S01 1080p"))
        assert r.subgroup is None

    def test_subgroup_at_start_only(self):
        r = classify(_make("Show [NotSubgroup] S01 1080p"))
        assert r.subgroup is None

    def test_extract_bluray(self):
        r = classify(_make("[Subs] Show S01 1080p Blu-Ray"))
        assert r.source_type == "Blu-ray"

    def test_extract_webdl(self):
        r = classify(_make("[Subs] Show S01 1080p WEB-DL"))
        assert r.source_type == "WEB-DL"

    def test_extract_webrip(self):
        r = classify(_make("[Subs] Show S01 1080p WEBRip"))
        assert r.source_type == "WEBRip"

    def test_extract_hevc(self):
        r = classify(_make("[Subs] Show S01 1080p HEVC"))
        assert r.source_type == "HEVC"

    def test_episode_from_exx(self):
        r = classify(_make("[Subs] Show E04 1080p"))
        assert r.episode == 4

    def test_episode_from_sxx_eyy(self):
        r = classify(_make("[Subs] Show S01E05 1080p"))
        assert r.episode == 5
        assert r.season == 1

    def test_full_classification(self):
        r = classify(_make("[FBI] Re:Zero Starting Life in Another World S04E11 1080p WEB-DL x265"))
        assert r.subgroup == "FBI"
        assert r.season == 4
        assert r.episode == 11
        assert r.quality == "1080P"
        assert r.source_type in ("WEB-DL", "HEVC")


class TestGroupBySeason:
    def test_groups_by_season_then_quality(self):
        results = [
            _make("[A] Show S01 1080p"),
            _make("[A] Show S01 720p"),
            _make("[A] Show S02 1080p"),
        ]
        classified = [classify(r) for r in results]
        groups = group_by_season(classified)

        assert "S01" in groups
        assert "S02" in groups
        assert "1080P" in groups["S01"]
        assert "720P" in groups["S01"]

    def test_newest_season_first(self):
        results = [
            _make("[A] Show S01 1080p"),
            _make("[A] Show S02 1080p"),
            _make("[A] Show S04 1080p"),
        ]
        classified = [classify(r) for r in results]
        groups = group_by_season(classified)
        keys = [k for k in groups if k != "_unclassified"]
        assert keys == ["S04", "S02", "S01"]

    def test_best_quality_first(self):
        results = [
            _make("[A] Show S01 720p"),
            _make("[A] Show S01 1080p"),
        ]
        classified = [classify(r) for r in results]
        groups = group_by_season(classified)
        qkeys = list(groups["S01"].keys())
        assert qkeys == ["1080P", "720P"]

    def test_unclassified_handling(self):
        results = [_make("Random video")]
        classified = [classify(r) for r in results]
        groups = group_by_season(classified)
        assert "_unclassified" in groups


class TestGroupBySubgroup:
    def test_groups_by_subgroup_then_season(self):
        results = [
            _make("[FBI] Show S01 1080p"),
            _make("[Erai] Show S01 1080p"),
        ]
        classified = [classify(r) for r in results]
        groups = group_by_subgroup(classified)
        assert "FBI" in groups
        assert "Erai" in groups

    def test_unknown_subgroup(self):
        results = [_make("Show S01 1080p")]
        classified = [classify(r) for r in results]
        groups = group_by_subgroup(classified)
        assert "_unknown" in groups


class TestRelevanceSort:
    def test_exact_title_start_first(self):
        r1 = _make("ZAnyWorld S02 1080p")  # substring only ("Any" not "Another")
        r2 = _make("Another S01 1080p")  # title starts with query
        sorted_results = relevance_sort("Another", [r1, r2])
        assert sorted_results[0].title.startswith("Another")
        assert "ZAnyWorld" in sorted_results[1].title

    def test_standalone_word_before_substring(self):
        r1 = _make("[Subs] Another world S01 1080p")  # standalone "Another"
        r2 = _make("[Subs] AnotherWorld S01 1080p")  # no word boundary
        sorted_results = relevance_sort("Another", [r1, r2])
        assert sorted_results[0] is r1

    def test_no_match_returns_original_order(self):
        r1 = _make("Some random title")
        r2 = _make("Another thing")
        # With "Another" as query, r2 should match
        sorted_results = relevance_sort("Another", [r1, r2])
        assert sorted_results[0] is r2

    def test_empty_query_returns_original(self):
        r1 = _make("Test A")
        r2 = _make("Test B")
        sorted_results = relevance_sort("", [r1, r2])
        assert sorted_results == [r1, r2]
