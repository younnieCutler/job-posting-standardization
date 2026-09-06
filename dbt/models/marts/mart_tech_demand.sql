-- canonical 스킬 태그별 공고 수 (표기 변형이 stg_postings 에서 합쳐진 후).

select
    skill,
    count(distinct posting_id) as postings
from {{ ref('stg_postings') }}, unnest(skills) as skill
group by skill
order by postings desc
