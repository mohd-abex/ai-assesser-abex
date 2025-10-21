# Supabase Setup – InterviewAI

This guide shows how to apply the schema and seed your Supabase project for InterviewAI.

## Prerequisites

- A Supabase project (URL, Anon Key, Service Role Key)
- Access to the SQL Editor in the Supabase dashboard

## 1) Apply Schema Migration

1. Open Supabase Dashboard → SQL → New Query.
2. Open the file `supabase/migrations/20251021_0001_init_schema.sql` locally and copy its contents.
3. Paste into the SQL editor and run it.
4. Verify:
   - Tables created (organizations, profiles, job_descriptions, interview_sessions, interview_questions, interview_responses, interview_evaluations, api_request_logs)
   - RLS enabled and policies present
   - Buckets created (`interview-recordings`, `candidate-resumes`)
   - Function `reset_monthly_quota()` exists

If your project doesn’t support `pg_cron`, comment out the last schedule line or schedule resets externally.

## 2) Seed Data

1. Create a test user in Auth (Authentication → Users) or sign up via app later.
2. Copy the user’s `id` (UUID) from `auth.users`.
3. Open `supabase/seed.sql` and replace `{{YOUR_AUTH_USER_ID}}` with that UUID.
4. Paste the modified seed.sql into the SQL editor and run it.
5. Verify:
   - One organization exists with an API key and webhook secret
   - Your profile row is linked to that organization
   - A sample job description and interview session exist
   - A few interview questions seeded for that session

## 3) Storage Buckets

The migration creates private buckets:

- `interview-recordings` (audio uploads) – use signed URLs for access.
- `candidate-resumes` (resumes) – also private; signed URLs for access.

Upload test files via Storage Explorer to confirm permissions.

## 4) Environment Variables (Frontend)

Add to `frontend/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key> # keep server-side only
```

## 5) Common Issues

- RLS blocking queries: Ensure you’re authenticated; use the service role key server-side.
- Buckets not present: Re-run the storage bucket creation statements from the migration.
- Missing pg_cron: Comment out the schedule line; use an external scheduler to call `select reset_monthly_quota();` monthly.

## 6) Next Steps

- Proceed to Frontend Init (Next.js App Router) as per `../docs/development_topology.md` Step 3.
- Implement Supabase client (v2) in `frontend/lib/supabase/`.
