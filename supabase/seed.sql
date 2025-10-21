-- InterviewAI Seed Data
-- IMPORTANT: Replace {{YOUR_AUTH_USER_ID}} with a real auth.users.id for your test user.
-- Run this after the initial schema migration.

-- 1) Create a demo organization with an API key and webhook settings
with org as (
  insert into organizations (name, contact_email, api_key, webhook_url, webhook_secret)
  values (
    'Demo Organization',
    'owner@demo.org',
    'org_demo_' || encode(gen_random_bytes(24), 'hex'),
    'https://example.com/webhooks/interview-results',
    'whsec_' || encode(gen_random_bytes(24), 'hex')
  )
  returning id, api_key
)
select * from org;

-- 2) Link a profile to your existing auth user and the new organization
-- Replace the placeholder with a real user id from auth.users
insert into profiles (id, email, full_name, company_name, organization_id, subscription_tier)
select '{{YOUR_AUTH_USER_ID}}'::uuid, 'owner@demo.org', 'Demo Owner', 'Demo Org', o.id, 'essential'
from organizations o
order by created_at desc
limit 1;

-- 3) Create a sample job description
with jd as (
  insert into job_descriptions (user_id, title, description, industry, difficulty, custom_questions)
  values (
    '{{YOUR_AUTH_USER_ID}}'::uuid,
    'Customer Support Associate',
    'Handle customer queries via email and chat; de-escalation and empathy are critical.',
    'Customer Support',
    'easy',
    '["Tell me about a time you de-escalated a situation.", "How would you handle a delayed shipment complaint?"]'::jsonb
  )
  returning id
)
select * from jd;

-- 4) Create a sample interview session
with last_jd as (
  select id from job_descriptions where user_id = '{{YOUR_AUTH_USER_ID}}'::uuid order by created_at desc limit 1
), sess as (
  insert into interview_sessions (
    job_description_id, user_id, candidate_name, candidate_email, status, ai_tier_used, started_at
  )
  select id, '{{YOUR_AUTH_USER_ID}}'::uuid, 'Jane Candidate', 'jane.candidate@example.com', 'pending', 'essential', null from last_jd
  returning id
)
select * from sess;

-- 5) Seed a few interview questions for that session
with s as (
  select id from interview_sessions where user_id = '{{YOUR_AUTH_USER_ID}}'::uuid order by created_at desc limit 1
)
insert into interview_questions (session_id, question_text, question_order, question_type)
select id, 'Tell me about yourself.', 1, 'behavioral' from s
union all
select id, 'Describe a time you handled an unhappy customer.', 2, 'situational' from s
union all
select id, 'How do you prioritize multiple incoming chats?', 3, 'technical' from s;

-- 6) Optional: seed an evaluation (example placeholder)
-- with s as (
--   select id from interview_sessions where user_id = '{{YOUR_AUTH_USER_ID}}'::uuid order by created_at desc limit 1
-- )
-- insert into interview_evaluations (
--   session_id, overall_score, technical_score, behavioral_score, communication_score,
--   strengths, weaknesses, red_flags, recommendation, detailed_analysis
-- )
-- select id, 82, 78, 85, 84,
--   array['Empathetic', 'Clear communicator'],
--   array['Needs faster triage'],
--   array[]::text[],
--   'recommended',
--   'Good fit for L1 support with coaching on throughput.'
-- from s;

-- 7) View what was created (for quick checks)
select id, name, api_key from organizations order by created_at desc limit 1;
select id, email, organization_id from profiles where id = '{{YOUR_AUTH_USER_ID}}'::uuid;
select id, title from job_descriptions where user_id = '{{YOUR_AUTH_USER_ID}}'::uuid order by created_at desc limit 1;
select id, candidate_email, status from interview_sessions where user_id = '{{YOUR_AUTH_USER_ID}}'::uuid order by created_at desc limit 1;
select question_order, question_text from interview_questions order by created_at desc limit 3;
