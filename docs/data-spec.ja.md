# JDF データ仕様書

**日本語 | [한국어](data-spec.md)**

JDF パイプラインが扱うデータのスキーマ・ID 採番方針・保存場所の仕様です。設計の根拠は [`architecture_decision_record.ja.md`](architecture_decision_record.ja.md)、実行方法は [`../README.ja.md`](../README.ja.md) を参照してください。

## 1. データレイヤー

| レイヤー | 場所 | 内容 |
|---|---|---|
| Raw | `data/raw/<platform>/*.parquet` | 媒体7種の元スキーマそのまま（GCS Raw Zone のローカル再現） |
| Landed | `data/kafka_landed/postings.jsonl` | Kafka Consumer が書き出した raw JSON Lines |
| Processed | `data/processed/postings_clean.parquet` | Spark バッチ前処理の結果（元の列 + `raw_title_normalized`、negative_control 除外、posting_id 重複除去済み） |
| Ground truth | `data/synthetic/ground_truth.csv` | マッチングの正解表（role_id / posting_id / tier / company など） |

Canonical Schema へのマッピングと BigQuery 以降の分析レイヤーは未実装です。

## 2. 媒体（source_platform）

`hrmos` / `doda` / `geekly` / `openwork` / `mid_tenshoku` / `talentio` / `company_site`

## 3. ID 採番方針

`posting_id = sha256(source_platform + source_posting_id)`

決定的ハッシュなので、何度実行しても同じ求人には同じ値が振られます。BigQuery の MERGE キーにそのまま使います。

## 4. 日本語の扱い

- `raw_title` などの原文フィールドはそのまま保存します。
- 正規化した値は別の列として追加します（`raw_title_normalized` = NFKC 正規化）。
- Taxonomy マッピング（職種名 → job_family_group）は生成の段階で付与しており、実データを対象としたマッピング規則は未実装です。

## 5. レコードスキーマ

Kafka の topic `jdf.raw_postings` に流れるメッセージと、Raw Parquet のレコードは同じフィールド集合です（値は `make_variant()` が返す dict の JSON シリアライズ）。

### フィールド

| フィールド | 型 | 意味 |
|---|---|---|
| posting_id | string | sha256(source_platform+source_posting_id)、BigQuery MERGE キー |
| source_posting_id | string | 媒体内の元の求人 ID |
| source_platform | string | hrmos/doda/geekly/openwork/mid_tenshoku/talentio/company_site |
| role_id | string | 合成した役割（ポジション）ID |
| company_name | string | 会社名（Faker 生成） |
| raw_title | string | 元の職種名（日本語） |
| job_family_group | string | 6つの職種グループ |
| tier | string | 経験レベル（junior〜principal、null/unknown の例外を含む） |
| location_raw / location | string | 勤務地の原文表記 / 正規化した値 |
| salary_min / salary_max | int/null | 年収レンジ（万円） |
| salary_type / salary_text | string | 給与の表記方式 / 原文テキスト |
| employment_type | string | 雇用形態 |
| agency | string/null | エージェント経由かどうか |
| posted_at | string/null | 掲載日 |
| description_raw / requirements_raw / preferred_raw | string | 原文の職務内容 / 必須要件 / 歓迎要件 |
| is_negative_control | bool | マッチング検証用のネガティブサンプルかどうか |
| tier_blended / coverage_gap_applied | bool | 経験レベルの混合 / 表記欠落パターンを適用したかどうか |

### Kafka メッセージの例（`data/kafka_landed/postings.jsonl` の1件）
```json
{
  "posting_id": "6a48f7dd400bf0b401f760b370fe109534c7bdcd9695191b96b73f1f96de8fb0",
  "source_posting_id": "company_site-113-0",
  "source_platform": "company_site",
  "role_id": "113",
  "company_name": "合同会社木村電気",
  "raw_title": "業務系SE",
  "job_family_group": "software_development",
  "tier": "mid",
  "location_raw": "勤務地：大阪府",
  "location": "大阪府",
  "salary_min": 485.0,
  "salary_max": 617.0,
  "salary_type": "月給制",
  "salary_text": "",
  "employment_type": "正社員",
  "agency": null,
  "posted_at": null,
  "description_raw": "職務内容：業務系SEとしてご活躍いただきます。",
  "requirements_raw": "必須要件：SQL・データ抽出経験3年以上",
  "preferred_raw": "求める経験・スキル：SQL実務経験、AWSまたはGCP実務経験、Python実務経験",
  "is_negative_control": false,
  "tier_blended": false,
  "coverage_gap_applied": false
}
```

## 6. 品質チェック

- `ingestion/verify_coverage.py` — 会社・職種・媒体・経験レベル・表記パターンが一方に偏っていないかを自動で検証します。
- `is_negative_control` — マッチング検証用のネガティブサンプル。Spark の前処理で除外されます。
- tier の例外 — junior〜principal の5段階に加えて null / unknown を意図的に混ぜ、欠損の処理経路を検証します。
- Golden set — [`golden-set/real-postings-golden-set.csv`](golden-set/real-postings-golden-set.csv)（56行・19ケース）。実際の求人に現れる表記ゆれパターンの出どころです。

### 現時点の限界

golden set（実データ）では、同じ求人でも `title` が94%のケースで媒体ごとに異なり、年収の数字も59%で食い違います。一方、現在の合成データでは `location_raw`（77%）・`salary_type`（87%）・`requirements_raw`（96%）は媒体ごとに変わるものの、**`raw_title` と `salary_min` / `salary_max` は全媒体で同一**です。

つまり、表記ゆれの中でも最も難しい軸がまだ生成側に移せていません。この状態ではエンティティ解決が本来より易しく解けてしまうため、生成規則（`ingestion/synth_rules.py`）への職種名・年収の変形の追加が次の優先課題です。
