-- Page 1 ATS 블록 스코어카드 1행.
select
    count(distinct posting_id)                                      as postings,
    count(distinct company_name)                                    as companies,
    count(distinct source_platform)                                 as channels,
    count(distinct location)                                        as locations,
    max(collected_at)                                               as last_collected_at,
    round(safe_divide(countif(array_length(skills) > 0), count(*)), 3) as skill_signal_rate
from {{ ref('stg_ats_postings') }}
