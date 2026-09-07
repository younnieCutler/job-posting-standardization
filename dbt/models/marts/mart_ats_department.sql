-- 부서별 공고 수 상위 20 (Public ATS).
select
    coalesce(department, '(미기재)')  as department,
    count(distinct posting_id)        as postings
from {{ ref('stg_ats_postings') }}
group by 1
order by postings desc
limit 20
