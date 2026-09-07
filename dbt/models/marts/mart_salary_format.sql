-- 급여 표기 방식 분포. 실제 급여액이 아니라 "표기가 몇 가지로 갈리는가" (정규화 대상).
select
    coalesce(salary_type, '(미기재)')  as salary_type,
    count(*)                          as postings,
    round(safe_divide(count(*), sum(count(*)) over ()), 3) as share
from {{ ref('stg_postings') }}
group by 1
order by postings desc
