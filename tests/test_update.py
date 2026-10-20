# -*- coding: utf-8 -*-
"""
定期更新まわりのテスト（ネットワーク不要）。

注意: J-STAGE の Atom は実APIの応答ではなく、parse_entry が読む要素だけを手で組んだ最小の例。
実APIとの整合は GitHub Actions の初回実行（workflow_dispatch）で確認する。
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

import run_update
import scrape_pubmed
import update_jstage


def _resp(status=200):
    r = mock.MagicMock()
    r.status_code = status
    r.raise_for_status.return_value = None
    return r


class PubmedRetryTest(unittest.TestCase):
    @mock.patch("scrape_pubmed.time.sleep")
    @mock.patch("scrape_pubmed.requests.get")
    def test_retries_then_succeeds(self, get, _sleep):
        get.side_effect = [requests.ConnectionError("down"), _resp(500), _resp(200)]
        resp = scrape_pubmed._get("http://x", {}, 5)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get.call_count, 3)

    @mock.patch("scrape_pubmed.time.sleep")
    @mock.patch("scrape_pubmed.requests.get", side_effect=requests.ConnectionError("down"))
    def test_gives_up_with_exception(self, get, _sleep):
        with self.assertRaises(RuntimeError):
            scrape_pubmed._get("http://x", {}, 5)
        self.assertEqual(get.call_count, scrape_pubmed.MAX_RETRIES)

    @mock.patch("scrape_pubmed.time.sleep")
    @mock.patch("scrape_pubmed.requests.get")
    def test_sends_tool_and_optional_credentials(self, get, _sleep):
        get.return_value = _resp(200)
        with mock.patch.object(scrape_pubmed, "NCBI_API_KEY", "KEY"), \
                mock.patch.object(scrape_pubmed, "NCBI_EMAIL", "a@example.org"):
            scrape_pubmed._get("http://x", {"db": "pubmed"}, 5)
        sent = get.call_args.kwargs["params"]
        self.assertEqual((sent["tool"], sent["api_key"], sent["email"]),
                         ("kampo_database", "KEY", "a@example.org"))


class PubmedFetchAllTest(unittest.TestCase):
    def _patch(self, count, efetch, parse):
        return (mock.patch("scrape_pubmed.esearch", return_value=(count, "w", "1")),
                mock.patch("scrape_pubmed.efetch_batch", side_effect=efetch),
                mock.patch("scrape_pubmed.parse_articles", side_effect=parse),
                mock.patch("scrape_pubmed.time.sleep"))

    def _run(self, patches):
        with patches[0], patches[1], patches[2], patches[3]:
            return scrape_pubmed.fetch_all("q", "term")

    def test_complete_fetch(self):
        arts = [{"pmid": str(i)} for i in range(200)]
        out = self._run(self._patch(400, lambda *a: "<x/>", lambda x: arts))
        self.assertEqual(len(out), 400)

    def test_failed_batch_stops_instead_of_dropping(self):
        def efetch(*a):
            raise requests.ConnectionError("down")
        with self.assertRaises(RuntimeError):
            self._run(self._patch(400, efetch, lambda x: []))

    def test_incomplete_result_stops(self):
        # 400件ヒットなのに解析できたのが0件 → 欠落として停止
        with self.assertRaises(RuntimeError):
            self._run(self._patch(400, lambda *a: "<x/>", lambda x: []))


ATOM = """<feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/"
 xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
 <entry>
  <title>テスト論文</title>
  <id>https://www.jstage.jst.go.jp/article/kampomed/76/9/76_1/_article/-char/ja/</id>
  <prism:doi>10.3937/kampomed.76.1</prism:doi>
  <prism:volume>76</prism:volume>
  <pubyear>2026</pubyear>
  <cdjournal>kampomed</cdjournal>
 </entry>
</feed>"""


class JstageTest(unittest.TestCase):
    def test_parse_overrides_journal_name(self):
        entry = ET.fromstring(ATOM).find("{http://www.w3.org/2005/Atom}entry")
        art = update_jstage.parse_journal_entry(entry, "日本東洋医学雑誌", "kampomed")
        self.assertEqual(art["journal"], "日本東洋医学雑誌")   # parse_entry の固定値（鍼灸学会雑誌）を上書き
        self.assertEqual(art["cdjournal"], "kampomed")
        self.assertEqual(art["doi"], "10.3937/kampomed.76.1")
        self.assertEqual(art["pubyear"], "2026")

    def test_select_new(self):
        known = update_jstage.known_keys([{"entry_id": "e1", "link": "l1", "doi": "d1"}])
        fetched = [
            {"entry_id": "e1", "link": "l1", "doi": "d1"},    # 既存
            {"entry_id": "e2", "link": "l2", "doi": "d1"},    # DOI が既知 → 既存扱い
            {"entry_id": "e3", "link": "l3", "doi": "d3"},    # 新着
            {"entry_id": "e3", "link": "l3", "doi": "d3"},    # 取得内の重複
            {"entry_id": "", "link": "", "doi": ""},          # 識別子なし → 採用しない
        ]
        new = update_jstage.select_new(fetched, known)
        self.assertEqual([a["entry_id"] for a in new], ["e3"])


def _art(link, source="pm", year="2025", tags=True, **kw):
    a = {"t": f"論文[{link}]", "y": year, "l": link, "j": "J", "s": source, "ab": "x"}
    if tags:
        a["d"] = ["ICD01_common_cold"]
    a.update(kw)
    return a


def _db(arts):
    return {"articles": arts}


class RunUpdateTest(unittest.TestCase):
    def test_load_db_from_html(self):
        db = {"articles": [{"t": "a}b", "l": "L"}], "stats": {"total": 1}}
        html = "<script>const x=1;\nconst DB = " + json.dumps(db, ensure_ascii=False) + ";\nconst y=2;</script>"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.html"
            p.write_text(html, encoding="utf-8")
            self.assertEqual(run_update.load_db_from_html(p), db)
            self.assertIsNone(run_update.load_db_from_html(Path(d) / "none.html"))

    def test_diff_and_summary(self):
        prev = _db([_art("a"), _art("b", "jp", "2024")])
        new = _db([_art("a"), _art("c", "pm", "2026", tags=False), _art("b", "jp", "2024")])
        added, removed = run_update.diff_dbs(prev, new)
        self.assertEqual([x["l"] for x in added], ["c"])
        self.assertEqual(removed, [])
        s = run_update.summarize(new)
        self.assertEqual((s["total"], s["jp"], s["pm"], s["untagged"], s["latest_pm"]), (3, 1, 2, 1, 2026))

    def test_gates(self):
        prev = run_update.summarize(_db([_art(str(i)) for i in range(100)] +
                                        [_art(f"j{i}", "jp", "2025") for i in range(10)]))
        # 正常: 増加のみ
        ok = run_update.summarize(_db([_art(str(i)) for i in range(105)] +
                                      [_art(f"j{i}", "jp", "2025") for i in range(10)]))
        self.assertEqual(run_update.check_gates(prev, ok, 0, 2026)[0], [])
        # PubMed が大きく減った → 停止
        bad = run_update.summarize(_db([_art(str(i)) for i in range(50)] +
                                       [_art(f"j{i}", "jp", "2025") for i in range(10)]))
        errors, _ = run_update.check_gates(prev, bad, 0, 2026)
        self.assertTrue(any("総数が減少" in e for e in errors))
        self.assertTrue(any("PubMed" in e for e in errors))
        # J-STAGE が減った・重複キーあり → 停止
        jp_down = run_update.summarize(_db([_art(str(i)) for i in range(100)] +
                                           [_art(f"j{i}", "jp", "2025") for i in range(5)]))
        self.assertTrue(any("J-STAGE" in e for e in run_update.check_gates(prev, jp_down, 0, 2026)[0]))
        self.assertTrue(any("重複" in e for e in run_update.check_gates(prev, ok, 2, 2026)[0]))
        # 急増・J-STAGE の発行年が古い → 警告のみ
        big = run_update.summarize(_db([_art(str(i)) for i in range(200)] +
                                       [_art(f"j{i}", "jp", "2023") for i in range(10)]))
        errors, warnings = run_update.check_gates(prev, big, 0, 2026)
        self.assertEqual(errors, [])
        self.assertTrue(any("増加" in w for w in warnings))
        self.assertTrue(any("J-STAGE の最新発行年" in w for w in warnings))

    def test_report_lists_every_added_article_and_escapes_brackets(self):
        added = [_art(f"http://x/{i}", year="2026") for i in range(500)]
        new_sum = run_update.summarize(_db(added))
        summary = run_update.render_summary("2026-11-01", None, new_sum, added, [], [], [], 2026)
        text = run_update.render_report(summary, added, [])
        self.assertEqual(sum(1 for line in text.splitlines() if line.startswith("- [")), 500)
        self.assertIn("論文\\[http://x/0\\]", text)


if __name__ == "__main__":
    unittest.main()
