# InterviewAI – Development Topology (Step‑by‑Step Guide)

A topological, ordered guide to build InterviewAI with a smooth developer experience. Each step is minimal, verifiable, and aligned with the product flow and tech stack.

This focuses on two modes: Standalone (full SaaS) and Integrated (API‑first + webhooks). You can complete Standalone first, then enable integration.

---

## 0) Prerequisites

- Accounts: Supabase, Vercel, Railway/Render/Fly (for FastAPI), Groq (API key)
- Tools: Node.js ≥ 18, pnpm or npm, Python ≥ 3.10, uv or pip, Git
- Optional: Upstash Redis account (free tier) for sessions/queues

---

## 1) Repository Scaffold

1. Create monorepo structure:

```
interview-ai/
  frontend/
  ai-service/
  supabase/
  docs/
```

2. Initialize Git and README.

3. Commit.

Verification: Repo structure exists; initial commit pushed.

---

## 2) Supabase Setup (Database + Auth)

1. Create Supabase project; obtain URL, anon key, service role key.
2. Create `supabase/migrations` with schema from context (profiles, job_descriptions, interview_sessions, interview_questions, interview_responses, interview_evaluations, organizations, api_request_logs). Apply migrations via Supabase SQL editor.
3. Configure Storage buckets:
   - `interview-recordings` (private)
   - `candidate-resumes` (private)
4. Enable RLS on all tables and create policies (use templates from context; start with profile policies, then mirror for related tables).
5. Create function `reset_monthly_quota()` and indexes.

Verification: Tables exist, RLS enabled, buckets created, function runs.

---

## 3) Frontend Init (Next.js 14 + App Router)

1. Create Next.js app in `frontend/` with TypeScript and App Router.
2. Install deps: `next`, `react`, `typescript`, `tailwindcss`, `@supabase/supabase-js@^2`, `zustand`, `zod`, `shadcn/ui`, `next-themes`, `socket.io-client`.
3. Add Tailwind + globals with design tokens (from context) and `tailwind.config.ts`.
4. Set up shadcn/ui and `ThemeToggle`.
5. Add Supabase clients (`lib/supabase/client.ts`, `server.ts`).
6. Add `(auth)` routes: signup/login.
7. Set up layout and dark mode provider.

Env (`frontend/.env.local`):

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_APP_URL=http://localhost:3000
AI_SERVICE_URL=http://localhost:8000
AI_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Verification: App starts, can toggle dark mode, can sign up/login.

---

## 4) AI Service Init (FastAPI)

1. Create `ai-service/app` with `main.py`, `config.py`, `models/{base.py, stt.py, llm.py, tts.py}`, `services/{question_generator.py, interview_service.py, evaluation_service.py}`, `routers/{interview.py, transcribe.py, synthesize.py}`.
2. Add `requirements.txt` (fastapi, uvicorn, pydantic v2, python-multipart, groq, edge-tts, openai-whisper, python-dotenv).
3. Implement provider interfaces and a simple factory by env + tier (dev: Groq Whisper/Llama + Edge TTS).
4. Expose endpoints:
   - POST `/transcribe` (audio → text)
   - POST `/synthesize` (text → audio)
   - POST `/interview/turn` (state + audio → next prompt + score)
   - POST `/questions/generate` (JD → questions)

Env (`ai-service/.env`):

```
AI_ENV=development
GROQ_API_KEY=...
EDGE_TTS_ENABLED=true
DEFAULT_TIER=essential
```

Verification: `uvicorn app.main:app --reload` responds; curl transcribe returns text (stub OK).

---

## 5) Wire Frontend ↔ AI Service

1. In `frontend/lib/ai-service/client.ts`, add a thin client to call FastAPI endpoints using `AI_SERVICE_URL`.
2. Create a page to generate questions from a JD using the AI service; persist to Supabase.
3. Create an interview session in Supabase and produce a public invite link.

Verification: JD → questions stored; session created; invite link visible.

---

## 6) Public Interview Page (Turn‑Based)

1. Route: `app/(public)/interview/[id]/page.tsx`.
2. Components: device check, TTS playback for prompts, mic capture with MediaRecorder.
3. On each turn: upload audio → FastAPI `/transcribe` → call `/interview/turn` → get follow‑up + per‑turn score.
4. Persist `interview_responses` and progress until time/turns end. Mark session completed and trigger evaluation.

Verification: Can complete an interview; responses recorded in DB.

---

## 7) Evaluation & Reports

1. Use `evaluation_service.py` to aggregate per‑turn results into final scores and analysis; store in `interview_evaluations`.
2. Dashboard page to list candidates and view detailed report: overall score, per‑category, transcript, strengths/weaknesses, recommendation.

Verification: Recruiter can see completed interviews and open full reports.

---

## 8) Integration APIs (Parent Platform)

1. Next.js route handlers under `frontend/app/api/v1`:
   - POST `/interviews/schedule` (X-API-Key, Idempotency-Key) → returns `{ interview_id, interview_url }` quickly (202 async acceptable).
   - GET `/interviews/:id/status`
   - GET `/interviews/:id/results` (org‑scoped access)
2. Organization model: Create `organizations` table and link `profiles.organization_id`. Add API key issuance (manual for MVP) and validation middleware.

Verification: With a test API key, parent can create an interview and poll status.

---

## 9) Webhooks (Outgoing)

1. Create a webhook dispatcher in frontend backend or FastAPI (choose one owner; recommend frontend backend for proximity to DB updates).
2. On `interview.completed`, enqueue delivery with retries (1m, 5m, 30m, 2h, 6h). Sign with HMAC secret per organization.
3. Build a simple webhook receiver echo endpoint for local testing.

Verification: Webhook hits receiver; retries on failure; idempotency respected.

---

## 10) Realtime Enhancements (Optional)

- Introduce Socket.io for streaming partial transcripts and live token responses.
- Keep turn‑based protocol as fallback for reliability.

Verification: Live updates appear; fallback works offline.

---

## 11) Quotas, Tiers, and Billing Hooks

1. Enforce monthly quotas from `profiles` and/or `organizations` before scheduling/starting interviews.
2. Log model usage/cost by interview; attribute to tier for analytics.
3. Add switches to upgrade tier and reflect in factory selection.

Verification: Requests blocked when over quota; usage visible in admin view.

---

## 12) Security, Compliance, and RLS Validation

- Verify RLS prevents cross‑tenant access.
- Private storage with signed URLs time‑boxed.
- GDPR deletion workflow (hard‑delete or tombstone + revoke Storage objects).

Verification: Tests show isolation and proper access control.

---

## 13) Deployment

- Frontend: Vercel with env vars (Supabase, AI service URL, Redis URL).
- AI service: Railway/Render/Fly with `.env` secrets.
- Domains and CORS configured; HTTPS enforced.

Verification: Production URLs live; health endpoints pass.

---

## 14) Observability & Ops

- Structured logging with request/session IDs.
- Basic metrics (success rates, latencies) per provider.
- Alerting on DLQ webhook events and AI failures.

Verification: Logs searchable; errors trigger alerts.

---

## 15) Appendix – Helpful Snippets

Env examples:

```
# frontend/.env.local
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
AI_SERVICE_URL=http://localhost:8000
AI_ENV=development
REDIS_URL=...
```

```
# ai-service/.env
AI_ENV=development
GROQ_API_KEY=...
EDGE_TTS_ENABLED=true
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_CLOUD_TTS_KEY=
ELEVENLABS_API_KEY=
DEFAULT_TIER=essential
```

Optional commands to remember:

- Start Next.js dev server
- Run FastAPI with uvicorn
- Test webhook with curl

This topology ensures a smooth path: database → app → AI → integration → reliability. Follow in order, verify each step, and you’ll avoid rework while staying future‑proof.
