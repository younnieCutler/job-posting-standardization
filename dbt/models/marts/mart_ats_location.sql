-- 근무 지역별 공고 수 상위 20 (Public ATS, 원문 표기 — 정리 전).
select
    coalesce(location, '(미기재)')   as location,
    count(distinct posting_id)       as postings
from {{ ref('stg_ats_postings') }}
group by 1
order by postings desc
limit 20
