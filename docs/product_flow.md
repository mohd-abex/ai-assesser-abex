# InterviewAI – Future‑Proof Product Flow (Standalone + Integrated)

This document explains the best possible, production‑quality flow of InterviewAI with dual operation modes:

1. Standalone SaaS app, and 2) Integrated sub‑product invoked by a parent hiring platform. It also maps each step to the tech stack, clarifies AI/STT/TTS concepts, and details robust webhook patterns.

---

## 0) Big Picture

- Modes of operation:
  - Standalone: Companies use InterviewAI directly (auth, dashboard, links, reports).
  - Integrated: Parent platform calls InterviewAI APIs to schedule interviews and receives results via webhooks.
- Core pipeline (per interview turn):
  Candidate audio → STT (transcription) → LLM (reasoning & follow‑ups) → TTS (AI voice reply) → Candidate hears next question.
- Evaluation artifacts:
  - Transcript (full), per‑question scores, overall score, strengths/weaknesses, recommendation, audio URLs.
- Architecture principles:
  - API‑first, versioned, idempotent, observable.
  - AI provider abstraction (tier‑based with factory pattern).
  - Event‑driven completion (webhooks with retries).
  - Secure, multi‑tenant (organizations + RLS).

---

## 1) User Journeys & Flows

### 1.1 Standalone Flow (Recruiter‑first)

1. Recruiter signs up and logs in.
2. Creates a Job Description (title, description, industry, difficulty).
3. InterviewAI generates 8–12 role‑appropriate questions.
4. Recruiter reviews/edits, then creates interview session(s) and copies invite links.
5. Candidate opens link, runs device checks, starts interview.
6. Turn‑based conversation runs (audio):
   - AI asks Q1 (TTS → audio), candidate answers (mic), STT transcribes,
     LLM evaluates + creates next follow‑up until time/turns are done.
7. Final evaluation is compiled and stored (scores, transcript, analysis).
8. Recruiter sees results in dashboard, filters/sorts, exports if needed.

Tech per step:

- Auth/UI: Next.js 14 App Router (TypeScript), Supabase Auth, shadcn/ui, Tailwind (design tokens), next-themes.
- Data: Supabase (Postgres + Storage), RLS policies.
- AI loop: FastAPI service (Python) or Next.js API routes calling providers; STT: Whisper (Groq/local),
  LLM: Llama 3.1 8B (dev) / GPT‑4o‑mini / Claude 3.5 (tiered), TTS: Edge TTS (dev) / Google / ElevenLabs.
- Realtime: WebSocket (Socket.io) for per‑turn updates, or HTTP turn‑based if simpler.

### 1.2 Integrated Flow (Parent Platform‑first)

1. Parent platform UI: “Schedule AI Interview” button.
2. Parent backend calls InterviewAI API `POST /api/v1/interviews/schedule` with candidate + JD identifiers.
3. InterviewAI returns `interview_id` + `interview_url`.
4. Parent platform sends the link to the candidate (email/SMS) and stores `interview_id` for tracking.
5. Candidate completes interview on InterviewAI (same UI as standalone).
6. On completion, InterviewAI posts a webhook to parent platform with results payload (signed, retryable).
7. Parent platform updates candidate’s record and shows results in its UI.

Tech per step:

- Integration boundary: API keys per organization; API versioning `/api/v1`.
- Webhooks: HMAC signatures, retries with exponential backoff, idempotency keys, 2xx handling.
- Observability: Structured logs, request IDs, event logs, dead‑letter queue if needed.

---

## 2) System Architecture (Logical)

Client (Browser)
↕ Web UI (Next.js App Router)
↕ Next.js API Routes (CRUD, scheduling, webhooks receiver for tests)
↔ FastAPI AI Service (STT/LLM/TTS orchestration)
↔ Supabase (Postgres + Storage + Auth)
↔ Upstash Redis (queues/rate‑limits, ephemeral session state)
↔ External Providers (Groq, Edge TTS, OpenAI, Anthropic, Google TTS, ElevenLabs)

Key choices:

- Keep CRUD/auth close to Next.js; keep AI pipelines in FastAPI for Python ecosystem strength.
- All AI calls go through provider interfaces selected by a factory using env + subscription tier.
- Socket.io (Node) channel for live interview turns or fall back to HTTP turn‑based.

---

## 3) Detailed Interview Pipeline (Per Session)

1. Session Initiation

   - Input: `interview_session.id`, selected tier, generated question set.
   - Action: Create ephemeral session state in Redis, mark session `in_progress`.
   - Output: Ready to start turn‑based loop.

2. Per‑Turn Loop
   a) Prompt Delivery

   - Build AI’s next utterance (question or follow‑up) using LLM with context (JD, prior answers).
   - Synthesize to audio via TTS and play to candidate.
     b) Candidate Response Capture
   - Record mic audio via MediaRecorder; chunk or per‑turn upload to Next.js → forwarded to FastAPI.
     c) Transcription (STT)
   - Whisper via Groq (dev) or paid. Return high‑accuracy transcript.
     d) Analysis + Next Step
   - LLM evaluates answer vs expectations, assigns per‑turn score and rationale.
   - Decide next follow‑up or proceed to next main question based on time/turn budget.
     e) Persistence
   - Store transcript, audio URL, ai_score, feedback in `interview_responses` table.

3. Completion & Evaluation Report
   - Aggregate per‑turn scores to compute overall, technical, behavioral, communication.
   - Generate strengths, weaknesses, red flags, recommendation.
   - Persist in `interview_evaluations` and mark session `completed`.
   - Emit event: `interview.completed` (standalone → updates dashboard; integrated → webhook).

Resilience:

- Timebox each turn (e.g., 90–120s max).
- Handle partial uploads, network retries, resume.
- Fallbacks: if TTS fails → text display; if STT fails → ask to repeat; if LLM fails → safe default prompt.

---

## 4) AI Abstraction & Tiers (Factory Pattern)

Interfaces (Python):

- STTProvider.transcribe(audio_bytes) → text
- LLMProvider.generate(prompt, context) → text/json
- TTSProvider.synthesize(text) → audio_bytes

Factory selects providers by `AI_ENV` (development/production) and `tier` (essential/professional/enterprise).

Dev (free):

- STT: Groq Whisper
- LLM: Groq Llama 3.1 8B
- TTS: Edge TTS

Prod:

- Essential: Whisper + Llama + Edge TTS
- Professional: Whisper + GPT‑4o‑mini + Google TTS
- Enterprise: Whisper + Claude 3.5 + ElevenLabs

Benefits:

- Swap vendors without changing business logic.
- Uniform error handling and metrics per interface.

---

## 5) Data Model (Supabase) – Key Tables

- profiles (extends auth.users with subscription and quota)
- organizations (integration tenants; api_key, webhook config, quotas)
- job_descriptions (title, description, industry, difficulty, custom_questions)
- interview_sessions (status, tier used, candidate info, timings)
- interview_questions (generated, ordered, typed)
- interview_responses (transcript, audio_url, per‑turn scoring)
- interview_evaluations (final aggregation and recommendation)
- api_request_logs (optional, for observability)

RLS:

- Profiles own their data; org members see their org’s data; public interview access is link‑scoped to that session only.

---

## 6) APIs (Versioned, API‑First)

Base: `/api/v1`

- Interviews
  - POST `/interviews/schedule` → returns `{ interview_id, interview_url, expires_at }`
  - GET `/interviews/:id/status` → returns status + minimal metadata
  - GET `/interviews/:id/results` → returns evaluation (auth‑gated)
- Candidates
  - POST `/candidates/invite` (optional helper)
- Webhooks
  - POST to partner endpoint with `event` + `data` (signed)

Auth:

- Standalone: Supabase Auth session.
- Integrated: `X-API-Key` for organization, rate‑limited and scoped.

Idempotency:

- Accept `Idempotency-Key` header for POSTs; store keys for 24h to prevent duplicates.

---

## 7) Webhook Strategy (Long‑Running & Reliable)

Why webhooks: Interviews are asynchronous and can take ~20 minutes.

Key patterns:

- 202 Accepted + async processing: scheduling endpoints should be quick.
- HMAC signatures: `X-Webhook-Signature: sha256=...` over body + secret.
- Retries: Exponential backoff (e.g., 1m, 5m, 30m, 2h, 6h), cap at 24–48h.
- Idempotency: Include `event_id`; receivers must dedupe.
- Dead‑letter: If all retries fail, park in DLQ and alert.
- Versioning: `X-Webhook-Version: 1` and payload `schema_version`.

Payload example:

```json
{
  "schema_version": 1,
  "event": "interview.completed",
  "event_id": "evt_01H...",
  "occurred_at": "2025-10-21T10:30:00Z",
  "data": {
    "interview_id": "int_01H...",
    "candidate": { "name": "Jane Doe", "email": "jane@ex.com" },
    "scores": {
      "overall": 84,
      "technical": 86,
      "behavioral": 78,
      "communication": 82
    },
    "recommendation": "highly_recommended",
    "transcript": "...",
    "turns": [
      { "q": "Tell me about...", "a": "...", "score": 8, "feedback": "..." }
    ],
    "artifacts": { "audio_urls": ["https://.../clip1.mp3", "..."] }
  }
}
```

Security:

- Rotate secrets; store per organization.
- Validate timestamp skew; reject old payloads.
- TLS only; never send secrets in payload.

---

## 8) Observability & Reliability

- Logging: Structured logs with request_id, session_id, org_id.
- Metrics: Per‑provider latency, success/error rates, cost attribution per interview.
- Tracing: Correlate front‑end events to backend actions (OpenTelemetry optional).
- Rate limits: Per API key; protect STT/LLM endpoints.
- Quotas: Enforce per subscription/org; monthly reset job.

---

## 9) Frontend Experience (Accessibility + Theming)

- Next.js App Router, React 18, Suspense boundaries for loading states.
- shadcn/ui with Tailwind CSS; use design tokens (never hard‑coded colors).
- next-themes with `.dark` class on html for dark mode.
- Device checks: mic permissions, audio test.
- Resilience: clear error messages, retry prompts, resume session if tab reloads.

---

## 10) Security & Compliance

- AuthN: Supabase Auth; API keys for integrations.
- AuthZ: RLS in Postgres, per‑row ownership + organization scoping.
- Storage: Private buckets for recordings; signed URLs for limited time access.
- PII: Minimize and encrypt at rest; configurable data retention.
- Compliance: GDPR/CCPA aligned workflows; deletion on request.

---

## 11) Newcomer Glossary

- STT (Speech‑to‑Text): Converts speech audio into written text. We use Whisper models (Groq API in dev).
- LLM (Large Language Model): AI that understands/generates text. Used to ask questions, analyze answers, and score.
- TTS (Text‑to‑Speech): Converts text into spoken audio so the AI ‘talks’. Edge TTS (free) in dev.
- Webhook: An HTTP callback that our system sends to another system when an event happens (e.g., interview completed).
- Idempotency: Making repeated requests safe; duplicates won’t create duplicate resources.
- RLS (Row Level Security): Database feature restricting each user/org to only their rows.
- Provider Abstraction: Coding pattern to swap AI vendors without changing business logic.

---

## 12) Tech Stack by Layer (Final)

- Frontend: Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui, next-themes, Zustand
- Backend (App): Next.js API routes (CRUD, scheduling, auth checks), Socket.io server
- AI Service: FastAPI (Python), pydantic, uvicorn; providers for STT/LLM/TTS
- Data: Supabase (Postgres, Storage, Auth), migrations + RLS
- Realtime/Cache: Upstash Redis (rate limits, sessions, queues)
- AI Providers (Dev): Groq Whisper, Groq Llama 3.1 8B, Edge TTS
- AI Providers (Prod by Tier): GPT‑4o‑mini, Claude 3.5, Google/ElevenLabs TTS
- Infra: Vercel (frontend), Railway/Render/Fly (FastAPI), environment‑based switching
- Observability: App logs, optional OpenTelemetry, webhook DLQ

---

## 13) Future‑Proofing Checklist

- API versioning from day one (`/api/v1`), explicit deprecation policy.
- Provider abstraction + feature flags for rolling upgrades.
- Organization‑scoped multi‑tenant model; API keys with rotation.
- Webhooks with retries, signatures, and idempotency.
- Strict adherence to design tokens and App Router conventions.
- Database indices on hot paths; background job for monthly quota resets.
- Blue/green deploys where possible; health checks for AI service.

---

## 14) Visual Flow (Text Diagram)

Standalone
Recruiter → Create JD → Gen Questions → Create Session → Send Link → Candidate Interview → Evaluate → Dashboard Results

Integrated
Parent Platform → Schedule API → Get Link → Candidate Interview (InterviewAI) → Webhook Results → Parent Dashboard

---

This flow is designed to be robust, scalable, and adaptable, supporting both independent operation and seamless integration with a parent hiring platform while keeping AI vendors swappable and costs observable.
