-- 채용 활발 기업 상위 (공고 수 기준). 합성 데이터 — 실제 기업 활동 아님.
with exploded as (
    select posting_id, company_name, job_family_group, s as skill
    from {{ ref('stg_postings') }}
    left join unnest(skills) as s
)
select
    company_name,
    count(distinct posting_id)        as postings,
    count(distinct job_family_group)  as job_families,
    count(distinct skill)             as distinct_skills
from exploded
group by company_name
order by postings desc
limit 20
