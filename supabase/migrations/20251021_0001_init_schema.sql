-- InterviewAI Initial Database Schema and Storage Buckets
-- Date: 2025-10-21

-- Extensions
create extension if not exists pgcrypto;
create extension if not exists pg_cron;

-- Helper: auto-update updated_at
create or replace function trigger_set_timestamp()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Organizations (integration tenants)
create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  contact_email text,

  -- API Authentication
  api_key text unique not null,
  api_key_created_at timestamptz default now(),
  api_key_last_used_at timestamptz,

  -- Integration Settings
  webhook_url text,
  webhook_secret text,

  -- Quota & Billing
  quota_per_month integer default 1000,
  quota_used_this_month integer default 0,
  quota_reset_date timestamptz default (now() + interval '1 month'),

  -- Status
  is_active boolean default true,

  -- Metadata
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create trigger organizations_set_timestamp
before update on organizations
for each row execute function trigger_set_timestamp();

-- Profiles (extend auth.users)
create table if not exists profiles (
  id uuid references auth.users on delete cascade primary key,
  email text unique not null,
  full_name text,
  company_name text,
  organization_id uuid references organizations(id),
  subscription_tier text check (subscription_tier in ('essential','professional','enterprise')) default 'essential',
  subscription_status text check (subscription_status in ('active','canceled','past_due')) default 'active',
  interviews_quota integer default 100,
  interviews_used_this_month integer default 0,
  quota_reset_date timestamptz default now(),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create trigger profiles_set_timestamp
before update on profiles
for each row execute function trigger_set_timestamp();

-- Job Descriptions
create table if not exists job_descriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade not null,
  title text not null,
  description text not null,
  industry text not null,
  difficulty text check (difficulty in ('easy','medium')) default 'easy',
  custom_questions jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create trigger job_descriptions_set_timestamp
before update on job_descriptions
for each row execute function trigger_set_timestamp();

-- Interview Sessions
create table if not exists interview_sessions (
  id uuid primary key default gen_random_uuid(),
  job_description_id uuid references job_descriptions(id) on delete cascade not null,
  user_id uuid references profiles(id) on delete cascade not null,
  candidate_name text,
  candidate_email text not null,
  status text check (status in ('pending','in_progress','completed','failed')) default 'pending',
  ai_tier_used text not null,
  started_at timestamptz,
  completed_at timestamptz,
  duration_seconds integer,
  created_at timestamptz default now()
);

-- Interview Questions
create table if not exists interview_questions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references interview_sessions(id) on delete cascade not null,
  question_text text not null,
  question_order integer not null,
  question_type text check (question_type in ('technical','behavioral','situational')) not null,
  created_at timestamptz default now()
);

-- Interview Responses
create table if not exists interview_responses (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references interview_sessions(id) on delete cascade not null,
  question_id uuid references interview_questions(id) on delete cascade not null,
  transcript text not null,
  audio_url text,
  response_time_seconds integer,
  ai_score integer check (ai_score between 0 and 100),
  ai_feedback text,
  created_at timestamptz default now()
);

-- Interview Evaluations (final)
create table if not exists interview_evaluations (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references interview_sessions(id) on delete cascade not null,
  overall_score integer check (overall_score between 0 and 100) not null,
  technical_score integer check (technical_score between 0 and 100),
  behavioral_score integer check (behavioral_score between 0 and 100),
  communication_score integer check (communication_score between 0 and 100),
  strengths text[],
  weaknesses text[],
  red_flags text[],
  recommendation text check (recommendation in ('highly_recommended','recommended','not_recommended')) not null,
  detailed_analysis text,
  created_at timestamptz default now()
);

-- API Request Logs (optional observability)
create table if not exists api_request_logs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references organizations(id) on delete cascade,
  endpoint text not null,
  method text not null,
  status_code integer,
  response_time_ms integer,
  created_at timestamptz default now()
);

-- Create buckets via direct insert for broader compatibility; idempotent with ON CONFLICT
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'interview-recordings',
  'interview-recordings',
  false,
  52428800::bigint,
  array['audio/mpeg','audio/webm','audio/ogg']::text[]
)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'candidate-resumes',
  'candidate-resumes',
  false,
  20971520::bigint,
  array['application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document']::text[]
)
on conflict (id) do nothing;

-- RLS
alter table organizations enable row level security;
alter table profiles enable row level security;
alter table job_descriptions enable row level security;
alter table interview_sessions enable row level security;
alter table interview_questions enable row level security;
alter table interview_responses enable row level security;
alter table interview_evaluations enable row level security;
alter table api_request_logs enable row level security;

-- Policies: Organizations (org-only access via API key/service role in backend; restrict from client)
create policy "Org read by members"
  on organizations for select
  using (id in (select organization_id from profiles where id = auth.uid()));

create policy "Org update by members"
  on organizations for update
  using (id in (select organization_id from profiles where id = auth.uid()));

-- Policies: Profiles (self service)
create policy "Profiles: view own"
  on profiles for select
  using (auth.uid() = id);

create policy "Profiles: update own"
  on profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Policies: Job Descriptions (owner based)
create policy "JDs: owner read"
  on job_descriptions for select
  using (user_id = auth.uid());

create policy "JDs: owner insert"
  on job_descriptions for insert
  with check (user_id = auth.uid());

create policy "JDs: owner update"
  on job_descriptions for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "JDs: owner delete"
  on job_descriptions for delete
  using (user_id = auth.uid());

-- Policies: Interview Sessions (owner based)
create policy "Sessions: owner read"
  on interview_sessions for select
  using (user_id = auth.uid());

create policy "Sessions: owner insert"
  on interview_sessions for insert
  with check (user_id = auth.uid());

create policy "Sessions: owner update"
  on interview_sessions for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Sessions: owner delete"
  on interview_sessions for delete
  using (user_id = auth.uid());

-- Policies: Questions/Responses/Evaluations (join via session ownership)
create policy "Questions: owner read"
  on interview_questions for select
  using (exists (
    select 1 from interview_sessions s where s.id = interview_questions.session_id and s.user_id = auth.uid()
  ));

create policy "Questions: owner insert"
  on interview_questions for insert
  with check (exists (
    select 1 from interview_sessions s where s.id = interview_questions.session_id and s.user_id = auth.uid()
  ));

create policy "Questions: owner update"
  on interview_questions for update
  using (exists (
    select 1 from interview_sessions s where s.id = interview_questions.session_id and s.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from interview_sessions s where s.id = interview_questions.session_id and s.user_id = auth.uid()
  ));

create policy "Responses: owner read"
  on interview_responses for select
  using (exists (
    select 1 from interview_sessions s where s.id = interview_responses.session_id and s.user_id = auth.uid()
  ));

create policy "Responses: owner insert"
  on interview_responses for insert
  with check (exists (
    select 1 from interview_sessions s where s.id = interview_responses.session_id and s.user_id = auth.uid()
  ));

create policy "Responses: owner update"
  on interview_responses for update
  using (exists (
    select 1 from interview_sessions s where s.id = interview_responses.session_id and s.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from interview_sessions s where s.id = interview_responses.session_id and s.user_id = auth.uid()
  ));

create policy "Evaluations: owner read"
  on interview_evaluations for select
  using (exists (
    select 1 from interview_sessions s where s.id = interview_evaluations.session_id and s.user_id = auth.uid()
  ));

create policy "Evaluations: owner insert"
  on interview_evaluations for insert
  with check (exists (
    select 1 from interview_sessions s where s.id = interview_evaluations.session_id and s.user_id = auth.uid()
  ));

-- Indexes
create index if not exists idx_job_descriptions_user_id on job_descriptions(user_id);
create index if not exists idx_interview_sessions_user_id on interview_sessions(user_id);
create index if not exists idx_interview_sessions_status on interview_sessions(status);
create index if not exists idx_interview_questions_session_id on interview_questions(session_id);
create index if not exists idx_interview_responses_session_id on interview_responses(session_id);
create index if not exists idx_interview_evaluations_session_id on interview_evaluations(session_id);
create index if not exists idx_api_logs_org_id on api_request_logs(organization_id);
create index if not exists idx_api_logs_created_at on api_request_logs(created_at);

-- Quota Reset Function (profiles + organizations)
create or replace function reset_monthly_quota()
returns void as $$
begin
  update profiles
  set interviews_used_this_month = 0,
      quota_reset_date = now() + interval '1 month'
  where quota_reset_date < now();

  update organizations
  set quota_used_this_month = 0,
      quota_reset_date = now() + interval '1 month'
  where quota_reset_date < now();
end;
$$ language plpgsql;

-- Optional: schedule monthly reset (pg_cron)
select cron.schedule('reset-quota-monthly', '0 0 1 * *', $$ select reset_monthly_quota(); $$);
