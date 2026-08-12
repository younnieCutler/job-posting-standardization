"""Generation rules/pools for synthetic job postings.

Role axis (job family / company / tier) is independent of the golden set.
Pattern axis below is reverse-engineered from docs/golden-set/real-postings-golden-set.csv.
See plan/2026-07-19-synthetic-dataset-generator.md for the design rationale.
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

SENIORITY_TIERS = ["junior", "mid", "expert"]

# two independently-worded threshold phrasings per tier
# (golden-set blended_tier pattern: "SQL3年以上" vs "実務経験3年以上" for the same tier)
TIER_THRESHOLD_PHRASES = {
    "junior": ["実務経験1年以上", "何らかの開発言語での実務経験1年以上歓迎"],
    "mid": ["実務経験3年以上", "SQL・データ抽出経験3年以上"],
    "expert": ["実務経験5年以上+チームリード経験", "大規模データ基盤の実務経験5年以上相当（テックリード経験歓迎）"],
}

# blended_tier pattern: which neighbor tier gets mixed in when TIER_BLEND_RATE triggers
TIER_BLEND_NEIGHBORS = {"junior": "mid", "mid": "expert", "expert": "mid"}

# tier-linked base salary band (万円) before per-role jitter
SALARY_BANDS_MAN_YEN = {
    "junior": (350, 500),
    "mid": (500, 750),
    "expert": (750, 1100),
}

# Japanese label variants observed for the same logical field across platforms
FIELD_NAME_VARIANTS = {
    "job_description": ["職務内容", "仕事内容"],
    "requirements": ["必須要件", "応募資格"],
    "preferred": ["歓迎要件", "尚可条件", "求める経験・スキル"],
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
}

EMPLOYMENT_TYPE = "正社員"  # per user decision 2026-07-19: 정사원으로 충분함
