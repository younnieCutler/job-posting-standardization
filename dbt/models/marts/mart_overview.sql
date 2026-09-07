-- 리포트 헤더 스코어카드 1행. 데이터가 실제로 증명하는 것만.
select
    count(*)                                                        as total_postings,
    count(distinct company_name)                                   as companies,
    count(distinct job_family_group)                               as job_families,
    count(distinct source_platform)                                as channels,
    round(safe_divide(countif(array_length(skills) > 0), count(*)), 3) as skill_tag_rate,
    round(safe_divide(countif(posted_at is not null), count(*)), 3)    as posted_at_coverage,
    count(distinct salary_type)                                    as salary_format_variants
from {{ ref('stg_postings') }}
