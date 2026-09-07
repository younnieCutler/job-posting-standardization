-- 월별 공고 유입 추이. posted_at 이 있는 공고만 (커버리지는 mart_overview.posted_at_coverage).
select
    posted_month,
    count(*)  as postings
from {{ ref('stg_postings') }}
where posted_month is not null
group by posted_month
order by posted_month
