# -*- coding: utf-8 -*-
"""
romaji.py - ひらがなの読み（yomi）をヘボン式ローマ字に変換する

方剤名の読みから英語論文中のローマ字表記を作るために使う。
clean_pubmed.py と gap_classifier.py が共有する（以前は clean_pubmed.py の中にあった）。

yomi_to_romaji は長音を残す素朴なヘボン式で、促音は 't' になる（りっくんしとう → ritkunshitou）。
英語論文で使われる表記（Rikkunshito, Shosaikoto）とは一致しない。clean_pubmed.py は従来の出力に依存するので変えていない。
英語論文の表記に合わせるときは yomi_to_romaji_variants を使う。
"""
import re

HEPBURN = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "っ": "t",
}


def yomi_to_romaji(yomi):
    result = ""
    i = 0
    while i < len(yomi):
        if i + 1 < len(yomi) and yomi[i : i + 2] in HEPBURN:
            result += HEPBURN[yomi[i : i + 2]]
            i += 2
        elif yomi[i] in HEPBURN:
            result += HEPBURN[yomi[i]]
            i += 1
        else:
            i += 1
    return result


def _kana_to_romaji(yomi):
    """促音は次の子音を重ねる（りっく → rikku）。長音は仮名どおり（しょう → shou）"""
    out = ""
    i = 0
    double = False
    while i < len(yomi):
        ch = yomi[i]
        if ch == "っ":
            double = True
            i += 1
            continue
        if i + 1 < len(yomi) and yomi[i : i + 2] in HEPBURN:
            syl = HEPBURN[yomi[i : i + 2]]
            i += 2
        elif ch in HEPBURN:
            syl = HEPBURN[ch]
            i += 1
        else:
            i += 1
            continue
        if double:
            syl = ("t" + syl) if syl.startswith("ch") else syl[0] + syl
            double = False
        out += syl
    return out


def yomi_to_romaji_variants(yomi):
    """英語論文で使われる綴りの集合: 長音を残す形（shousaikotou）と、長音を畳んだ形（shosaikoto）"""
    full = _kana_to_romaji(yomi)
    short = re.sub(r"ou|oo|uu", lambda m: m.group(0)[0], full)
    return {full, short}
