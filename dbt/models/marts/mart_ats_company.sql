-- 공고 많이 관측된 기업 상위 20 (Public ATS). 실제 기업 활동이 아니라 수집 표본 내 관측.
select
    company_name,
    count(distinct posting_id)          as postings,
    count(distinct department)          as departments,
    count(distinct location)            as locations
from {{ ref('stg_ats_postings') }}
where company_name is not null
group by company_name
order by postings desc
limit 20
