-- 직무 분야 × 경력 수준별 공고 수 (스택 막대 / 히트맵용).
select
    job_family_group,
    coalesce(tier, 'null')        as tier,
    count(*)                      as postings
from {{ ref('stg_postings') }}
group by 1, 2
order by job_family_group, postings desc
