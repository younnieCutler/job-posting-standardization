-- source_platform 별 공고 수 + 스킬 태그가 하나라도 붙은 비율.

select
    source_platform,
    count(*)                                                  as postings,
    countif(array_length(skills) > 0)                         as postings_with_skill,
    round(safe_divide(countif(array_length(skills) > 0), count(*)), 3) as skill_tag_rate
from {{ ref('stg_postings') }}
group by source_platform
order by postings desc
