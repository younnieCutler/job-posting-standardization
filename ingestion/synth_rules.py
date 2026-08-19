"""Generation rules/pools for synthetic job postings.

Role axis (job family / company / tier / location) is independent of the golden set.
Pattern axis below is reverse-engineered from docs/golden-set/real-postings-golden-set.csv.
See plan/2026-07-19-synthetic-dataset-generator.md for the original design and
2026-08-18 golden-set notes (JDF-Canonical-Schema-v1 / compatibility-delta) for the
tier/platform/location updates layered on top of it.
"""

# code identifier (English) -> real Japanese job titles observed in the market
JOB_FAMILY_GROUPS = {
    "software_development": [
        "Webエンジニア", "バックエンドエンジニア", "フロントエンドエンジニア",
        "アプリケーションエンジニア", "業務系SE",
    ],
    "infrastructure_platform": [
        "インフラエンジニア", "サーバーエンジニア", "ネットワークエンジニア",
        "クラウドエンジニア", "SRE", "Corporate SRE", "プラットフォームエンジニア",
    ],
    "data_ai": [
        "データエンジニア", "データ基盤エンジニア", "データサイエンティスト",
        "AIエンジニア", "機械学習エンジニア",
    ],
    "security_qa": [
        "セキュリティエンジニア", "QAエンジニア", "品質管理", "テストエンジニア",
    ],
    "architecture_consulting": [
        "ソリューションアーキテクト", "ITアーキテクト", "システムアーキテクト",
        "プリセールス", "ITコンサルタント",
    ],
    "corporate_it_support": [
        "社内SE", "情報システム", "テクニカルサポート", "ヘルプデスク",
    ],
}

# 2026-08-18 delta 1: 3-tier -> 5-tier + null/unknown exception path. null/unknown are
# generated on a separate low-rate exception path, never mixed into the normal
# tier/salary-band distribution below (see build_tier_exception_roles in the generator).
SENIORITY_TIERS = ["junior", "mid", "senior", "lead", "principal"]
TIER_EXCEPTIONS = ["null", "unknown"]
TIER_EXCEPTION_RATE = 0.03  # small fraction of total roles, per exception path

TIER_THRESHOLD_PHRASES = {
    "junior": ["実務経験1年以上", "何らかの開発言語での実務経験1年以上歓迎"],
    "mid": ["実務経験3年以上", "SQL・データ抽出経験3年以上"],
    "senior": ["実務経験5年以上", "シニアクラスの実務経験5年以上"],
    "lead": ["実務経験7年以上+チームリード経験", "リーダー候補としての実務経験7年以上"],
    "principal": ["実務経験10年以上+複数プロジェクトのアーキテクト経験", "エキスパートクラスの実務経験10年以上相当"],
}

# blended_tier pattern: which neighbor tier gets mixed in when TIER_BLEND_RATE triggers
TIER_BLEND_NEIGHBORS = {
    "junior": "mid", "mid": "senior", "senior": "lead", "lead": "principal", "principal": "lead",
}

# tier-linked base salary band (万円) before per-role jitter
SALARY_BANDS_MAN_YEN = {
    "junior": (350, 500),
    "mid": (500, 700),
    "senior": (700, 900),
    "lead": (900, 1100),
    "principal": (1100, 1400),
}

# 2026-08-18 delta 3: location_raw is new (Canonical Schema v1 §1). Prefecture-level +
# full-remote, weighted toward Tokyo/major metros like the real Japan IT job market.
LOCATION_POOL = {
    "東京都": 45, "大阪府": 12, "神奈川県": 10, "愛知県": 6,
    "福岡県": 6, "フルリモート": 15, "北海道": 3, "京都府": 3,
}

# Japanese label variants observed for the same logical field across platforms
FIELD_NAME_VARIANTS = {
    "job_description": ["職務内容", "仕事内容"],
    "requirements": ["必須要件", "応募資格"],
    "preferred": ["歓迎要件", "尚可条件", "求める経験・スキル"],
    "location": ["勤務地", "勤務地・エリア"],
}

SALARY_TYPE_FORMATS = {
    "年俸制": "年収{min}万〜{max}万円（年俸制）",
    "月給+賞与制": "月給{min_m}万〜{max_m}万円+賞与年2回（予定年収{min}万〜{max}万円）",
    "月給制": "月給{min_m}万円（賞与なし）",
}

PREFERRED_REQUIREMENT_POOL = [
    "AWSまたはGCP実務経験",
    "Python実務経験",
    "チームでの開発経験",
    "上流工程（要件定義）経験",
    "SQL実務経験",
]

COVERAGE_GAP_RATE = 0.3
TIER_BLEND_RATE = 0.15

# real companies from the golden set — must never appear in generated output
BLOCKED_COMPANY_NAMES = {
    "NHNテコラス", "hokan", "ニジボックス",
    "ビズリーチ", "Ascent Business Consulting", "ABEJA", "アポロ",
    "Japan Digital Design 株式会社", "ディップ株式会社", "ファンズ株式会社",
    "株式会社MonotaRO", "株式会社Photosynth", "株式会社SmartHR",
    "株式会社アプトポッド", "株式会社インテージテクノスフィア", "株式会社エクサ",
    "株式会社サーバーワークス", "株式会社システナ", "株式会社ブシロード",
    "株式会社マネーフォワード", "株式会社電通デジタル",
}

EMPLOYMENT_TYPE = "正社員"  # per user decision 2026-07-19: 정사원으로 충분함

# 2026-08-18 delta 2: source_a/b/c -> 7 real platform names (Canonical Schema v1
# source_platform enum). Missing-field rates are placeholders (가안) inferred from the
# 19-case golden set (small sample, low confidence) — replace with measured rates once
# Raw Ingestion (batch-ingestion item 11) accumulates real volume.
PLATFORM_PROFILES = {
    "hrmos": {"salary_blank_rate": 0.4, "posted_at_rate": 0.5, "agency_rate": 0.0},
    "doda": {"salary_blank_rate": 0.1, "posted_at_rate": 0.8, "agency_rate": 0.3},
    "geekly": {"salary_blank_rate": 0.05, "posted_at_rate": 0.7, "agency_rate": 0.9},
    "openwork": {"salary_blank_rate": 0.6, "posted_at_rate": 0.3, "agency_rate": 0.0},
    "mid_tenshoku": {"salary_blank_rate": 0.2, "posted_at_rate": 0.6, "agency_rate": 0.4},
    "talentio": {"salary_blank_rate": 0.3, "posted_at_rate": 0.4, "agency_rate": 0.0},
    "company_site": {"salary_blank_rate": 0.5, "posted_at_rate": 0.1, "agency_rate": 0.0},
}
