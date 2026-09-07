-- 공고 본문에서 관측된 기술 키워드별 공고 수 (Public ATS). 표기 변형 합산 후.
-- regex 키워드 매칭이지 taxonomy 아님.
select
    skill,
    source_platform,
    count(distinct posting_id) as postings
from {{ ref('stg_ats_postings') }}, unnest(skills) as skill
group by skill, source_platform
order by postings desc
