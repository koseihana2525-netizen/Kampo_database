"""
Duagnosis Kampo Knowledge Base - Term Dictionaries
漢方用語辞書（方剤名・証関連用語・症状・腹証）

Phase 0 パイロット用
方剤辞書はツムラ医療用漢方製剤の全処方 + 東洋医学雑誌頻出の非ツムラ方剤を収録
"""

# ── 方剤辞書（ツムラ番号 → 方剤名、別名含む） ──
# origin: "経方"=傷寒論/金匱要略由来, "後世方"=後世の医書由来
# aliases: 略称・別表記・ツムラ番号表記など
FORMULAS = {
    # ===== ツムラ医療用漢方製剤（全処方） =====
    1: {"name": "葛根湯", "yomi": "かっこんとう", "origin": "経方",
        "aliases": ["カッコントウ", "TJ-001"]},
    2: {"name": "葛根湯加川芎辛夷", "yomi": "かっこんとうかせんきゅうしんい", "origin": "後世方",
        "aliases": ["TJ-002"]},
    3: {"name": "乙字湯", "yomi": "おつじとう", "origin": "後世方",
        "aliases": ["TJ-003"]},
    5: {"name": "安中散", "yomi": "あんちゅうさん", "origin": "後世方",
        "aliases": ["TJ-005", "アンチュウサン"]},
    6: {"name": "十味敗毒湯", "yomi": "じゅうみはいどくとう", "origin": "後世方",
        "aliases": ["TJ-006"]},
    7: {"name": "八味地黄丸", "yomi": "はちみじおうがん", "origin": "経方",
        "aliases": ["TJ-007", "八味丸", "腎気丸", "ハチミジオウガン"]},
    8: {"name": "大柴胡湯", "yomi": "だいさいことう", "origin": "経方",
        "aliases": ["TJ-008", "ダイサイコトウ"]},
    9: {"name": "小柴胡湯", "yomi": "しょうさいことう", "origin": "経方",
        "aliases": ["TJ-009", "ショウサイコトウ"]},
    10: {"name": "柴胡桂枝湯", "yomi": "さいこけいしとう", "origin": "経方",
         "aliases": ["TJ-010"]},
    11: {"name": "柴胡桂枝乾姜湯", "yomi": "さいこけいしかんきょうとう", "origin": "経方",
         "aliases": ["TJ-011"]},
    12: {"name": "柴胡加竜骨牡蛎湯", "yomi": "さいこかりゅうこつぼれいとう", "origin": "経方",
         "aliases": ["TJ-012", "柴胡加竜骨牡蠣湯"]},
    14: {"name": "半夏瀉心湯", "yomi": "はんげしゃしんとう", "origin": "経方",
         "aliases": ["TJ-014", "ハンゲシャシントウ", "半夏潟心湯"]},
    15: {"name": "黄連解毒湯", "yomi": "おうれんげどくとう", "origin": "後世方",
         "aliases": ["TJ-015"]},
    16: {"name": "半夏厚朴湯", "yomi": "はんげこうぼくとう", "origin": "経方",
         "aliases": ["TJ-016"]},
    17: {"name": "五苓散", "yomi": "ごれいさん", "origin": "経方",
         "aliases": ["TJ-017", "ゴレイサン"]},
    18: {"name": "桂枝加朮附湯", "yomi": "けいしかじゅつぶとう", "origin": "経方",
         "aliases": ["TJ-018"]},
    19: {"name": "小青竜湯", "yomi": "しょうせいりゅうとう", "origin": "経方",
         "aliases": ["TJ-019", "ショウセイリュウトウ"]},
    20: {"name": "防已黄耆湯", "yomi": "ぼういおうぎとう", "origin": "経方",
         "aliases": ["TJ-020", "防巳黄耆湯", "防己黄耆湯"]},
    21: {"name": "小半夏加茯苓湯", "yomi": "しょうはんげかぶくりょうとう", "origin": "経方",
         "aliases": ["TJ-021"]},
    22: {"name": "消風散", "yomi": "しょうふうさん", "origin": "後世方",
         "aliases": ["TJ-022"]},
    23: {"name": "当帰芍薬散", "yomi": "とうきしゃくやくさん", "origin": "経方",
         "aliases": ["TJ-023", "トウキシャクヤクサン", "妊娠時当帰芍薬散"]},
    24: {"name": "加味逍遙散", "yomi": "かみしょうようさん", "origin": "後世方",
         "aliases": ["TJ-024", "カミショウヨウサン", "加味逍遥散"]},
    25: {"name": "桂枝茯苓丸", "yomi": "けいしぶくりょうがん", "origin": "経方",
         "aliases": ["TJ-025", "ケイシブクリョウガン", "自家製桂枝茯苓丸", "桂枝萩苓丸"]},
    26: {"name": "桂枝加竜骨牡蛎湯", "yomi": "けいしかりゅうこつぼれいとう", "origin": "経方",
         "aliases": ["TJ-026"]},
    27: {"name": "麻黄湯", "yomi": "まおうとう", "origin": "経方",
         "aliases": ["TJ-027", "マオウトウ"]},
    28: {"name": "越婢加朮湯", "yomi": "えっぴかじゅつとう", "origin": "経方",
         "aliases": ["TJ-028"]},
    29: {"name": "麦門冬湯", "yomi": "ばくもんどうとう", "origin": "経方",
         "aliases": ["TJ-029", "バクモンドウトウ"]},
    30: {"name": "真武湯", "yomi": "しんぶとう", "origin": "経方",
         "aliases": ["TJ-030", "シンブトウ"]},
    31: {"name": "呉茱萸湯", "yomi": "ごしゅゆとう", "origin": "経方",
         "aliases": ["TJ-031"]},
    32: {"name": "人参湯", "yomi": "にんじんとう", "origin": "経方",
         "aliases": ["TJ-032", "理中湯", "理中丸"]},
    33: {"name": "大黄牡丹皮湯", "yomi": "だいおうぼたんぴとう", "origin": "経方",
         "aliases": ["TJ-033"]},
    34: {"name": "白虎加人参湯", "yomi": "びゃっこかにんじんとう", "origin": "経方",
         "aliases": ["TJ-034"]},
    35: {"name": "四逆散", "yomi": "しぎゃくさん", "origin": "経方",
         "aliases": ["TJ-035"]},
    36: {"name": "木防已湯", "yomi": "もくぼういとう", "origin": "経方",
         "aliases": ["TJ-036", "木防巳湯", "木防己湯"]},
    37: {"name": "半夏白朮天麻湯", "yomi": "はんげびゃくじゅつてんまとう", "origin": "後世方",
         "aliases": ["TJ-037"]},
    38: {"name": "当帰四逆加呉茱萸生姜湯", "yomi": "とうきしぎゃくかごしゅゆしょうきょうとう", "origin": "経方",
         "aliases": ["TJ-038"]},
    39: {"name": "苓桂朮甘湯", "yomi": "りょうけいじゅつかんとう", "origin": "経方",
         "aliases": ["TJ-039"]},
    40: {"name": "猪苓湯", "yomi": "ちょれいとう", "origin": "経方",
         "aliases": ["TJ-040"]},
    41: {"name": "補中益気湯", "yomi": "ほちゅうえっきとう", "origin": "後世方",
         "aliases": ["TJ-041", "ホチュウエッキトウ", "ホチュウ"]},
    43: {"name": "六君子湯", "yomi": "りっくんしとう", "origin": "後世方",
         "aliases": ["TJ-043", "リックンシトウ"]},
    45: {"name": "桂枝湯", "yomi": "けいしとう", "origin": "経方",
         "aliases": ["TJ-045"]},
    46: {"name": "七物降下湯", "yomi": "しちもつこうかとう", "origin": "後世方",
         "aliases": ["TJ-046"]},
    47: {"name": "釣藤散", "yomi": "ちょうとうさん", "origin": "後世方",
         "aliases": ["TJ-047"]},
    48: {"name": "十全大補湯", "yomi": "じゅうぜんたいほとう", "origin": "後世方",
         "aliases": ["TJ-048", "ジュウゼンタイホトウ"]},
    50: {"name": "荊芥連翹湯", "yomi": "けいがいれんぎょうとう", "origin": "後世方",
         "aliases": ["TJ-050"]},
    51: {"name": "薏苡仁湯", "yomi": "よくいにんとう", "origin": "経方",
         "aliases": ["TJ-051"]},
    52: {"name": "薏苡附子敗醤散", "yomi": "よくいぶしはいしょうさん", "origin": "経方",
         "aliases": ["TJ-052"]},
    53: {"name": "疎経活血湯", "yomi": "そけいかっけつとう", "origin": "後世方",
         "aliases": ["TJ-053"]},
    54: {"name": "抑肝散", "yomi": "よくかんさん", "origin": "後世方",
         "aliases": ["TJ-054", "ヨクカンサン"]},
    55: {"name": "麻杏甘石湯", "yomi": "まきょうかんせきとう", "origin": "経方",
         "aliases": ["TJ-055"]},
    56: {"name": "五淋散", "yomi": "ごりんさん", "origin": "後世方",
         "aliases": ["TJ-056"]},
    57: {"name": "温清飲", "yomi": "うんせいいん", "origin": "後世方",
         "aliases": ["TJ-057"]},
    58: {"name": "清上防風湯", "yomi": "せいじょうぼうふうとう", "origin": "後世方",
         "aliases": ["TJ-058"]},
    59: {"name": "治頭瘡一方", "yomi": "ぢずそういっぽう", "origin": "後世方",
         "aliases": ["TJ-059"]},
    60: {"name": "桂枝加芍薬湯", "yomi": "けいしかしゃくやくとう", "origin": "経方",
         "aliases": ["TJ-060"]},
    61: {"name": "桃核承気湯", "yomi": "とうかくじょうきとう", "origin": "経方",
         "aliases": ["TJ-061"]},
    62: {"name": "防風通聖散", "yomi": "ぼうふうつうしょうさん", "origin": "後世方",
         "aliases": ["TJ-062", "ボウフウツウショウサン"]},
    63: {"name": "五積散", "yomi": "ごしゃくさん", "origin": "後世方",
         "aliases": ["TJ-063"]},
    64: {"name": "炙甘草湯", "yomi": "しゃかんぞうとう", "origin": "経方",
         "aliases": ["TJ-064"]},
    65: {"name": "帰脾湯", "yomi": "きひとう", "origin": "後世方",
         "aliases": ["TJ-065"]},
    66: {"name": "参蘇飲", "yomi": "じんそいん", "origin": "後世方",
         "aliases": ["TJ-066"]},
    67: {"name": "女神散", "yomi": "にょしんさん", "origin": "後世方",
         "aliases": ["TJ-067"]},
    68: {"name": "芍薬甘草湯", "yomi": "しゃくやくかんぞうとう", "origin": "経方",
         "aliases": ["TJ-068", "シャクヤクカンゾウトウ"]},
    69: {"name": "茯苓飲", "yomi": "ぶくりょういん", "origin": "経方",
         "aliases": ["TJ-069"]},
    70: {"name": "香蘇散", "yomi": "こうそさん", "origin": "後世方",
         "aliases": ["TJ-070"]},
    71: {"name": "四物湯", "yomi": "しもつとう", "origin": "後世方",
         "aliases": ["TJ-071"]},
    72: {"name": "甘麦大棗湯", "yomi": "かんばくたいそうとう", "origin": "経方",
         "aliases": ["TJ-072"]},
    73: {"name": "柴陥湯", "yomi": "さいかんとう", "origin": "後世方",
         "aliases": ["TJ-073"]},
    74: {"name": "調胃承気湯", "yomi": "ちょういじょうきとう", "origin": "経方",
         "aliases": ["TJ-074"]},
    75: {"name": "四君子湯", "yomi": "しくんしとう", "origin": "後世方",
         "aliases": ["TJ-075"]},
    76: {"name": "竜胆瀉肝湯", "yomi": "りゅうたんしゃかんとう", "origin": "後世方",
         "aliases": ["TJ-076", "竜胆潟肝湯"]},
    77: {"name": "芎帰膠艾湯", "yomi": "きゅうききょうがいとう", "origin": "経方",
         "aliases": ["TJ-077"]},
    78: {"name": "麻杏薏甘湯", "yomi": "まきょうよくかんとう", "origin": "経方",
         "aliases": ["TJ-078"]},
    79: {"name": "平胃散", "yomi": "へいいさん", "origin": "後世方",
         "aliases": ["TJ-079"]},
    80: {"name": "柴胡清肝湯", "yomi": "さいこせいかんとう", "origin": "後世方",
         "aliases": ["TJ-080"]},
    81: {"name": "二陳湯", "yomi": "にちんとう", "origin": "後世方",
         "aliases": ["TJ-081"]},
    82: {"name": "桂枝人参湯", "yomi": "けいしにんじんとう", "origin": "経方",
         "aliases": ["TJ-082"]},
    83: {"name": "抑肝散加陳皮半夏", "yomi": "よくかんさんかちんぴはんげ", "origin": "後世方",
         "aliases": ["TJ-083"]},
    84: {"name": "大黄甘草湯", "yomi": "だいおうかんぞうとう", "origin": "経方",
         "aliases": ["TJ-084"]},
    85: {"name": "神秘湯", "yomi": "しんぴとう", "origin": "後世方",
         "aliases": ["TJ-085"]},
    86: {"name": "当帰飲子", "yomi": "とうきいんし", "origin": "後世方",
         "aliases": ["TJ-086"]},
    87: {"name": "六味丸", "yomi": "ろくみがん", "origin": "後世方",
         "aliases": ["TJ-087", "六味地黄丸"]},
    88: {"name": "二朮湯", "yomi": "にじゅつとう", "origin": "後世方",
         "aliases": ["TJ-088"]},
    89: {"name": "治打撲一方", "yomi": "ぢだぼくいっぽう", "origin": "後世方",
         "aliases": ["TJ-089"]},
    90: {"name": "清肺湯", "yomi": "せいはいとう", "origin": "後世方",
         "aliases": ["TJ-090"]},
    91: {"name": "竹茹温胆湯", "yomi": "ちくじょうんたんとう", "origin": "後世方",
         "aliases": ["TJ-091", "竹如温胆湯", "竹筎温胆湯"]},
    92: {"name": "滋陰至宝湯", "yomi": "じいんしほうとう", "origin": "後世方",
         "aliases": ["TJ-092"]},
    93: {"name": "滋陰降火湯", "yomi": "じいんこうかとう", "origin": "後世方",
         "aliases": ["TJ-093"]},
    95: {"name": "五虎湯", "yomi": "ごことう", "origin": "後世方",
         "aliases": ["TJ-095"]},
    96: {"name": "柴朴湯", "yomi": "さいぼくとう", "origin": "後世方",
         "aliases": ["TJ-096"]},
    97: {"name": "大防風湯", "yomi": "だいぼうふうとう", "origin": "後世方",
         "aliases": ["TJ-097"]},
    98: {"name": "黄耆建中湯", "yomi": "おうぎけんちゅうとう", "origin": "経方",
         "aliases": ["TJ-098"]},
    99: {"name": "小建中湯", "yomi": "しょうけんちゅうとう", "origin": "経方",
         "aliases": ["TJ-099"]},
    100: {"name": "大建中湯", "yomi": "だいけんちゅうとう", "origin": "経方",
          "aliases": ["TJ-100", "ダイケンチュウトウ"]},
    101: {"name": "升麻葛根湯", "yomi": "しょうまかっこんとう", "origin": "後世方",
          "aliases": ["TJ-101"]},
    102: {"name": "当帰湯", "yomi": "とうきとう", "origin": "後世方",
          "aliases": ["TJ-102"]},
    103: {"name": "酸棗仁湯", "yomi": "さんそうにんとう", "origin": "経方",
          "aliases": ["TJ-103"]},
    104: {"name": "辛夷清肺湯", "yomi": "しんいせいはいとう", "origin": "後世方",
          "aliases": ["TJ-104"]},
    105: {"name": "通導散", "yomi": "つうどうさん", "origin": "後世方",
          "aliases": ["TJ-105"]},
    106: {"name": "温経湯", "yomi": "うんけいとう", "origin": "経方",
          "aliases": ["TJ-106"]},
    107: {"name": "牛車腎気丸", "yomi": "ごしゃじんきがん", "origin": "後世方",
          "aliases": ["TJ-107", "ゴシャジンキガン"]},
    108: {"name": "人参養栄湯", "yomi": "にんじんようえいとう", "origin": "後世方",
          "aliases": ["TJ-108", "ニンジンヨウエイトウ"]},
    109: {"name": "小柴胡湯加桔梗石膏", "yomi": "しょうさいことうかききょうせっこう", "origin": "後世方",
          "aliases": ["TJ-109"]},
    110: {"name": "立効散", "yomi": "りっこうさん", "origin": "後世方",
          "aliases": ["TJ-110"]},
    111: {"name": "清心蓮子飲", "yomi": "せいしんれんしいん", "origin": "後世方",
          "aliases": ["TJ-111"]},
    112: {"name": "猪苓湯合四物湯", "yomi": "ちょれいとうごうしもつとう", "origin": "後世方",
          "aliases": ["TJ-112"]},
    113: {"name": "三黄瀉心湯", "yomi": "さんおうしゃしんとう", "origin": "経方",
          "aliases": ["TJ-113"]},
    114: {"name": "柴苓湯", "yomi": "さいれいとう", "origin": "後世方",
          "aliases": ["TJ-114"]},
    115: {"name": "胃苓湯", "yomi": "いれいとう", "origin": "後世方",
          "aliases": ["TJ-115"]},
    116: {"name": "茯苓飲合半夏厚朴湯", "yomi": "ぶくりょういんごうはんげこうぼくとう", "origin": "後世方",
          "aliases": ["TJ-116"]},
    117: {"name": "茵蔯五苓散", "yomi": "いんちんごれいさん", "origin": "経方",
          "aliases": ["TJ-117"]},
    118: {"name": "苓姜朮甘湯", "yomi": "りょうきょうじゅつかんとう", "origin": "経方",
          "aliases": ["TJ-118"]},
    119: {"name": "苓甘姜味辛夏仁湯", "yomi": "りょうかんきょうみしんげにんとう", "origin": "経方",
          "aliases": ["TJ-119"]},
    120: {"name": "黄連湯", "yomi": "おうれんとう", "origin": "経方",
          "aliases": ["TJ-120"]},
    121: {"name": "三物黄芩湯", "yomi": "さんもつおうごんとう", "origin": "経方",
          "aliases": ["TJ-121"]},
    122: {"name": "排膿散及湯", "yomi": "はいのうさんきゅうとう", "origin": "経方",
          "aliases": ["TJ-122"]},
    123: {"name": "当帰建中湯", "yomi": "とうきけんちゅうとう", "origin": "経方",
          "aliases": ["TJ-123"]},
    124: {"name": "川芎茶調散", "yomi": "せんきゅうちゃちょうさん", "origin": "後世方",
          "aliases": ["TJ-124"]},
    125: {"name": "桂枝茯苓丸加薏苡仁", "yomi": "けいしぶくりょうがんかよくいにん", "origin": "後世方",
          "aliases": ["TJ-125"]},
    126: {"name": "麻子仁丸", "yomi": "ましにんがん", "origin": "経方",
          "aliases": ["TJ-126"]},
    127: {"name": "麻黄附子細辛湯", "yomi": "まおうぶしさいしんとう", "origin": "経方",
          "aliases": ["TJ-127", "マオウブシサイシントウ", "麻黄細辛附子湯"]},
    128: {"name": "啓脾湯", "yomi": "けいひとう", "origin": "後世方",
          "aliases": ["TJ-128"]},
    133: {"name": "大承気湯", "yomi": "だいじょうきとう", "origin": "経方",
          "aliases": ["TJ-133"]},
    134: {"name": "桂枝加芍薬大黄湯", "yomi": "けいしかしゃくやくだいおうとう", "origin": "経方",
          "aliases": ["TJ-134"]},
    135: {"name": "茵蔯蒿湯", "yomi": "いんちんこうとう", "origin": "経方",
          "aliases": ["TJ-135"]},
    136: {"name": "清暑益気湯", "yomi": "せいしょえっきとう", "origin": "後世方",
          "aliases": ["TJ-136"]},
    137: {"name": "加味帰脾湯", "yomi": "かみきひとう", "origin": "後世方",
          "aliases": ["TJ-137"]},
    138: {"name": "桔梗湯", "yomi": "ききょうとう", "origin": "経方",
          "aliases": ["TJ-138"]},
}

# ── 非ツムラ方剤（東洋医学雑誌頻出） ──
# ツムラ番号がないもの、他メーカー固有処方、古典処方など
# キーは "E" + 連番（Extra の意）
EXTRA_FORMULAS = {
    "E001": {"name": "黄耆桂枝五物湯", "yomi": "おうぎけいしごもつとう", "origin": "経方", "aliases": []},
    "E002": {"name": "烏頭湯", "yomi": "うずとう", "origin": "経方", "aliases": []},
    "E003": {"name": "越婢加朮附湯", "yomi": "えっぴかじゅつぶとう", "origin": "経方",
             "aliases": ["越婢加朮湯加附子"]},
    "E004": {"name": "黄芩湯", "yomi": "おうごんとう", "origin": "経方", "aliases": ["黄苓湯"]},
    "E005": {"name": "葛根黄連黄芩湯", "yomi": "かっこんおうれんおうごんとう", "origin": "経方", "aliases": []},
    "E006": {"name": "帰耆建中湯", "yomi": "きぎけんちゅうとう", "origin": "後世方", "aliases": []},
    "E007": {"name": "桂枝加黄耆湯", "yomi": "けいしかおうぎとう", "origin": "経方", "aliases": []},
    "E008": {"name": "桂枝加厚朴杏仁湯", "yomi": "けいしかこうぼくきょうにんとう", "origin": "経方", "aliases": []},
    "E009": {"name": "桂麻各半湯", "yomi": "けいまかくはんとう", "origin": "経方", "aliases": []},
    "E010": {"name": "柴胡疎肝湯", "yomi": "さいこそかんとう", "origin": "後世方", "aliases": []},
    "E011": {"name": "十味敗毒湯加荊芥連翹", "yomi": "じゅうみはいどくとうかけいがいれんぎょう", "origin": "後世方", "aliases": []},
    "E012": {"name": "小承気湯", "yomi": "しょうじょうきとう", "origin": "経方", "aliases": []},
    "E013": {"name": "小柴胡湯加味方", "yomi": "しょうさいことうかみほう", "origin": "後世方", "aliases": []},
    "E014": {"name": "逍遙散", "yomi": "しょうようさん", "origin": "後世方", "aliases": []},
    "E015": {"name": "参苓白朮散", "yomi": "じんりょうびゃくじゅつさん", "origin": "後世方", "aliases": []},
    "E016": {"name": "附子理中湯", "yomi": "ぶしりちゅうとう", "origin": "経方", "aliases": ["附子人参湯"]},
    "E017": {"name": "補陽還五湯", "yomi": "ほようかんごとう", "origin": "後世方", "aliases": []},
    "E018": {"name": "独活寄生湯", "yomi": "どっかつきせいとう", "origin": "後世方", "aliases": []},
    "E019": {"name": "十全大補湯加味", "yomi": "じゅうぜんたいほとうかみ", "origin": "後世方", "aliases": []},
    "E020": {"name": "竜骨牡蛎湯", "yomi": "りゅうこつぼれいとう", "origin": "経方", "aliases": []},
    "E021": {"name": "白虎湯", "yomi": "びゃっことう", "origin": "経方", "aliases": []},
    "E022": {"name": "四逆湯", "yomi": "しぎゃくとう", "origin": "経方", "aliases": []},
    "E023": {"name": "潤腸湯", "yomi": "じゅんちょうとう", "origin": "後世方", "aliases": []},
    "E024": {"name": "銀翹散", "yomi": "ぎんぎょうさん", "origin": "後世方", "aliases": []},
    "E025": {"name": "荊防敗毒散", "yomi": "けいぼうはいどくさん", "origin": "後世方", "aliases": []},
    "E026": {"name": "藿香正気散", "yomi": "かっこうしょうきさん", "origin": "後世方", "aliases": []},
    "E027": {"name": "小陥胸湯", "yomi": "しょうかんきょうとう", "origin": "経方", "aliases": []},
    "E028": {"name": "大柴胡湯去大黄", "yomi": "だいさいことうきょだいおう", "origin": "経方", "aliases": []},
    "E029": {"name": "通脈四逆湯", "yomi": "つうみゃくしぎゃくとう", "origin": "経方", "aliases": []},
    "E030": {"name": "杞菊地黄丸", "yomi": "こぎくじおうがん", "origin": "後世方", "aliases": []},
    # ── 東洋医学雑誌のタイトルに出現した古典処方 ──
    "E031": {"name": "茯苓四逆湯", "yomi": "ぶくりょうしぎゃくとう", "origin": "経方", "aliases": []},
    "E032": {"name": "紫雲膏", "yomi": "しうんこう", "origin": "後世方", "aliases": []},
    "E033": {"name": "九味檳榔湯", "yomi": "くみびんろうとう", "origin": "後世方", "aliases": []},
    "E034": {"name": "大青竜湯", "yomi": "だいせいりゅうとう", "origin": "経方", "aliases": []},
    "E035": {"name": "奔豚湯", "yomi": "ほんとんとう", "origin": "経方", "aliases": []},
    "E036": {"name": "甘草瀉心湯", "yomi": "かんぞうしゃしんとう", "origin": "経方", "aliases": []},
    "E037": {"name": "烏頭赤石脂丸", "yomi": "うずせきしゃくしがん", "origin": "経方", "aliases": []},
    "E038": {"name": "桂姜棗草黄辛附湯", "yomi": "けいきょうそうそうおうしんぶとう", "origin": "経方", "aliases": []},
    "E039": {"name": "烏薬順気散", "yomi": "うやくじゅんきさん", "origin": "後世方", "aliases": []},
    "E040": {"name": "蘇子降気湯", "yomi": "そしこうきとう", "origin": "後世方", "aliases": []},
    "E041": {"name": "桂枝麻黄各半湯", "yomi": "けいしまおうかくはんとう", "origin": "経方", "aliases": ["桂麻各半湯"]},
    "E042": {"name": "小続命湯", "yomi": "しょうぞくめいとう", "origin": "後世方", "aliases": []},
    "E043": {"name": "柴葛解肌湯", "yomi": "さいかつげきとう", "origin": "後世方", "aliases": []},
    "E044": {"name": "茯苓杏仁甘草湯", "yomi": "ぶくりょうきょうにんかんぞうとう", "origin": "経方", "aliases": []},
    "E045": {"name": "清熱補血湯", "yomi": "せいねつほけつとう", "origin": "後世方", "aliases": []},
    "E046": {"name": "大陥胸丸", "yomi": "だいかんきょうがん", "origin": "経方", "aliases": []},
    "E047": {"name": "大陥胸湯", "yomi": "だいかんきょうとう", "origin": "経方", "aliases": []},
    "E048": {"name": "茯苓沢瀉湯", "yomi": "ぶくりょうたくしゃとう", "origin": "経方", "aliases": []},
    "E049": {"name": "腸癰湯", "yomi": "ちょうようとう", "origin": "経方", "aliases": []},
    "E050": {"name": "麗沢通気湯", "yomi": "れいたくつうきとう", "origin": "後世方", "aliases": ["麗澤通気湯"]},
    "E051": {"name": "薯蕷丸", "yomi": "しょよがん", "origin": "経方", "aliases": []},
    "E052": {"name": "沢瀉湯", "yomi": "たくしゃとう", "origin": "経方", "aliases": []},
    "E053": {"name": "白朮附子湯", "yomi": "びゃくじゅつぶしとう", "origin": "経方", "aliases": []},
    "E054": {"name": "甘草附子湯", "yomi": "かんぞうぶしとう", "origin": "経方", "aliases": []},
    "E055": {"name": "養腎降濁湯", "yomi": "ようじんこうだくとう", "origin": "後世方", "aliases": []},
    "E056": {"name": "正気天香湯", "yomi": "せいきてんこうとう", "origin": "後世方", "aliases": []},
    "E057": {"name": "伯州散", "yomi": "はくしゅうさん", "origin": "後世方", "aliases": []},
    "E058": {"name": "土瓜根散", "yomi": "どかこんさん", "origin": "経方", "aliases": []},
    "E059": {"name": "白通湯", "yomi": "はくつうとう", "origin": "経方", "aliases": []},
    "E060": {"name": "桂枝二越婢一湯", "yomi": "けいしにえっぴいちとう", "origin": "経方", "aliases": []},
    "E061": {"name": "抵当丸", "yomi": "ていとうがん", "origin": "経方", "aliases": []},
    "E062": {"name": "高枕無憂散", "yomi": "こうちんむゆうさん", "origin": "後世方", "aliases": []},
    "E063": {"name": "順気和中湯", "yomi": "じゅんきわちゅうとう", "origin": "後世方", "aliases": []},
    "E064": {"name": "香砂平胃散", "yomi": "こうしゃへいいさん", "origin": "後世方", "aliases": []},
    "E065": {"name": "生姜半夏甘草人参湯", "yomi": "しょうきょうはんげかんぞうにんじんとう", "origin": "経方", "aliases": []},
    "E066": {"name": "中黄膏", "yomi": "ちゅうおうこう", "origin": "後世方", "aliases": []},
    "E067": {"name": "利隔湯", "yomi": "りかくとう", "origin": "後世方", "aliases": []},
    "E068": {"name": "越婢加半夏湯", "yomi": "えっぴかはんげとう", "origin": "経方", "aliases": []},
    "E069": {"name": "茯苓桂枝甘草大棗湯", "yomi": "ぶくりょうけいしかんぞうたいそうとう", "origin": "経方", "aliases": []},
    "E070": {"name": "大黄附子湯", "yomi": "だいおうぶしとう", "origin": "経方", "aliases": []},
    "E071": {"name": "神仙太乙膏", "yomi": "しんせんたいつこう", "origin": "後世方", "aliases": ["太乙膏"]},
    "E072": {"name": "甘草湯", "yomi": "かんぞうとう", "origin": "経方", "aliases": []},
    "E073": {"name": "大黄甘遂湯", "yomi": "だいおうかんすいとう", "origin": "経方", "aliases": []},
    "E074": {"name": "胆道排石湯", "yomi": "たんどうはいせきとう", "origin": "後世方", "aliases": []},
    "E075": {"name": "分消湯", "yomi": "ぶんしょうとう", "origin": "後世方", "aliases": []},
    "E076": {"name": "牡蠣沢瀉散", "yomi": "ぼれいたくしゃさん", "origin": "経方", "aliases": []},
    "E077": {"name": "烏頭桂枝湯", "yomi": "うずけいしとう", "origin": "経方", "aliases": []},
    "E078": {"name": "桂枝附子湯", "yomi": "けいしぶしとう", "origin": "経方", "aliases": []},
    "E079": {"name": "梔子柏皮湯", "yomi": "ししはくひとう", "origin": "経方", "aliases": []},
    "E080": {"name": "厚朴三物湯", "yomi": "こうぼくさんもつとう", "origin": "経方", "aliases": []},
    "E081": {"name": "催生湯", "yomi": "さいせいとう", "origin": "後世方", "aliases": []},
    "E082": {"name": "百合固金湯", "yomi": "びゃくごうこきんとう", "origin": "後世方", "aliases": []},
    "E083": {"name": "温脾湯", "yomi": "うんぴとう", "origin": "後世方", "aliases": []},
    "E084": {"name": "三黄湯", "yomi": "さんおうとう", "origin": "後世方", "aliases": []},
    "E085": {"name": "解労散", "yomi": "かいろうさん", "origin": "後世方", "aliases": []},
    "E086": {"name": "清湿化痰湯", "yomi": "せいしつけたんとう", "origin": "後世方", "aliases": []},
    "E087": {"name": "葛根紅花湯", "yomi": "かっこんこうかとう", "origin": "後世方", "aliases": []},
    "E088": {"name": "清脾除湿飲", "yomi": "せいひじょしついん", "origin": "後世方", "aliases": []},
    "E089": {"name": "桂枝加苓朮附湯", "yomi": "けいしかりょうじゅつぶとう", "origin": "経方", "aliases": []},
    "E090": {"name": "昇陥湯", "yomi": "しょうかんとう", "origin": "後世方", "aliases": []},
    "E091": {"name": "清熱補気湯", "yomi": "せいねつほきとう", "origin": "後世方", "aliases": []},
    "E092": {"name": "白虎加桂枝湯", "yomi": "びゃっこかけいしとう", "origin": "経方", "aliases": []},
    "E093": {"name": "当帰六黄湯", "yomi": "とうきりくおうとう", "origin": "後世方", "aliases": []},
    "E094": {"name": "桂枝加桂湯", "yomi": "けいしかけいとう", "origin": "経方", "aliases": []},
    "E095": {"name": "厚朴七物湯", "yomi": "こうぼくしちもつとう", "origin": "経方", "aliases": []},
    "E096": {"name": "茯苓甘草湯", "yomi": "ぶくりょうかんぞうとう", "origin": "経方", "aliases": []},
    "E097": {"name": "明朗飲", "yomi": "めいろういん", "origin": "後世方", "aliases": []},
    "E098": {"name": "苓桂甘棗湯", "yomi": "りょうけいかんそうとう", "origin": "経方", "aliases": []},
    "E099": {"name": "苓桂五味甘草湯", "yomi": "りょうけいごみかんぞうとう", "origin": "経方", "aliases": []},
    "E100": {"name": "八味丸", "yomi": "はちみがん", "origin": "経方", "aliases": []},
    "E101": {"name": "柴蘇飲", "yomi": "さいそいん", "origin": "後世方", "aliases": []},
    "E102": {"name": "選奇湯", "yomi": "せんきとう", "origin": "後世方", "aliases": []},
    "E103": {"name": "半夏人参甘草湯", "yomi": "はんげにんじんかんぞうとう", "origin": "経方", "aliases": []},
    "E104": {"name": "玉屏風散", "yomi": "ぎょくへいふうさん", "origin": "後世方", "aliases": []},
    "E105": {"name": "防已茯苓湯", "yomi": "ぼういぶくりょうとう", "origin": "経方", "aliases": ["防己茯苓湯"]},
    "E106": {"name": "柿蔕湯", "yomi": "していとう", "origin": "後世方", "aliases": []},
    "E107": {"name": "芎帰調血飲", "yomi": "きゅうきちょうけついん", "origin": "後世方", "aliases": ["帰調血飲"]},
    "E108": {"name": "提肛散", "yomi": "ていこうさん", "origin": "後世方", "aliases": []},
    "E109": {"name": "百合滑石散", "yomi": "びゃくごうかっせきさん", "origin": "経方", "aliases": []},
    "E110": {"name": "桂枝去芍薬加皂莢湯", "yomi": "けいしきょしゃくやくかそうきょうとう", "origin": "経方", "aliases": []},
    "E111": {"name": "血府逐瘀湯", "yomi": "けっぷちくおとう", "origin": "後世方", "aliases": []},
    "E112": {"name": "千金内托散", "yomi": "せんきんないたくさん", "origin": "後世方", "aliases": []},
    "E113": {"name": "霊梅散", "yomi": "れいばいさん", "origin": "後世方", "aliases": []},
    "E114": {"name": "梔子乾姜湯", "yomi": "ししかんきょうとう", "origin": "経方", "aliases": []},
    "E115": {"name": "梔子豉湯", "yomi": "しししとう", "origin": "経方", "aliases": []},
    "E116": {"name": "麻黄連軺赤小豆湯", "yomi": "まおうれんしょうせきしょうずとう", "origin": "経方", "aliases": []},
    "E117": {"name": "温胆湯", "yomi": "うんたんとう", "origin": "後世方", "aliases": []},
    "E118": {"name": "良枳湯", "yomi": "りょうきとう", "origin": "後世方", "aliases": []},
    "E119": {"name": "通脈四逆湯", "yomi": "つうみゃくしぎゃくとう", "origin": "経方", "aliases": []},
    "E120": {"name": "大桃花湯", "yomi": "だいとうかとう", "origin": "経方", "aliases": []},
    "E121": {"name": "橘皮枳実生姜湯", "yomi": "きっぴきじつしょうきょうとう", "origin": "経方", "aliases": []},
    "E122": {"name": "活勝湿湯", "yomi": "かっしょうしつとう", "origin": "後世方", "aliases": []},
    # ── 先生確認済み（2025-03-24） ──
    "E123": {"name": "中建中湯", "yomi": "ちゅうけんちゅうとう", "origin": "後世方", "aliases": []},
    "E124": {"name": "竜骨湯", "yomi": "りゅうこつとう", "origin": "後世方", "aliases": []},  # 外台秘要方
    "E125": {"name": "十味剉散", "yomi": "じゅうみざさん", "origin": "後世方", "aliases": []},  # 勿誤薬室方函口訣
    "E126": {"name": "大三五七散", "yomi": "だいさんごしちさん", "origin": "後世方", "aliases": []},  # 勿誤薬室方函口訣
    "E127": {"name": "変製心気飲", "yomi": "へんせいしんきいん", "origin": "後世方", "aliases": []},  # 勿誤薬室方函口訣
    "E128": {"name": "四味膠艾湯", "yomi": "しみきょうがいとう", "origin": "後世方", "aliases": []},  # 矢数道明
    "E129": {"name": "大黄丸", "yomi": "だいおうがん", "origin": "経方", "aliases": []},
    # ── 合方（東洋医学雑誌タイトルに出現） ──
    "G001": {"name": "香蘇散合六君子湯", "yomi": "こうそさんごうりっくんしとう", "origin": "合方", "aliases": []},
    "G002": {"name": "人参養栄湯合香蘇散", "yomi": "にんじんようえいとうごうこうそさん", "origin": "合方", "aliases": []},
    "G003": {"name": "六味丸合酸棗仁湯", "yomi": "ろくみがんごうさんそうにんとう", "origin": "合方", "aliases": []},
    "G004": {"name": "女神散合逍遥散", "yomi": "にょしんさんごうしょうようさん", "origin": "合方", "aliases": []},
    "G005": {"name": "柴胡四物湯合猪苓湯", "yomi": "さいこしもつとうごうちょれいとう", "origin": "合方", "aliases": []},
}

# ── 誤抽出除外リスト ──
# 文字化け・HTMLエンティティ・文章断片による偽陽性
FORMULA_EXCLUDE = {
    # 文字化け由来（元の文字が〓等に化けて方剤名が不完全に抽出）
    "苡仁湯",        # ← 薏苡仁湯の「薏」欠落
    "帰膠艾湯",      # ← 芎帰膠艾湯の「芎」欠落
    "根加朮附湯",    # ← 葛根加朮附湯の「葛」欠落
    "茶調散",        # ← 川芎茶調散の「川芎」欠落
    "赤小豆湯",      # ← 麻黄連軺赤小豆湯の部分
    "楼薤白白酒湯",  # ← 栝楼薤白白酒湯の「栝」欠落
    "楼薤白半夏湯",  # ← 栝楼薤白半夏湯の「栝」欠落
    # 「合〜」表記の断片（最長一致で本来の合方が取れるはずだが念のため）
    "合半夏厚朴湯",
    "合桂枝茯苓丸",
    "合黄連解毒湯",
    "合麻黄附子細辛湯",
    "合苓桂朮甘湯",
    "合白虎加人参湯",
    "合薏苡仁湯",
    "加石膏",         # ← 「白虎加人参湯エキス加石膏末」の断片
    # 文脈の断片
    "類含有口腔軟膏", # ← 「ナフトキノン類含有口腔軟膏」
    "自家製丸",       # ← 「自家製丸薬調剤」
    "経過中黄連解毒湯", # ← 文脈の一部
    "鍼灸湯",         # ← 「鍼灸湯液併用治療」
    # 表記ゆれ断片（最長一致済みだが念のため）
    "枝去桂加茯苓白朮湯",   # ← 桂枝去桂加茯苓白朮湯の「桂」欠落
    "枝去桂加萩苓白朮湯",   # ← 同上の異体字版
    # 合方の「尤湯」部分（越婢加朮湯の表記ゆれ断片）
    "尤湯合半夏厚朴湯",
    # 「胡去半夏加括模根湯」← 小柴胡去半夏加栝楼根湯の文字化け
    "胡去半夏加括模根湯",
    # 撲一方の断片
    "撲一方合疎経活血湯",
    # 蒿湯の断片
    "蒿湯合五苓散",
    # 帰調血飲の断片
    "帰調血飲",
}


# ── 証関連用語辞書 ──
# カテゴリ別に整理
PATTERN_TERMS = {
    "八綱弁証": {
        "寒熱": ["寒証", "熱証", "寒熱錯雑", "真寒仮熱", "真熱仮寒", "悪寒", "発熱", "微熱", "潮熱"],
        "虚実": ["虚証", "実証", "虚実中間", "虚実挟雑", "正虚邪実"],
        "表裏": ["表証", "裏証", "半表半裏", "表裏同病"],
        "陰陽": ["陰証", "陽証", "陰虚", "陽虚", "陰盛", "陽盛"],
    },
    "気血津液弁証": {
        "気": ["気虚", "気滞", "気逆", "気陥", "気鬱"],
        "血": ["血虚", "瘀血", "血熱", "血寒", "出血"],
        "津液": ["津液不足", "痰飲", "水滞", "水毒", "浮腫", "痰湿"],
    },
    "臓腑弁証": {
        "肝": ["肝気鬱結", "肝火上炎", "肝陰虚", "肝血虚", "肝風内動", "肝鬱化火"],
        "心": ["心気虚", "心血虚", "心陰虚", "心火亢盛", "心脾両虚"],
        "脾": ["脾気虚", "脾陽虚", "脾虚湿困", "脾胃虚弱", "脾胃湿熱"],
        "肺": ["肺気虚", "肺陰虚", "風寒犯肺", "風熱犯肺", "痰熱壅肺"],
        "腎": ["腎陽虚", "腎陰虚", "腎精不足", "腎気不固"],
    },
    "六経弁証": {
        "太陽病": ["太陽病", "太陽病中風", "太陽病傷寒"],
        "少陽病": ["少陽病", "少陽証"],
        "陽明病": ["陽明病", "陽明腑実"],
        "太陰病": ["太陰病"],
        "少陰病": ["少陰病"],
        "厥陰病": ["厥陰病"],
    },
}

# ── 腹証用語辞書（日本漢方特有） ──
ABDOMINAL_TERMS = [
    "胸脇苦満", "心下痞", "心下痞硬", "腹力", "腹直筋緊張",
    "臍上悸", "臍下不仁", "小腹急結", "小腹不仁",
    "振水音", "腸雷鳴", "瘀血圧痛点", "正中芯",
    "胃内停水", "少腹拘急", "裏急後重",
]

# ── 症状用語辞書 ──
SYMPTOM_TERMS = {
    "全身": ["倦怠感", "疲労", "全身倦怠感", "食欲不振", "体重減少", "発熱", "悪寒", "盗汗", "自汗"],
    "頭頸部": ["頭痛", "めまい", "耳鳴", "咽頭痛", "口渇", "口内炎", "鼻閉", "鼻汁"],
    "呼吸器": ["咳嗽", "喀痰", "呼吸困難", "喘鳴", "胸痛", "息切れ"],
    "消化器": ["腹痛", "悪心", "嘔吐", "下痢", "便秘", "腹部膨満", "胃痛", "食欲低下"],
    "循環器": ["動悸", "胸痛", "浮腫", "冷え", "のぼせ", "手足の冷え"],
    "精神神経": ["不眠", "不安", "イライラ", "抑うつ", "易怒性", "健忘"],
    "筋骨格": ["腰痛", "関節痛", "筋肉痛", "肩こり", "しびれ"],
    "皮膚": ["湿疹", "蕁麻疹", "掻痒感", "乾燥肌", "アトピー性皮膚炎"],
    "泌尿生殖": ["頻尿", "排尿困難", "月経不順", "月経痛", "更年期障害", "不妊"],
}


def get_all_formula_names():
    """全方剤名のリスト（検索用）- ツムラ + 非ツムラ + 別名"""
    names = []
    for num, info in FORMULAS.items():
        names.append(info["name"])
        names.append(f"ツムラ{num}")
        names.append(f"TJ-{num:03d}")
        for alias in info.get("aliases", []):
            names.append(alias)
    for key, info in EXTRA_FORMULAS.items():
        names.append(info["name"])
        for alias in info.get("aliases", []):
            names.append(alias)
    return names


def get_formula_info(name):
    """方剤名から詳細情報を取得（別名検索対応）"""
    # ツムラ方剤を検索
    for num, info in FORMULAS.items():
        if info["name"] == name:
            return {**info, "tsumura_no": num, "source": "tsumura"}
        if name in info.get("aliases", []):
            return {**info, "tsumura_no": num, "source": "tsumura"}
    # 非ツムラ方剤を検索
    for key, info in EXTRA_FORMULAS.items():
        if info["name"] == name:
            return {**info, "tsumura_no": None, "source": "extra", "extra_key": key}
        if name in info.get("aliases", []):
            return {**info, "tsumura_no": None, "source": "extra", "extra_key": key}
    return None


def get_all_pattern_terms():
    """全証関連用語のフラットリスト"""
    terms = []
    for category, subcats in PATTERN_TERMS.items():
        for subcat, term_list in subcats.items():
            terms.extend(term_list)
    terms.extend(ABDOMINAL_TERMS)
    return terms


def get_all_symptom_terms():
    """全症状用語のフラットリスト"""
    terms = []
    for category, term_list in SYMPTOM_TERMS.items():
        terms.extend(term_list)
    return terms


if __name__ == "__main__":
    n_tsumura = len(FORMULAS)
    n_extra = len(EXTRA_FORMULAS)
    n_keipo = sum(1 for f in FORMULAS.values() if f["origin"] == "経方")
    n_gosei = sum(1 for f in FORMULAS.values() if f["origin"] == "後世方")
    n_extra_keipo = sum(1 for f in EXTRA_FORMULAS.values() if f["origin"] == "経方")
    n_extra_gosei = sum(1 for f in EXTRA_FORMULAS.values() if f["origin"] == "後世方")

    print(f"ツムラ方剤数: {n_tsumura}")
    print(f"  経方: {n_keipo}")
    print(f"  後世方: {n_gosei}")
    print(f"非ツムラ方剤数: {n_extra}")
    print(f"  経方: {n_extra_keipo}")
    print(f"  後世方: {n_extra_gosei}")
    print(f"合計方剤数: {n_tsumura + n_extra}")
    print(f"証関連用語数: {len(get_all_pattern_terms())}")
    print(f"症状用語数: {len(get_all_symptom_terms())}")
    print(f"検索用方剤名数（別名含む）: {len(get_all_formula_names())}")
