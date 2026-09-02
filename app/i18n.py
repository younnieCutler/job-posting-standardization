"""대시보드 다국어 문자열 (한국어 / 日本語 / English)."""

LANGS = {"한국어": "ko", "日本語": "ja", "English": "en"}

STR = {
    "app_title": {
        "ko": "TechHire Nexus Japan — 일본 IT 엔지니어 노동시장 인텔리전스",
        "ja": "TechHire Nexus Japan — 日本ITエンジニア 労働市場インテリジェンス",
        "en": "TechHire Nexus Japan — Japan IT Engineer Labour Market Intelligence",
    },
    "app_subtitle": {
        "ko": "여러 채용 채널의 공고를 표준화한 B2B 시장 분석 리포트 (Revelio Labs·HRog 같은 노동시장 인텔리전스 제품). 구독: 대기업 HR·TA 부서.",
        "ja": "複数の採用チャネルの求人を標準化した B2B 市場分析レポート（Revelio Labs・HRog のような労働市場インテリジェンス製品）。購読対象：大手企業の HR・TA 部門。",
        "en": "A B2B market-analysis report built on job postings standardized across channels (a labour-market-intelligence product in the vein of Revelio Labs / HRog). Subscribers: enterprise HR / TA teams.",
    },
    "source_bq": {
        "ko": "데이터 출처: BigQuery `{ref}` — dbt 검증 통과",
        "ja": "データ出典：BigQuery `{ref}` — dbt テスト合格",
        "en": "Data source: BigQuery `{ref}` — dbt tests passed",
    },
    "source_local": {
        "ko": "데이터 출처: 로컬 parquet `{ref}` (BigQuery 미연결)",
        "ja": "データ出典：ローカル parquet `{ref}`（BigQuery 未接続）",
        "en": "Data source: local parquet `{ref}` (BigQuery not connected)",
    },
    "source_local_fallback": {
        "ko": "BigQuery 접근 실패 → 로컬 parquet로 폴백 ({err})",
        "ja": "BigQuery アクセス失敗 → ローカル parquet にフォールバック（{err}）",
        "en": "BigQuery access failed → fell back to local parquet ({err})",
    },
    "kpi_postings": {"ko": "분석 공고 수", "ja": "分析対象 求人数", "en": "Postings analyzed"},
    "kpi_companies": {"ko": "커버 기업 수", "ja": "カバー企業数", "en": "Companies covered"},
    "kpi_families": {"ko": "직무군", "ja": "職種グループ", "en": "Job families"},
    "kpi_platforms": {"ko": "채널(플랫폼)", "ja": "チャネル（媒体）", "en": "Channels"},
    "kpi_norm": {
        "ko": "표준화로 통합된 표기",
        "ja": "標準化で統合した表記",
        "en": "Notations unified by standardization",
    },
    "kpi_norm_help": {
        "ko": "우대요건 필드명·급여 표기·직무명 원문의 서로 다른 표기 수 → 정규 값 수",
        "ja": "歓迎要件フィールド名・給与表記・職種名原文の異なる表記数 → 正規値数",
        "en": "Distinct raw notations (preferred-req field name, salary format, raw title) → normalized values",
    },
    "sec1_title": {"ko": "1. 기술 수요", "ja": "1. スキル需要", "en": "1. Skill demand"},
    "sec1_who": {
        "ko": "읽는 사람: 채용 계획을 세우는 HR·TA 리더 — \"지금 시장이 어떤 기술을 뽑고 있나\"",
        "ja": "読者：採用計画を立てる HR・TA リーダー —「いま市場はどのスキルを採用しているか」",
        "en": "Reader: HR / TA leaders planning hiring — \"what skills is the market hiring for right now\"",
    },
    "sec1_chart": {
        "ko": "canonical 스킬별 공고 수 (표기 변형 합산 후)",
        "ja": "canonical スキル別 求人数（表記ゆれ統合後）",
        "en": "Postings per canonical skill (after merging notation variants)",
    },
    "sec1_family_filter": {"ko": "직무군 필터", "ja": "職種グループで絞り込み", "en": "Filter by job family"},
    "sec1_all": {"ko": "전체", "ja": "すべて", "en": "All"},
    "sec2_title": {"ko": "2. 급여 벤치마크", "ja": "2. 給与ベンチマーク", "en": "2. Salary benchmark"},
    "sec2_who": {
        "ko": "읽는 사람: 오퍼 금액을 정하는 리더 — \"우리 오퍼가 시장 대비 어디에 있나\"",
        "ja": "読者：オファー額を決めるリーダー —「自社オファーは市場に対してどこか」",
        "en": "Reader: leaders setting offer levels — \"where does our offer sit vs. the market\"",
    },
    "sec2_band": {
        "ko": "직무군 × 티어별 연봉 밴드 (만엔, 최소–중앙값–최대)",
        "ja": "職種グループ × ティア別 年収バンド（万円、最小–中央値–最大）",
        "en": "Salary band by job family × tier (¥10k, min–median–max)",
    },
    "sec2_type": {
        "ko": "급여 표기 방식 분포 — 이것도 표준화 대상",
        "ja": "給与表記方式の分布 — これも標準化対象",
        "en": "Salary-format distribution — also a standardization target",
    },
    "sec3_title": {"ko": "3. 경쟁 강도 & 채널", "ja": "3. 競争度 & チャネル", "en": "3. Competition & channels"},
    "sec3_who": {
        "ko": "읽는 사람: 채널 전략 담당 — \"어느 자리가 붐비나, 어느 채널에 올려야 하나\"",
        "ja": "読者：チャネル戦略担当 —「どのポジションが混んでいるか、どの媒体に出すか」",
        "en": "Reader: channel strategy owners — \"which roles are crowded, which channel to post on\"",
    },
    "sec3_heat": {
        "ko": "직무군 × 티어 공고 밀도",
        "ja": "職種グループ × ティア 求人密度",
        "en": "Posting density: job family × tier",
    },
    "sec3_platform": {"ko": "채널별 공고 분포", "ja": "チャネル別 求人分布", "en": "Postings by channel"},
    "sec4_title": {
        "ko": "4. 표준화 방법론 (리포트 신뢰성 근거)",
        "ja": "4. 標準化の方法論（レポート信頼性の根拠）",
        "en": "4. Standardization methodology (why the numbers are trustworthy)",
    },
    "sec4_who": {
        "ko": "읽는 사람: 리포트 구매 검토자 — \"이 수치를 믿어도 되나\"",
        "ja": "読者：レポート購入検討者 —「この数値は信頼できるか」",
        "en": "Reader: report buyers doing due diligence — \"can I trust these numbers\"",
    },
    "sec4_before": {"ko": "정규화 전 (표기 흔들림)", "ja": "正規化前（表記ゆれ）", "en": "Before (raw notations)"},
    "sec4_after": {"ko": "정규화 후 (canonical)", "ja": "正規化後（canonical）", "en": "After (canonical)"},
    "sec4_item": {"ko": "항목", "ja": "項目", "en": "Field"},
    "sec4_row_field": {"ko": "우대요건 필드명", "ja": "歓迎要件フィールド名", "en": "Preferred-req field name"},
    "sec4_row_title": {"ko": "직무명 원문", "ja": "職種名 原文", "en": "Raw job title"},
    "sec4_row_salary": {"ko": "급여 표기 방식", "ja": "給与表記方式", "en": "Salary format"},
    "sec4_note": {
        "ko": "표준화하지 않으면 같은 수요가 여러 표기로 쪼개져 시장 규모가 과소·과대 집계된다.",
        "ja": "標準化しないと同じ需要が複数の表記に分かれ、市場規模が過小・過大に集計される。",
        "en": "Without standardization the same demand splits across notations, mis-sizing the market.",
    },
    "sec4_bench_title": {
        "ko": "카테고리 벤치마크 — 같은 사업을 하는 선행 사례",
        "ja": "カテゴリ・ベンチマーク — 同じ事業を行う先行事例",
        "en": "Category benchmarks — established players in this space",
    },
    "bench_company": {"ko": "회사", "ja": "会社", "en": "Company"},
    "bench_what": {"ko": "하는 일", "ja": "事業内容", "en": "What they do"},
    "bench_maps": {"ko": "JDF의 대응 부분", "ja": "JDF での対応部分", "en": "Maps to (in JDF)"},
    "col_skill": {"ko": "스킬", "ja": "スキル", "en": "Skill"},
    "col_postings": {"ko": "공고 수", "ja": "求人数", "en": "Postings"},
    "col_platform": {"ko": "채널", "ja": "チャネル", "en": "Channel"},
    "col_family": {"ko": "직무군", "ja": "職種グループ", "en": "Job family"},
    "col_tier": {"ko": "티어", "ja": "ティア", "en": "Tier"},
    "col_min": {"ko": "최소", "ja": "最小", "en": "Min"},
    "col_median": {"ko": "중앙값", "ja": "中央値", "en": "Median"},
    "col_max": {"ko": "최대", "ja": "最大", "en": "Max"},
    "col_type": {"ko": "표기 방식", "ja": "表記方式", "en": "Format"},
    "col_count": {"ko": "건수", "ja": "件数", "en": "Count"},
}


# 카테고리 벤치마크 — vault `03-projects/job-data-foundry/JDF-프로젝트-의사결정-로그-2026-08-13-기준.md`
# 벤치마크 섹션(verified) + `job-data-foundry/docs/job-data-foundry-design-spec.md` 벤치마크 표.
BENCHMARKS = [
    {
        "name": "Lightcast 🇺🇸",
        "what": {
            "ko": "채용공고·이력서·정부통계의 직군명·스킬명을 하나의 표준 체계로 정리 (Open Skills / Open Titles)",
            "ja": "求人・履歴書・政府統計の職種名・スキル名を単一の標準体系に整理（Open Skills / Open Titles）",
            "en": "Standardizes occupation and skill names from postings, resumes, gov stats into one taxonomy",
        },
        "maps": {
            "ko": "Taxonomy·Canonical Schema 설계의 최상위 참고",
            "ja": "Taxonomy・Canonical Schema 設計の最上位リファレンス",
            "en": "Top reference for the taxonomy / canonical schema design",
        },
    },
    {
        "name": "HRog (フロッグ) 🇯🇵",
        "what": {
            "ko": "150+ 구인사이트 40억건 수집. クレンジング(정제·名寄せ)·チャート(시장분석)·Academia(기관 대상)",
            "ja": "150+ 求人サイト 40億件を収集。クレンジング（名寄せ）・チャート（市場分析）・Academia（機関向け）",
            "en": "40B+ records from 150+ boards. Cleansing (entity resolution), market-analysis charts, data for institutions",
        },
        "maps": {
            "ko": "정규화 파이프라인의 실물 모델 — 가장 가까운 사례",
            "ja": "正規化パイプラインの実物モデル — 最も近い事例",
            "en": "Closest real-world model for the normalization pipeline",
        },
    },
    {
        "name": "Revelio Labs 🇺🇸",
        "what": {
            "ko": "채용 데이터를 정규화해 노동시장 분석 리포트를 투자사에 판매",
            "ja": "採用データを正規化し、労働市場分析レポートを投資家に販売",
            "en": "Normalizes hiring data and sells labour-market analysis reports to investors",
        },
        "maps": {
            "ko": "B2B 리포트 비즈니스 모델 (이 대시보드가 파는 것)",
            "ja": "B2B レポートのビジネスモデル（このダッシュボードが売るもの）",
            "en": "The B2B report business model (what this dashboard sells)",
        },
    },
    {
        "name": "求人ボックス 🇯🇵",
        "what": {
            "ko": "2,000만건+ 구인공고 검색 애그리게이터",
            "ja": "2,000万件+ の求人検索アグリゲーター",
            "en": "Job-search aggregator with 20M+ postings",
        },
        "maps": {
            "ko": "중복 제거·카테고리 정규화 벤치마크",
            "ja": "重複排除・カテゴリ正規化のベンチマーク",
            "en": "Benchmark for dedup and category normalization",
        },
    },
    {
        "name": "TheirStack 🇺🇸",
        "what": {
            "ko": "공고 본문에서 기술스택 추출·정규화 후 API로 판매",
            "ja": "求人本文から技術スタックを抽出・正規化し API で販売",
            "en": "Extracts and normalizes tech stack from posting text, sells via API",
        },
        "maps": {
            "ko": "스킬 태그 정규화 파이프라인 벤치마크",
            "ja": "スキルタグ正規化パイプラインのベンチマーク",
            "en": "Benchmark for the skill-tag normalization pipeline",
        },
    },
    {
        "name": "소문 (somoon.ai) 🇰🇷",
        "what": {
            "ko": "실제 기업 채용페이지에서 공고 직접 수집. 구직자용 AI 비교 + 기관용 데이터·API",
            "ja": "企業の採用ページから求人を直接収集。求職者向け AI 比較 + 機関向けデータ・API",
            "en": "Collects postings straight from company career pages. AI comparison for seekers, data/API for institutions",
        },
        "maps": {
            "ko": "한국 사례 — 개인용에서 기관용으로 확장",
            "ja": "韓国の事例 — 個人向けから機関向けへ拡張",
            "en": "Korean case — expanding from consumer to institutional",
        },
    },
]


def benchmark_rows(lang: str) -> list[dict]:
    return [
        {"name": b["name"], "what": b["what"][lang], "maps": b["maps"][lang]}
        for b in BENCHMARKS
    ]


def make_t(lang: str):
    def t(key: str, **kw) -> str:
        s = STR.get(key, {}).get(lang) or STR.get(key, {}).get("en") or key
        return s.format(**kw) if kw else s

    return t
