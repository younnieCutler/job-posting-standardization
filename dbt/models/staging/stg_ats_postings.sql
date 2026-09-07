-- Public ATS (Greenhouse·Ashby) 실채용공고. jdf.ats_postings 에서 타입 정리 +
-- 본문 기술 키워드 추출 (stg_postings 와 동일한 SKILL_KEYWORDS regex 15종).
-- 합성 트랙과 섞지 않는다 — 별도 소스.

with src as (
    select * from `{{ target.project }}.{{ target.dataset }}.ats_postings`
),

typed as (
    select
        posting_id,
        source_platform,
        nullif(trim(company_name), '')          as company_name,
        nullif(trim(title_normalized), '')      as title_normalized,
        nullif(trim(title), '')                 as raw_title,
        nullif(trim(location), '')              as location,
        nullif(trim(department), '')            as department,
        safe_cast(collected_at as timestamp)    as collected_at,
        lower(coalesce(description_normalized, description, '')) as text_blob
    from src
)

select
    posting_id,
    source_platform,
    company_name,
    title_normalized,
    raw_title,
    location,
    department,
    collected_at,
    array(
        select tag from unnest([
            struct('Python'                 as tag, r'python|パイソン'                            as pat),
            struct('SQL',                       r'\bsql\b|エスキューエル'),
            struct('AWS',                       r'\baws\b|amazon web services'),
            struct('GCP',                       r'\bgcp\b|google cloud'),
            struct('Java',                      r'\bjava\b|ジャバ'),
            struct('TypeScript',               r'typescript|\bts\b'),
            struct('React',                     r'\breact\b|リアクト'),
            struct('Go',                        r'\bgolang\b|go言語'),
            struct('Kubernetes',               r'kubernetes|\bk8s\b'),
            struct('Docker',                    r'\bdocker\b'),
            struct('Terraform',                r'terraform'),
            struct('Spark',                     r'\bspark\b'),
            struct('ML',                        r'machine learning|\bml\b|機械学習'),
            struct('Security',                  r'security|セキュリティ'),
            struct('Requirement definition',   r'要件定義|上流工程')
        ])
        where regexp_contains(text_blob, pat)
    ) as skills
from typed
