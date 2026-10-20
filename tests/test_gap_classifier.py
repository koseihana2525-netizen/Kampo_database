# -*- coding: utf-8 -*-
"""
gap_classifier.py（認知ギャップの分類）のテスト。実データは使わず、短い合成の文章だけを使う。

legacy は投稿版 v3 の処理の再現、primary は主解析（修正版）。
各テストは、legacy で検出できなかった・誤って検出していたものが primary で直っていること、
および日本語側など直す必要のない部分が変わっていないことを確かめる。
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import gap_classifier as G
from romaji import yomi_to_romaji, yomi_to_romaji_variants


def art(title="", abstract="", lang="en"):
    return {"title": title, "abstract": abstract, "lang": lang}


def terms(c, level="conservative"):
    return {t for t, _ in c[level]}


class FormulaDetectionEnglish(unittest.TestCase):
    def test_hyphenated_romanization_is_detected_only_in_primary(self):
        a = art("Effects of Sho-saiko-to on lipid peroxidation")
        self.assertFalse(G.classify(a, "legacy")["formula"])
        self.assertTrue(G.classify(a, "primary")["formula"])

    def test_spaced_and_hyphenated_variants(self):
        for title in ("Oren-gedoku-to inhibits calcification", "Hochu ekki to in the long-term management", "Rikkunshi-to (TJ-43) relaxation"):
            self.assertTrue(G.classify(art(title), "primary")["formula"], title)

    def test_conventional_romanization_of_all_formulas(self):
        # 読みから作る綴りは、長音を畳んだ形（Shosaikoto）と、促音を重ねた形（Rikkunshito, Hochuekkito）を含む
        for title in ("Juzen-taiho-to for anemia", "Hochu-ekki-to in frailty", "Rikkunshito and appetite", "Ninjin'yoei-to in older adults",
                      "Orengedoku-to for dermatitis", "Shimotsu-to in vitro", "Uyaku-junki-san for neuralgia"):
            self.assertTrue(G.classify(art(title), "primary")["formula"], title)

    def test_short_hyphenated_names_and_spelling_variants(self):
        # 8文字未満の名前は1語まるごとの一致で、ハイフンの有無によらない。訓令式・m→b・oh・長音の混在も同じ処方として扱う
        for title in ("Mao-to for influenza", "Unkei-to in infertility", "Kihi-to and insomnia", "Kanzo-to was added", "Koso-san for dyspepsia",
                      "Syo-saiko-to in hepatitis", "Gosya-jinki-gan for neuropathy", "Tokaku-jyoki-to for constipation", "Shimbu-to in elderly patients",
                      "Hachimi-ji-oh-gan and the bladder", "Ninjin-youei-to for frailty", "Byakko-ka-ninjin-to for diabetes", "Tsumyaku-shigyaku-to"):
            self.assertTrue(G.classify(art(title), "primary")["formula"], title)

    def test_short_names_must_be_whole_words(self):
        for title in ("The maotoxin was measured", "Only kihitos were counted", "unkeitoxic", "Mao tox"):
            self.assertFalse(G.classify(art(title), "primary")["formula"], title)

    def test_shorter_name_inside_longer_formula_name_is_attributed_to_the_longer(self):
        c = G.classify(art("Saikokeishito was given"), "primary")
        self.assertTrue(c["formula"])
        self.assertNotIn("keishito", c["formulas"])
        self.assertTrue(G.classify(art("Keishito was given"), "primary")["formula"])

    def test_tj_codes_are_detected_only_in_primary(self):
        # legacy はパターン側にハイフンを残したまま、テキスト側だけ空白に置換していたため、TJ コードを検出できなかった
        for title in ("Efficacy of TJ-54 in dementia", "Efficacy of TJ-054 in dementia", "TJ 107 was administered"):
            self.assertFalse(G.classify(art(title), "legacy")["formula"], title)
            self.assertTrue(G.classify(art(title), "primary")["formula"], title)

    def test_tj_code_outside_tsumura_range_is_not_a_formula(self):
        self.assertFalse(G.classify(art("TJ-999 was used"), "primary")["formula"])
        self.assertFalse(G.classify(art("Sample TJ1000 batch"), "primary")["formula"])

    def test_running_piglet_is_a_concept_not_a_formula(self):
        a = art("The running piglet syndrome in Kampo")
        self.assertTrue(G.classify(a, "legacy")["formula"])          # legacy の誤り
        c = G.classify(a, "primary")
        self.assertFalse(c["formula"])
        self.assertIn("running piglet", terms(c))                      # 思考概念語としては残る
        self.assertEqual(c["quad_conservative"], "Q2_cognition_only")

    def test_unrelated_text_has_no_formula(self):
        self.assertFalse(G.classify(art("Muscle contraction in rats"), "primary")["formula"])


class FormulaDetectionJapanese(unittest.TestCase):
    def test_japanese_detection_is_unchanged(self):
        for text, expected in (("五苓散を投与した", True), ("抑肝散加陳皮半夏が奏効", True), ("検査値の推移を検討した", False)):
            a = art(text, lang="ja")
            self.assertEqual(G.classify(a, "legacy")["formula"], expected, text)
            self.assertEqual(G.classify(a, "primary")["formula"], expected, text)


class ConceptDetection(unittest.TestCase):
    def test_hyphenated_concept_terms(self):
        a = art("Yin-yang balance and kyo-jitsu pattern")
        self.assertNotIn("yin-yang", terms(G.classify(a, "legacy")))
        self.assertIn("yin-yang", terms(G.classify(a, "primary")))
        self.assertIn("kyo-jitsu", terms(G.classify(a, "primary")))
        self.assertIn("mind-body unity", terms(G.classify(art("the concept of mind-body unity"), "primary")))

    def test_sho_requires_a_word_boundary(self):
        # legacy は 'sho ' を部分文字列で照合していたため、yusho・tsusho などに当たっていた
        for text in ("PCB poisoning in yusho patients", "bofu tsusho san was given", "taisho kampo"):
            self.assertIn("sho ", terms(G.classify(art(text), "legacy")), text)
            self.assertNotIn("sho ", terms(G.classify(art(text), "primary")), text)

    def test_sho_followed_by_punctuation_is_detected(self):
        a = art("Diagnosis by sho, a traditional pattern")
        self.assertNotIn("sho ", terms(G.classify(a, "legacy")))
        self.assertIn("sho ", terms(G.classify(a, "primary")))
        self.assertIn("sho ", terms(G.classify(art("Treatment was selected by sho."), "primary")))

    def test_sho_in_hyphenated_formula_name_is_not_a_concept(self):
        # Sho-saiko-to の Sho は小柴胡湯の「小」。ハイフン付きの処方名を検出できるようにした分、これを証と数えると偽の Q1 が生じる
        for text in ("Sho-saiko-to was administered", "Effects of Sho-seiryu-to and Sho-hange-ka-bukuryo-to"):
            c = G.classify(art(text), "primary")
            self.assertTrue(c["formula"], text)
            self.assertNotIn("sho ", terms(c), text)
            self.assertEqual(c["quad_conservative"], "Q3_formula_only", text)
        c = G.classify(art("Sho-saiko-to was selected according to sho."), "primary")
        self.assertIn("sho ", terms(c))                                   # 独立した sho は数える
        self.assertEqual(c["quad_conservative"], "Q1_both")
        c = G.classify(art("sho-based selection of Kamishoyosan"), "primary")
        self.assertIn("sho-based", terms(c))
        self.assertNotIn("sho ", terms(c))

    def test_sho_inside_a_formula_name_split_by_spaces_is_not_a_concept(self):
        for text in ("Sho saiko-to was administered", "Bofu tsu sho san was given", "Sho-seiryu-to and Sho seiryu to"):
            c = G.classify(art(text), "primary")
            self.assertTrue(c["formula"], text)
            self.assertNotIn("sho ", terms(c), text)

    def test_capitalized_abbreviations_are_not_concepts(self):
        # SHO は Shosaiko-to の略、HIE は低酸素性虚血性脳症
        for text in ("Goreisan reduced HIE injury", "Shosaiko-to (SHO) was administered; SHO increased"):
            c = G.classify(art(text), "primary")
            self.assertNotIn("sho ", terms(c), text)
            self.assertNotIn("hie ", terms(c), text)
        self.assertIn("sho ", terms(G.classify(art("Goreisan was selected by Sho."), "primary")))
        self.assertIn("hie ", terms(G.classify(art("Goreisan for hie in women"), "primary")))

    def test_extension_terms_only_in_primary_ext(self):
        a = art("桂枝茯苓丸を投与した。腹診で臍傍圧痛を認め、桂枝湯証と考えた。", lang="ja")
        self.assertEqual(G.classify(a, "primary")["quad_conservative"], "Q3_formula_only")
        c = G.classify(a, "primary_ext")
        self.assertEqual(c["quad_conservative"], "Q1_both")
        self.assertIn("腹診", terms(c))
        self.assertIn("○○湯証", terms(c))
        for variant in ("primary", "primary_ext"):   # 拡張は日本語側だけ
            self.assertEqual(G.classify(art("Keishibukuryogan was prescribed; abdominal findings were noted"), variant)["quad_conservative"], "Q3_formula_only")

    def test_macron_is_folded(self):
        a = art("Kampo diagnosis by shō")
        self.assertNotIn("sho ", terms(G.classify(a, "legacy")))
        self.assertIn("sho ", terms(G.classify(a, "primary")))

    def test_folding_does_not_touch_japanese(self):
        text = "がぎぐげご ぱぴぷぺぽ 随証治療"
        self.assertEqual(G.fold_diacritics(text), text)
        self.assertEqual(G.fold_diacritics("Hōshō-sōtai"), "Hosho-sotai")

    def test_zuisho_alone_is_excluded_from_conservative(self):
        alone = art("随証治療の重要性", lang="ja")
        for variant in G.VARIANTS:
            c = G.classify(alone, variant)
            self.assertIn("随証", terms(c, "liberal"))
            self.assertEqual(terms(c), set())
        both = art("気虚に対して随証治療を行った", lang="ja")
        for variant in G.VARIANTS:
            self.assertIn("随証", terms(G.classify(both, variant)))

    def test_dictionary_content_is_the_submitted_version(self):
        self.assertEqual(len(G.CONCEPT_TERMS), 181)                      # 投稿版の辞書B（Liberal）
        self.assertEqual(len({t for t in G.CONCEPT_TERMS if t not in G.FP_HARD and t != "冷え"}), 177)   # Conservative
        self.assertEqual(len(G.CONCEPT_TERMS) - len([t for t in G.CONCEPT_TERMS if t in G.STRICT_REMOVE]), 166)   # Strict
        self.assertEqual(G.CONCEPT_TERMS["瘀血"], "pathology")


class Quadrant(unittest.TestCase):
    def test_quadrants(self):
        self.assertEqual(G.quadrant(True, [("a", "b")]), "Q1_both")
        self.assertEqual(G.quadrant(False, [("a", "b")]), "Q2_cognition_only")
        self.assertEqual(G.quadrant(True, []), "Q3_formula_only")
        self.assertEqual(G.quadrant(False, []), "Q4_neither")

    def test_classification_end_to_end(self):
        c = G.classify(art("Kamishoyosan improves qi deficiency symptoms"), "primary")
        self.assertEqual(c["quad_conservative"], "Q1_both")
        c = G.classify(art("Kamishoyosan was prescribed for menopausal symptoms"), "primary")
        self.assertEqual(c["quad_conservative"], "Q3_formula_only")

    def test_invalid_variant(self):
        with self.assertRaises(ValueError):
            G.classify(art("x"), "unknown")


class Romaji(unittest.TestCase):
    def test_yomi_to_romaji(self):
        self.assertEqual(yomi_to_romaji("よくかんさん"), "yokukansan")
        self.assertEqual(yomi_to_romaji("ごれいさん"), "goreisan")
        self.assertEqual(yomi_to_romaji("しょ"), "sho")

    def test_romaji_variants_match_english_conventions(self):
        self.assertEqual(yomi_to_romaji_variants("しょうさいことう"), {"shousaikotou", "shosaikoto"})
        self.assertIn("rikkunshito", yomi_to_romaji_variants("りっくんしとう"))        # 促音は次の子音を重ねる
        self.assertIn("hochuekkito", yomi_to_romaji_variants("ほちゅうえっきとう"))
        self.assertIn("ninjinyoeito", yomi_to_romaji_variants("にんじんようえいとう"))
        self.assertEqual(yomi_to_romaji_variants("よくかんさん"), {"yokukansan"})
        self.assertIn("byakkokaninjinto", yomi_to_romaji_variants("びゃっこかにんじんとう"))   # びゃ は HEPBURN に無い
        self.assertIn("tsumyakushigyakuto", yomi_to_romaji_variants("つうみゃくしぎゃくとう"))
        self.assertIn("jidabokuippo", yomi_to_romaji_variants("ぢだぼくいっぽう"))
        with self.assertRaises(ValueError):
            yomi_to_romaji_variants("ゐ")

    def test_romaji_names_for_compact_matching_are_long_enough(self):
        self.assertTrue(G._COMPACT_NAMES)
        self.assertTrue(all(len(n) >= 8 for n in G._COMPACT_NAMES))
        self.assertNotIn("running piglet", G._COMPACT_NAMES)


class Statistics(unittest.TestCase):
    """run_gap_analysis.py の統計の補助関数（scipy・statsmodels・pandas が無い環境ではスキップ）"""

    @classmethod
    def setUpClass(cls):
        try:
            import run_gap_analysis as R
        except ImportError as e:
            raise unittest.SkipTest(f"解析用の依存が無い: {e}")
        cls.R = R

    def test_single_stratum_mh_equals_sample_or(self):
        k, p = (500, 600), (30, 1300)
        m, lo, hi, _ = self.R.mantel_haenszel([(k, p)])
        sample = (p[1] * k[0]) / (p[0] * k[1])
        self.assertAlmostEqual(m, sample, places=6)
        self.assertLess(lo, m)
        self.assertGreater(hi, m)

    def test_exact_or_is_close_to_sample_or(self):
        o, lo, hi, pv, samp = self.R.exact_or((500, 600), (30, 1300))
        self.assertAlmostEqual(o, samp, delta=samp * 0.02)
        self.assertLess(lo, o)
        self.assertGreater(hi, o)
        self.assertLess(pv, 1e-10)

    def test_case_report_definitions(self):
        R = self.R
        self.assertEqual(R.kampo_type("肝硬変の一例", "A"), "case_report")
        self.assertEqual(R.kampo_type("抑肝散の使用経験", "A"), "case_report")
        self.assertNotEqual(R.kampo_type("抑肝散の使用経験", "B"), "case_report")   # 定義B は題名に「症例」「一例」等
        self.assertEqual(R.kampo_type("咳嗽に対する漢方治療の症例", "B"), "case_report")
        self.assertEqual(R.pubmed_type(["Journal Article", "Case Reports"]), "case_report")
        self.assertEqual(R.pubmed_type(["Randomized Controlled Trial"]), "rct")
        self.assertEqual(R.pubmed_type([]), "basic_other")


if __name__ == "__main__":
    unittest.main()
