-- jdf.postings_canonical (합성 트랙 MERGE 대상) 에서 타입 캐스팅 +
-- 스킬 태그 정규화 (表記ゆれ → canonical tag). app/dashboard.py SKILL_KEYWORDS 로직의 SQL 판.

with src as (
    select * from `{{ target.project }}.{{ target.dataset }}.postings_canonical`
),

typed as (
    select
        posting_id,
        source_platform,
        company_name,
        job_family_group,
        tier,
        safe_cast(salary_min as numeric)   as salary_min,
        safe_cast(salary_max as numeric)   as salary_max,
        nullif(trim(salary_type), '')      as salary_type,
        nullif(trim(employment_type), '')  as employment_type,
        nullif(trim(location), '')         as location,
        safe_cast(posted_at as timestamp)  as posted_at,
        date_trunc(date(safe_cast(posted_at as timestamp)), month) as posted_month,
        lower(concat(
            coalesce(preferred_raw, ''), ' ',
            coalesce(requirements_raw, ''), ' ',
            coalesce(description_raw, '')
        )) as text_blob
    from src
)

select
    posting_id,
    source_platform,
    company_name,
    job_family_group,
    tier,
    salary_min,
    salary_max,
    salary_type,
    employment_type,
    location,
    posted_at,
    posted_month,
    array(
        select tag from unnest([
            struct('Python'                 as tag, r'python|パイソン'                            as pat),
            struct('SQL',                       r'sql|エスキューエル'),
            struct('AWS',                       r'aws|amazon web services|アマゾンウェブサービス'),
            struct('GCP',                       r'gcp|google cloud'),
            struct('Java',                      r'\bjava\b|ジャバ'),
            struct('TypeScript',               r'typescript|\bts\b|タイプスクリプト'),
            struct('React',                     r'react|リアクト'),
            struct('Go',                        r'\bgolang\b|go言語|\bゴー\b'),
            struct('Kubernetes',               r'kubernetes|k8s|クバネティス'),
            struct('Docker',                    r'docker|ドッカー'),
            struct('Terraform',                r'terraform|テラフォーム'),
            struct('Spark',                     r'spark|スパーク'),
            struct('ML',                        r'機械学習|マシンラーニング|machine learning|\bml\b'),
            struct('Security',                  r'セキュリティ|security'),
            struct('Requirement definition',   r'要件定義|上流工程')
        ])
        where regexp_contains(text_blob, pat)
    ) as skills
from typed
