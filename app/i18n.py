"""대시보드 다국어 문자열 (한국어 / 日本語 / English).

원칙:
- 화면은 데이터가 실제로 증명하는 것만 주장한다.
- 두 데이터셋(일본어 합성 / 글로벌 실제 ATS)을 합쳐서 하나의 시장처럼 보여주지 않는다.
- 개발자용 컬럼명·DB 용어를 메인 화면에 노출하지 않는다. 기술 설명은 도움말에서만.
- 미구현 기능을 완성된 것처럼 표시하지 않는다.
"""

LANGS = {"한국어": "ko", "日本語": "ja", "English": "en"}

# 데이터셋 선택
DATASETS = {
    "japan": {
        "ko": "일본어 표준화 데이터셋 — 표준화 파이프라인 검증 (합성)",
        "ja": "日本語 標準化データセット — 標準化パイプライン検証（合成）",
        "en": "Japan Standardization Dataset — pipeline validation (synthetic)",
    },
    "ats": {
        "ko": "글로벌 공개 ATS 데이터셋 — 실제 공개 채용공고 스냅샷",
        "ja": "グローバル公開 ATS データセット — 実際の公開求人スナップショット",
        "en": "Global Public ATS Dataset — real public job-posting snapshot",
    },
}

STR = {
    "pick_dataset": {"ko": "분석 데이터", "ja": "分析データ", "en": "Dataset"},
    "app_title": {
        "ko": "JDF — 채용공고 표준화 리포트",
        "ja": "JDF — 求人票 標準化レポート",
        "en": "JDF — Job-Posting Standardization Report",
    },
    "split_note": {
        "ko": "실제 공개 ATS 데이터는 **시장 스냅샷 분석**에, 일본어 합성 데이터는 **표준화 파이프라인 "
              "품질 검증**에 사용합니다. 두 데이터는 목적이 달라 화면에서도 분리했습니다. 합쳐서 하나의 "
              "시장 지표로 만들지 않습니다.",
        "ja": "実際の公開 ATS データは**市場スナップショット分析**に、日本語合成データは**標準化パイプラインの"
              "品質検証**に使用します。目的が異なるため画面でも分離しています。合算して一つの市場指標にはしません。",
        "en": "The real public-ATS data is used for a **market snapshot**; the Japanese synthetic data is used for "
              "**pipeline quality validation**. They serve different purposes and are kept separate — never combined "
              "into one market metric.",
    },
    "who": {"ko": "이 화면을 보는 사람", "ja": "この画面を見る人", "en": "Who reads this"},
    "question": {"ko": "이 화면으로 답하려는 질문", "ja": "この画面で答える問い", "en": "Question answered"},
    "reader_planner": {
        "ko": "일본 IT 채용 계획을 세우는 HR/TA 데이터 분석 담당자",
        "ja": "日本 IT 採用計画を立てる HR/TA データ分析担当者",
        "en": "HR/TA data analyst planning IT hiring in Japan",
    },

    # ================= JAPAN TRACK (synthetic) =================
    "jp_warning": {
        "ko": "⚠️ 이 데이터는 **합성(가상) 채용공고**입니다. 실제 일본 시장의 수요·연봉·경쟁 상황이 아니라, "
              "표기가 제각각인 공고를 얼마나 일관되게 정리하는지 확인하기 위한 검증용 입력입니다.",
        "ja": "⚠️ このデータは**合成（架空）の求人**です。実際の日本市場の需要・年収・競争状況ではなく、"
              "表記がばらばらな求人をどれだけ一貫して整理できるかを確認するための検証用入力です。",
        "en": "⚠️ This is **synthetic (fictional) job-posting data** — not real Japan-market demand, salary, or "
              "competition. It is validation input for checking how consistently messy postings get cleaned up.",
    },
    "jp_h_summary": {"ko": "1. 요약 — 이 데이터에는 무엇이 들어 있나?",
                     "ja": "1. サマリー — このデータには何が入っているか？",
                     "en": "1. Summary — what's in this data?"},
    "jp_h_demand": {"ko": "2. 직무 수요 — 어떤 직무와 경력 수준의 공고가 많은가?",
                    "ja": "2. 職務需要 — どの職務・経験レベルの求人が多いか？",
                    "en": "2. Job demand — which roles and experience levels have the most postings?"},
    "jp_h_skill": {"ko": "3. 스킬 신호 — 공고에서 어떤 기술 키워드가 많이 나타나나?",
                   "ja": "3. スキルシグナル — 求人にどの技術キーワードが多く現れるか？",
                   "en": "3. Skill signals — which tech keywords appear most in postings?"},
    "jp_h_channel": {"ko": "4. 채널 — 데이터가 어떤 채널에서 수집됐나?",
                     "ja": "4. チャネル — データはどのチャネルから収集されたか？",
                     "en": "4. Channels — which channels was the data collected from?"},
    "jp_h_quality": {"ko": "5. 표준화 품질 — 다르게 적힌 데이터를 얼마나 일관되게 만들었나?",
                     "ja": "5. 標準化の品質 — バラバラの表記をどれだけ揃えられたか？",
                     "en": "5. Standardization quality — how consistent did the data become?"},
    "jp_h_method": {"ko": "6. 방법 · 출처 — 이 데이터는 어디서 왔고 어디까지 믿을 수 있나?",
                    "ja": "6. 方法・出典 — このデータはどこから来て、どこまで信頼できるか？",
                    "en": "6. Method & source — where is this data from and how far can it be trusted?"},

    "jp_q_summary": {"ko": "채용 계획 담당자 — 지금 이 데이터에 어떤 공고가 들어 있는가?",
                     "ja": "採用計画担当者 — いまこのデータにどんな求人が入っているか？",
                     "en": "Hiring planner — what postings are in this data right now?"},
    "jp_q_demand": {"ko": "채용 계획 담당자 — 어떤 직무 분야·경력 수준에 공고가 몰려 있는가?",
                    "ja": "採用計画担当者 — どの職務分野・経験レベルに求人が集中しているか？",
                    "en": "Hiring planner — which job fields / levels are the postings concentrated in?"},
    "jp_q_skill": {"ko": "채용 계획 담당자 — 공고 본문에 어떤 기술 키워드가 자주 등장하는가?",
                   "ja": "採用計画担当者 — 求人本文にどの技術キーワードが頻出するか？",
                   "en": "Hiring planner — which tech keywords recur in posting text?"},
    "jp_q_channel": {"ko": "데이터 담당자 — 이 데이터는 어떤 채널 구성으로 이뤄져 있는가?",
                     "ja": "データ担当者 — このデータはどのチャネル構成か？",
                     "en": "Data owner — what channel mix makes up this data?"},
    "jp_q_quality": {"ko": "데이터 담당자 — 표기 통일·중복 정리가 얼마나 됐는가? 무엇이 남았는가?",
                     "ja": "データ担当者 — 表記統一・重複整理はどこまで進んだか？何が残っているか？",
                     "en": "Data owner — how far did notation-unification and dedup get? what remains?"},

    "jp_dist_title": {"ko": "어떤 직무 분야에서 어떤 경력 수준의 공고가 많은가?",
                      "ja": "どの職務分野で、どの経験レベルの求人が多いか？",
                      "en": "Which job fields have the most postings, at which experience level?"},
    "jp_dist_cap": {"ko": "합성 데이터셋의 구성 분포입니다. 실제 일본 시장 수요가 아닙니다.",
                    "ja": "合成データセットの構成分布です。実際の日本市場需要ではありません。",
                    "en": "Composition of the synthetic dataset — not real Japan-market demand."},
    "jp_channel_title": {"ko": "채용공고는 어떤 채널에서 많이 수집됐나?",
                         "ja": "求人はどのチャネルから多く収集されたか？",
                         "en": "Which channels were most postings collected from?"},
    "jp_channel_cap": {"ko": "채널별 공고 수까지만 말합니다. '어디에 올려야 한다'는 해석은 이 데이터로 뒷받침되지 않습니다.",
                       "ja": "チャネル別の求人数まで。『どこに出すべき』という解釈はこのデータでは裏付けられません。",
                       "en": "Just posting counts per channel. The data does not support 'where to post'."},
    "jp_skill_title": {"ko": "공고에서 어떤 기술 키워드가 많이 나타나나? (표기 다른 것끼리 합산)",
                       "ja": "求人にどの技術キーワードが多く現れるか？（異なる表記を統合）",
                       "en": "Which tech keywords appear most? (different spellings merged)"},
    "jp_skill_cap": {"ko": "직무 분류 체계가 아닙니다. 같은 뜻의 여러 표기(예: Python / パイソン / PYTHON)를 하나로 묶어 센 결과입니다.",
                     "ja": "職務分類体系ではありません。同じ意味の複数表記（例: Python / パイソン / PYTHON）を一つにまとめて数えた結果です。",
                     "en": "Not a skill taxonomy. Counts after folding same-meaning spellings (e.g. Python / パイソン / PYTHON) together."},
    "jp_skill_filter": {"ko": "직무 분야로 좁혀 보기", "ja": "職務分野で絞る", "en": "Narrow by job field"},
    "jp_all": {"ko": "전체", "ja": "すべて", "en": "All"},

    "jp_metric": {"ko": "항목", "ja": "項目", "en": "Item"},
    "jp_value": {"ko": "값", "ja": "値", "en": "Value"},
    "jp_m_total": {"ko": "전체 공고 수", "ja": "全求人数", "en": "Total postings"},
    "jp_m_nfkc": {"ko": "표기 통일로 직무명이 바뀐 공고 수", "ja": "表記統一で職種名が変わった求人数",
                  "en": "Postings whose title changed after notation-unification"},
    "jp_m_nfkc_help": {"ko": "전각/반각·기호 통일(기술용어 NFKC). 이 스냅샷은 이미 깔끔해 바뀐 게 없을 수 있습니다.",
                       "ja": "全角/半角・記号の統一（技術的には NFKC）。このスナップショットは既にきれいで変化ゼロのこともあります。",
                       "en": "Full/half-width and symbol unification (NFKC). This snapshot may already be clean, so zero is possible."},
    "jp_m_dup": {"ko": "중복으로 판단돼 남지 않은 공고 수", "ja": "重複と判定され残らなかった求人数",
                 "en": "Postings removed as duplicates"},
    "jp_m_dup_help": {"ko": "같은 공고 판별 후 남은 데이터 기준. 0이면 이 스냅샷에 중복이 없다는 뜻입니다.",
                      "ja": "同一求人の判定後に残ったデータ基準。0 ならこのスナップショットに重複がないという意味です。",
                      "en": "Measured on post-dedup data. 0 means this snapshot has no duplicates."},
    "jp_m_salary_fmt": {"ko": "연봉이 적힌 방식의 가짓수 (아직 정리 전)", "ja": "年収の書き方の種類数（未整理）",
                        "en": "Distinct ways salary is written (not yet parsed)"},
    "jp_m_salary_help": {"ko": "예: '연봉 500만~700만엔' / '월급+상여' / '월급제'. 이를 최저·최고 숫자로 바꾸는 정리는 아직 없습니다.",
                         "ja": "例:『年収500万〜700万円』/『月給+賞与』/『月給制』。これを最低・最高の数値に変換する整理はまだありません。",
                         "en": "e.g. '¥5–7M/yr' / 'monthly + bonus' / 'monthly'. Converting these into min/max numbers is not implemented."},
    "jp_m_field": {"ko": "'우대 요건' 항목명이 적힌 방식의 가짓수 (아직 정리 전)",
                   "ja": "『歓迎要件』項目名の書き方の種類数（未整理）",
                   "en": "Distinct labels used for the 'preferred requirements' field (not yet unified)"},
    "jp_m_field_help": {"ko": "예: 歓迎要件 / 尚可条件 / 求める経験・スキル — 같은 항목인데 이름이 다릅니다. 공통 이름으로 저장하는 처리는 아직 없습니다.",
                        "ja": "例: 歓迎要件 / 尚可条件 / 求める経験・スキル — 同じ項目でも名前が違います。共通名で保存する処理はまだありません。",
                        "en": "e.g. 歓迎要件 / 尚可条件 / 求める経験・スキル — same field, different names. Writing a common name is not implemented."},
    "jp_nulls_title": {"ko": "값이 비어 있는 비율이 높은 항목", "ja": "値が空の比率が高い項目",
                       "en": "Fields most often left empty"},
    "jp_null_col": {"ko": "항목", "ja": "項目", "en": "Field"},
    "jp_null_rate": {"ko": "비어 있는 비율", "ja": "空の比率", "en": "Empty rate"},

    "jp_method_body": {
        "ko": "**만든 방법**: `ingestion/generate_synthetic_postings.py` — 가상 인물·회사 생성기(Faker 일본어) + "
              "실제 공고 표본 56건에서 뽑아낸 패턴(표기 흔들림·연봉 표기 방식·경력 등급 섞임). 직무·회사·경력 축과 "
              "패턴 축을 분리해 조합. 출력을 채널별 파일로 저장한 뒤 스트리밍·일괄 처리를 거쳐 검증용 파일로 만듭니다.\n\n"
              "**믿을 수 있는 범위**: 표기 흔들림을 얼마나 일관되게 정리하는지 확인하는 용도까지. 이 숫자를 실제 일본 "
              "채용시장 규모·수요·연봉으로 읽으면 안 됩니다.",
        "ja": "**作り方**: `ingestion/generate_synthetic_postings.py` — 架空の人物・企業生成（Faker 日本語）+ "
              "実際の求人サンプル 56 件から抽出したパターン（表記ゆれ・年収表記・経験ランクの混在）。職務・企業・経験の軸と"
              "パターンの軸を分けて組み合わせます。出力をチャネル別ファイルに保存し、ストリーミング・一括処理を経て検証用ファイルにします。\n\n"
              "**信頼できる範囲**: 表記ゆれをどれだけ揃えられるかの確認まで。実際の日本の採用市場規模・需要・年収として読んではいけません。",
        "en": "**How it was built**: `ingestion/generate_synthetic_postings.py` — fictional people/companies (Faker ja_JP) "
              "plus patterns extracted from 56 real posting samples (notation drift, salary-writing styles, mixed levels). "
              "Role/company/level axes are combined independently of the pattern axis. Output is saved per channel, then "
              "run through streaming + batch processing into a validation file.\n\n"
              "**How far to trust it**: only for checking how consistently notation drift gets cleaned up. Do not read these "
              "numbers as real Japan-market size, demand, or salary.",
    },

    # ================= GLOBAL ATS TRACK (real) =================
    "ats_note": {
        "ko": "출처: Greenhouse / Ashby 공개 API. 실제 채용공고입니다. 단 회사·직무·근무지가 미국·글로벌 중심이라 "
              "**일본 시장이 아닙니다**. 이 표본에서는 '관측됐다' 수준의 표현만 씁니다.",
        "ja": "出典: Greenhouse / Ashby 公開 API。実際の求人です。ただし企業・職種・勤務地が米国・グローバル中心のため"
              "**日本市場ではありません**。この標本では『観測された』程度の表現のみ使います。",
        "en": "Source: Greenhouse / Ashby public APIs. These are real postings, but companies/roles/locations are US- and "
              "global-centric — **not the Japan market**. Only 'observed in this sample' wording is used here.",
    },
    "ats_h_summary": {"ko": "1. 요약 — 이 공개 채용공고 표본에는 무엇이 들어 있나?",
                      "ja": "1. サマリー — この公開求人サンプルには何が入っているか？",
                      "en": "1. Summary — what's in this public-posting sample?"},
    "ats_h_company": {"ko": "2. 기업 — 어떤 회사가 공고를 많이 냈나?",
                      "ja": "2. 企業 — どの企業が多く求人を出したか？",
                      "en": "2. Companies — which companies posted the most?"},
    "ats_h_role": {"ko": "3. 직무 — 어떤 직무명이 많이 관측됐나?",
                   "ja": "3. 職務 — どの職種名が多く観測されたか？",
                   "en": "3. Roles — which job titles were observed most?"},
    "ats_h_location": {"ko": "4. 근무 지역 — 공고는 어디에 몰려 있나?",
                       "ja": "4. 勤務地 — 求人はどこに集中しているか？",
                       "en": "4. Locations — where are the postings concentrated?"},
    "ats_h_skill": {"ko": "5. 기술 키워드 — 공고 본문에서 어떤 기술이 많이 관측됐나?",
                    "ja": "5. 技術キーワード — 求人本文でどの技術が多く観測されたか？",
                    "en": "5. Tech keywords — which technologies were observed most in posting text?"},
    "ats_h_source": {"ko": "6. 출처 비교 — Greenhouse와 Ashby는 어떻게 다른가?",
                     "ja": "6. 出典比較 — Greenhouse と Ashby はどう違うか？",
                     "en": "6. Source comparison — how do Greenhouse and Ashby differ?"},
    "ats_h_method": {"ko": "7. 방법 · 출처 — 이 표본은 어떻게 수집·정리됐나?",
                     "ja": "7. 方法・出典 — この標本はどう収集・整理されたか？",
                     "en": "7. Method & source — how was this sample collected and cleaned?"},

    "ats_q_summary": {"ko": "채용 계획 담당자 — 이 공개 채용공고 표본의 규모와 구성은?",
                      "ja": "採用計画担当者 — この公開求人サンプルの規模と構成は？",
                      "en": "Hiring planner — what's the size and shape of this public-posting sample?"},
    "ats_q_company": {"ko": "채용 계획 담당자 — 어떤 회사가 활발히 채용 중으로 관측되나?",
                      "ja": "採用計画担当者 — どの企業が活発に採用中と観測されるか？",
                      "en": "Hiring planner — which companies are observed hiring actively?"},
    "ats_q_role": {"ko": "채용 계획 담당자 — 어떤 직무명이 표본에 많이 나타나나?",
                   "ja": "採用計画担当者 — どの職種名が標本に多く現れるか？",
                   "en": "Hiring planner — which job titles show up most in the sample?"},
    "ats_q_location": {"ko": "채용 계획 담당자 — 공고가 어느 지역에 집중돼 있나?",
                       "ja": "採用計画担当者 — 求人はどの地域に集中しているか？",
                       "en": "Hiring planner — which regions are the postings in?"},
    "ats_q_skill": {"ko": "채용 계획 담당자 — 표본에서 어떤 기술이 얼마나 관측되나?",
                    "ja": "採用計画担当者 — 標本でどの技術がどれだけ観測されるか？",
                    "en": "Hiring planner — which technologies are observed, and how often?"},
    "ats_q_source": {"ko": "데이터 담당자 — 두 수집 출처의 규모·구성 차이는?",
                     "ja": "データ担当者 — 二つの収集出典の規模・構成の違いは？",
                     "en": "Data owner — how do the two sources differ in size and mix?"},

    "ats_company_title": {"ko": "어떤 회사가 채용공고를 많이 냈나? (상위 20)",
                          "ja": "どの企業が求人を多く出したか？（上位 20）",
                          "en": "Which companies posted the most? (top 20)"},
    "ats_role_title": {"ko": "어떤 직무명이 많이 관측됐나? (상위 20)",
                       "ja": "どの職種名が多く観測されたか？（上位 20）",
                       "en": "Which job titles were observed most? (top 20)"},
    "ats_location_title": {"ko": "공고는 어느 지역에 몰려 있나? (상위 20)",
                           "ja": "求人はどの地域に集中しているか？（上位 20）",
                           "en": "Where are the postings concentrated? (top 20)"},
    "ats_skill_title": {"ko": "공고 본문에서 어떤 기술 키워드가 관측됐나?",
                        "ja": "求人本文でどの技術キーワードが観測されたか？",
                        "en": "Which tech keywords were observed in posting text?"},
    "ats_skill_cap": {"ko": "예: '이 공개 ATS 표본에서는 Python 관련 공고가 N건 관측됨'. 표기 다른 것끼리 합산.",
                      "ja": "例:『この公開 ATS 標本では Python 関連求人が N 件観測された』。異なる表記を統合。",
                      "en": "e.g. 'in this public-ATS sample, N postings mention Python'. Different spellings merged."},
    "ats_source_title": {"ko": "Greenhouse와 Ashby에서 각각 몇 건이 수집됐나?",
                         "ja": "Greenhouse と Ashby からそれぞれ何件収集されたか？",
                         "en": "How many postings came from Greenhouse vs Ashby?"},
    "ats_company_skill_title": {"ko": "회사별로 어떤 기술 키워드가 많이 관측됐나? (공고 수 상위 회사)",
                                "ja": "企業ごとにどの技術キーワードが多く観測されたか？（求人数上位企業）",
                                "en": "Which tech keywords per company? (companies with the most postings)"},
    "ats_partition": {"ko": "데이터 수집 시점", "ja": "データ収集時点", "en": "Data collection run"},
    "ats_method_body": {
        "ko": "**수집**: `ingestion/collect_public_ats_postings.py` — 공개 회사 카탈로그에서 회사를 골라 "
              "Greenhouse·Ashby 공식 API로 IT 공고를 가져옵니다. 개별 회사 실패는 기록하고 계속 진행합니다.\n\n"
              "**정리**: `spark_normalize_public_postings.py` — 전각/반각·기호 통일, 공고 고유 ID 부여, 같은 공고 "
              "중복 제거 후 날짜별 파일로 저장.\n\n"
              "**믿을 수 있는 범위**: 수집 시점의 공개 ATS 표본에 한합니다. 미국·글로벌 중심이라 일본 시장 규모·"
              "수요로 읽으면 안 됩니다. 공개 보드가 있는 회사만 포함됩니다.",
        "ja": "**収集**: `ingestion/collect_public_ats_postings.py` — 公開企業カタログから企業を選び、"
              "Greenhouse・Ashby 公式 API で IT 求人を取得。個別企業の失敗は記録して続行します。\n\n"
              "**整理**: `spark_normalize_public_postings.py` — 全角/半角・記号の統一、求人固有 ID の付与、"
              "同一求人の重複排除の後、日付別ファイルに保存。\n\n"
              "**信頼できる範囲**: 収集時点の公開 ATS 標本に限ります。米国・グローバル中心のため日本市場の規模・"
              "需要として読んではいけません。公開ボードを持つ企業のみ含まれます。",
        "en": "**Collection**: `ingestion/collect_public_ats_postings.py` picks companies from a public catalog and "
              "pulls IT postings via the Greenhouse/Ashby official APIs. Per-company failures are logged and skipped.\n\n"
              "**Cleaning**: `spark_normalize_public_postings.py` unifies full/half-width and symbols, assigns a posting "
              "ID, removes duplicates, and writes per-date files.\n\n"
              "**How far to trust it**: only as the public-ATS sample at collection time. US/global-centric — not Japan "
              "market size or demand. Only companies with a public board are included.",
    },

    # ---- 공통 표시용 컬럼명 (개발자 컬럼명 노출 금지) ----
    "c_field": {"ko": "직무 분야", "ja": "職務分野", "en": "Job field"},
    "c_level": {"ko": "경력 수준", "ja": "経験レベル", "en": "Experience level"},
    "c_channel": {"ko": "채용 채널", "ja": "採用チャネル", "en": "Hiring channel"},
    "c_postings": {"ko": "채용공고 수", "ja": "求人数", "en": "Postings"},
    "c_company": {"ko": "기업", "ja": "企業", "en": "Company"},
    "c_location": {"ko": "근무 지역", "ja": "勤務地", "en": "Location"},
    "c_title": {"ko": "직무명", "ja": "職種名", "en": "Job title"},
    "c_skill": {"ko": "기술 키워드", "ja": "技術キーワード", "en": "Tech keyword"},
    "c_source": {"ko": "수집 출처", "ja": "収集出典", "en": "Source"},
    "c_count": {"ko": "건수", "ja": "件数", "en": "Count"},

    # ---- KPI 라벨 ----
    "k_jp_records": {"ko": "공고 수 (합성)", "ja": "求人数（合成）", "en": "Postings (synthetic)"},
    "k_jp_companies": {"ko": "회사명 수 (합성)", "ja": "企業名数（合成）", "en": "Company names (synthetic)"},
    "k_jp_channels": {"ko": "채널 수", "ja": "チャネル数", "en": "Channels"},
    "k_jp_fields": {"ko": "직무 분야 수", "ja": "職務分野数", "en": "Job fields"},
    "k_ats_records": {"ko": "공고 수 (실제)", "ja": "求人数（実際）", "en": "Postings (real)"},
    "k_ats_companies": {"ko": "회사 수 (실제)", "ja": "企業数（実際）", "en": "Companies (real)"},
    "k_ats_sources": {"ko": "수집 출처 수", "ja": "収集出典数", "en": "Sources"},

    # ---- 벤치마크 (요약 표) ----
    "bench_title": {"ko": "참고한 선행 서비스", "ja": "参考にした先行サービス", "en": "Reference services"},
    "bench_more": {"ko": "상세 분석: `docs/6th-assignment/benchmarking.md`",
                   "ja": "詳細分析: `docs/6th-assignment/benchmarking.md`",
                   "en": "Full analysis: `docs/6th-assignment/benchmarking.md`"},
    "bench_c_service": {"ko": "참고 서비스", "ja": "参考サービス", "en": "Service"},
    "bench_c_took": {"ko": "우리가 참고한 점", "ja": "参考にした点", "en": "What we took"},
    "bench_c_apply": {"ko": "JDF 적용", "ja": "JDF への適用", "en": "Applied in JDF"},

    # ---- 미구현 ----
    "notimpl_title": {"ko": "아직 만들지 않은 것 (완성 기능처럼 표시하지 않음)",
                      "ja": "まだ作っていないもの（完成機能として表示しない）",
                      "en": "Not built yet (not shown as working features)"},
}

NOTIMPL = {
    "ko": [
        "직무 분류 — 직무명·스킬을 공통 코드로 묶는 처리 (얼마나 묶였는지 셀 수 없음)",
        "연봉 정리 — '연봉 500만~700만엔' 같은 문장을 최저·최고 숫자로 바꾸기",
        "클라우드 저장 + 집계 테이블 (BigQuery / dbt) — 이 리포트는 로컬 파일만 사용",
        "채용률·이탈률·지원자 경쟁률·실제 시장 연봉 벤치마크 — JDF에 없는 지표라 만들지 않음",
    ],
    "ja": [
        "職務分類 — 職種名・スキルを共通コードにまとめる処理（どれだけまとまったか計測不可）",
        "年収整理 —『年収500万〜700万円』のような文を最低・最高の数値に変換",
        "クラウド保存 + 集計テーブル（BigQuery / dbt）— 本レポートはローカルファイルのみ使用",
        "採用率・離職率・応募競争率・実際の市場年収ベンチマーク — JDF にない指標のため作らない",
    ],
    "en": [
        "Job classification — folding titles/skills into shared codes (can't measure how much folded)",
        "Salary parsing — turning phrases like '¥5–7M/yr' into min/max numbers",
        "Cloud storage + summary tables (BigQuery / dbt) — this report uses local files only",
        "Hiring rate, attrition, applicant competition, real market salary benchmark — not in JDF, not built",
    ],
}

# 벤치마크 요약 표 — 상세는 docs/6th-assignment/benchmarking.md
BENCH_TABLE = {
    "ko": [
        ("Lightcast", "직무·스킬 공통 언어", "표기 통일 · 직무 분류"),
        ("HRog", "일본 채용시장 분석 방식", "직무 · 경력 · 채널 분석"),
        ("Revelio Labs", "의사결정 중심 인력시장 리포트", "HR/TA용 종합 리포트 구조"),
        ("TheirStack", "공고 구조화 · 기술 추출", "스킬 키워드 통합"),
    ],
    "ja": [
        ("Lightcast", "職務・スキルの共通言語", "表記統一 ・ 職務分類"),
        ("HRog", "日本の採用市場分析の方法", "職務 ・ 経験 ・ チャネル分析"),
        ("Revelio Labs", "意思決定中心の人材市場レポート", "HR/TA 向け総合レポート構造"),
        ("TheirStack", "求人の構造化 ・ 技術抽出", "スキルキーワード統合"),
    ],
    "en": [
        ("Lightcast", "Common language for roles & skills", "Notation unification, job classification"),
        ("HRog", "How the Japan hiring market is analyzed", "Role / level / channel analysis"),
        ("Revelio Labs", "Decision-first workforce report", "Report structure for HR/TA"),
        ("TheirStack", "Structuring postings, extracting tech", "Skill-keyword merging"),
    ],
}


def bench_table(lang: str) -> list[tuple]:
    return BENCH_TABLE.get(lang, BENCH_TABLE["en"])


def notimpl(lang: str) -> list[str]:
    return NOTIMPL.get(lang, NOTIMPL["en"])


def make_t(lang: str):
    def t(key: str, **kw):
        v = STR.get(key, {}).get(lang)
        if v is None:
            v = STR.get(key, {}).get("en", key)
        return v.format(**kw) if kw else v

    return t
