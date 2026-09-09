from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.nbs_native_rss import parse_nbs_native_latest_releases_rss
from world_signals.nbs_release_monitor import nbs_native_rss_review_candidates

PLAN = json.loads((ROOT / "data/monitor/CHINA_NBS_NATIVE_RSS_BX_PLAN_v0.1.json").read_text())


def item_xml(
    title: str,
    *,
    link: str = "https://www.stats.gov.cn/sj/zxfb/202609/t20260909_9999999.html",
    pub_time: str = "2026-09-09 09:30:02",
    pub_date: str | None = None,
    doc_id: str = "9999999",
    channel: str = "数据发布",
    source: str = "国家统计局",
    extra: str = "",
) -> str:
    pub_date = pub_time if pub_date is None else pub_date
    return f"""<item>
<title>{title}</title><channel>{channel}</channel><link>{link}</link><source>{source}</source>
<pubTime>{pub_time}</pubTime><pubDate>{pub_date}</pubDate><description></description><content></content><docId>{doc_id}</docId><hitCount>0</hitCount>{extra}
</item>"""


def feed(*items: str) -> str:
    return "<?xml version='1.0' encoding='utf-8'?><rss><channel>" + "".join(items) + "</channel></rss>"


def config() -> dict:
    return {
        "adapter_id": "CHINA_NBS_LATEST_RELEASES_RSS",
        "source_id": "WSSRC-MAC-031",
        "canonical_schedule_source_id": "WSSRC-MAC-007",
        "canonical_occurrence_ids": list(PLAN["canonical_occurrence_ids"]),
        "identity_by_occurrence_id": copy.deepcopy(PLAN["canonical_identity_by_occurrence_id"]),
        "request_budget_per_run": 1,
        "schedule_request_count_per_run": 0,
        "english_rss_request_count_per_run": 0,
        "article_followup_request_count_per_run": 0,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_publication_metadata_is_event_clock_authority": False,
        "rss_publication_metadata_is_schedule_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "automatic_english_rss_fetch_allowed": False,
        "automatic_commit_allowed": False,
    }


def records() -> list[dict]:
    out = []
    for occurrence_id, identity in PLAN["canonical_identity_by_occurrence_id"].items():
        out.append({
            "occurrence_id": occurrence_id,
            "series_id": identity["series_id"],
            "source_id": "WSSRC-MAC-007",
            "region": "East Asia",
            "source_timezone": "Asia/Shanghai",
            "time_precision": "MINUTE",
            "timing_type": "LOCAL_DATETIME",
            "event_type": "DATA_RELEASE",
            "start_local": identity["start_local"],
            "start_utc": identity["start_utc"],
            "lifecycle_status": "PLANNED",
            "certainty_status": "CONFIRMED",
        })
    return out


class NBSNativeRSSParserTests(unittest.TestCase):
    def test_parses_bounded_series_identities(self):
        xml = feed(
            item_xml("2026年8月份居民消费价格同比上涨0.5%", doc_id="1"),
            item_xml("2026年8月份工业生产者出厂价格同比上涨3.5%", doc_id="2", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260909_9999998.html", pub_time="2026-09-09 09:30:01"),
            item_xml("2026年9月中国采购经理指数运行情况", doc_id="3", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260930_9999997.html", pub_time="2026-09-30 09:30:01"),
            item_xml("8月份国民经济运行总体平稳、稳中有进", doc_id="4", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999996.html", pub_time="2026-09-15 10:00:07"),
            item_xml("2026年8月份规模以上工业增加值增长4.5%", doc_id="5", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999995.html", pub_time="2026-09-15 10:00:06"),
            item_xml("2026年8月份能源生产情况", doc_id="6", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999994.html", pub_time="2026-09-15 10:00:02"),
            item_xml("2026年1—8月份全国固定资产投资基本情况", doc_id="7", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999993.html", pub_time="2026-09-15 10:00:05"),
            item_xml("2026年1—8月份全国房地产市场基本情况", doc_id="8", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999992.html", pub_time="2026-09-15 10:00:04"),
            item_xml("2026年1—8月份社会消费品零售总额增长1.2%", doc_id="9", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260915_9999991.html", pub_time="2026-09-15 10:00:03"),
            item_xml("2026年8月下旬流通领域重要生产资料市场价格变动情况", doc_id="10", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260904_9999990.html", pub_time="2026-09-04 09:30:00"),
        )
        items = parse_nbs_native_latest_releases_rss(xml)
        got = [(x.series_key, x.reference_year, x.reference_month) for x in items]
        self.assertEqual(got[:9], [
            ("CPI", 2026, 8), ("PPI", 2026, 8), ("PMI", 2026, 9),
            ("NEP", 2026, 8), ("IP", 2026, 8), ("ENERGY", 2026, 8),
            ("FAI", 2026, 8), ("REALESTATE", 2026, 8), ("RETAIL", 2026, 8),
        ])
        self.assertEqual(got[9], (None, None, None))

    def test_nep_quarter_forms_are_bounded(self):
        xml = feed(
            item_xml("一季度国民经济实现良好开局", doc_id="11", link="https://www.stats.gov.cn/sj/zxfb/202604/t20260416_1111111.html", pub_time="2026-04-16 10:00:07"),
            item_xml("上半年国民经济迎难而上、稳中向好", doc_id="12", link="https://www.stats.gov.cn/sj/zxfb/202607/t20260715_1111112.html", pub_time="2026-07-15 10:00:08"),
            item_xml("前三季度国民经济运行总体平稳", doc_id="13", link="https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1111113.html", pub_time="2026-10-19 10:00:07"),
        )
        items = parse_nbs_native_latest_releases_rss(xml)
        self.assertEqual([(x.series_key, x.reference_year, x.reference_month) for x in items], [
            ("NEP", 2026, 3), ("NEP", 2026, 6), ("NEP", 2026, 9),
        ])

    def test_malformed_document_fails_closed(self):
        with self.assertRaises(AdapterError):
            parse_nbs_native_latest_releases_rss("<rss><channel><item></channel></rss>")

    def test_item_field_contract_drift_fails_closed(self):
        bad = item_xml("2026年8月份居民消费价格同比上涨0.5%", extra="<extra>x</extra>")
        with self.assertRaisesRegex(AdapterError, "field contract drift"):
            parse_nbs_native_latest_releases_rss(feed(bad))

    def test_off_host_link_fails_closed(self):
        bad = item_xml("2026年8月份居民消费价格同比上涨0.5%", link="https://example.com/sj/zxfb/202609/t20260909_9999999.html")
        with self.assertRaisesRegex(AdapterError, "outside official HTTPS host"):
            parse_nbs_native_latest_releases_rss(feed(bad))

    def test_pubtime_pubdate_divergence_fails_closed(self):
        bad = item_xml("2026年8月份居民消费价格同比上涨0.5%", pub_date="2026-09-09 09:31:02")
        with self.assertRaisesRegex(AdapterError, "pubTime/pubDate divergence"):
            parse_nbs_native_latest_releases_rss(feed(bad))

    def test_duplicate_configured_series_identity_fails_closed(self):
        one = item_xml("2026年8月份居民消费价格同比上涨0.5%", doc_id="21")
        two = item_xml("2026年8月份居民消费价格环比上涨0.1%", doc_id="22", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260909_8888888.html", pub_time="2026-09-09 09:30:03")
        with self.assertRaisesRegex(AdapterError, "multiple items share one configured-series identity"):
            parse_nbs_native_latest_releases_rss(feed(one, two))


class NBSNativeRSSComparatorTests(unittest.TestCase):
    def test_exact_cpi_identity_generates_review_candidate_only(self):
        items = parse_nbs_native_latest_releases_rss(feed(item_xml("2026年8月份居民消费价格同比上涨0.5%")))
        candidates, observations = nbs_native_rss_review_candidates(records(), items, config())
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["occurrence_ids"], ["WSO-MAC-A-0069"])
        self.assertEqual(candidate["event_state_inference"], "NONE")
        self.assertFalse(candidate["automatic_commit_allowed"])
        self.assertFalse(candidate["canonical_clock_mutation_allowed"])
        self.assertTrue(candidate["completion_requires_review"])
        self.assertFalse(candidate["new_value"]["feed_publication_metadata_is_event_clock_authority"])
        self.assertTrue(any(o["type"].endswith("ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_DELAY_CANCELLATION_OR_CERTAINTY_SEMANTICS") for o in observations))

    def test_historical_target_series_is_outside_scope_observation(self):
        historical = item_xml(
            "2026年7月份居民消费价格同比上涨0.5%",
            link="https://www.stats.gov.cn/sj/zxfb/202608/t20260809_1965008.html",
            pub_time="2026-08-09 09:30:02",
            doc_id="1965008",
        )
        candidates, observations = nbs_native_rss_review_candidates(
            records(), parse_nbs_native_latest_releases_rss(feed(historical)), config()
        )
        self.assertEqual(candidates, [])
        self.assertTrue(any(o["type"] == "CHINA_NBS_RELEVANT_SERIES_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE" for o in observations))

    def test_completed_occurrence_gets_no_completion_action(self):
        rows = records()
        next(r for r in rows if r["occurrence_id"] == "WSO-MAC-A-0069")["lifecycle_status"] = "COMPLETED"
        items = parse_nbs_native_latest_releases_rss(feed(item_xml("2026年8月份居民消费价格同比上涨0.5%")))
        candidates, observations = nbs_native_rss_review_candidates(rows, items, config())
        self.assertEqual(candidates, [])
        self.assertTrue(any(o["type"] == "CHINA_NBS_COMPLETED_OCCURRENCE_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION" for o in observations))

    def test_absence_has_no_event_state_semantics(self):
        unrelated = item_xml("2026年8月下旬流通领域重要生产资料市场价格变动情况", doc_id="31", link="https://www.stats.gov.cn/sj/zxfb/202609/t20260904_3333333.html", pub_time="2026-09-04 09:30:00")
        candidates, observations = nbs_native_rss_review_candidates(
            records(), parse_nbs_native_latest_releases_rss(feed(unrelated)), config()
        )
        self.assertEqual(candidates, [])
        absence = observations[-1]
        self.assertEqual(absence["matched_occurrence_count"], 0)
        self.assertEqual(absence["event_state_inference"], "NONE")
        self.assertFalse(absence["automatic_commit_allowed"])

    def test_authority_gate_drift_fails_closed(self):
        cfg = config()
        cfg["clock_authority"] = True
        with self.assertRaisesRegex(ValueError, "monitor gate drift"):
            nbs_native_rss_review_candidates(records(), [], cfg)

    def test_canonical_clock_drift_fails_closed(self):
        rows = records()
        next(r for r in rows if r["occurrence_id"] == "WSO-MAC-A-0069")["start_local"] = "2026-09-09T09:31:00"
        with self.assertRaisesRegex(ValueError, "Canonical scope drift"):
            nbs_native_rss_review_candidates(rows, [], config())


if __name__ == "__main__":
    unittest.main()
