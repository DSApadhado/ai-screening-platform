# AI-Powered Candidate Screening Platform — Architecture Document

## 1. System Overview

A full-stack recruitment automation platform that uses AI to evaluate, rank, and progress candidates through a hiring pipeline. The system integrates resume parsing, GitHub profile analysis, LLM-based evaluation, automated emailing, and Google Calendar scheduling.

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async) |
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts |
| AI/LLM | OpenAI GPT-4o-mini (via API) |
| Database | SQLite (async via aiosqlite) |
| Email | SMTP (Gmail) |
| Calendar | Google Calendar API + Google Meet |
| Build | Vite 5 |
| Deployment | Docker, Railway/Render |

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ Home Page│ │ Job Dashboard│ │ Candidate Detail │  │
│  └──────────┘ └──────────────┘ └─────────────────┘  │
│         │            │                │              │
│         └────────────┼────────────────┘              │
│                      │ Axios HTTP                    │
└──────────────────────┼──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 FastAPI Backend                        │
│                                                       │
│  ┌─────────────┐  ┌──────────────────────────────┐   │
│  │ Jobs Router  │  │     Pipeline Router           │   │
│  │ - CRUD jobs  │  │ - Process resumes             │   │
│  │ - Upload CSV │  │ - Analyze GitHub              │   │
│  │ - Upload PDF │  │ - AI evaluate                 │   │
│  │ - Test results│ │ - Shortlist                   │   │
│  └──────┬───────┘  │ - Send test emails            │   │
│         │          │ - Score tests                  │   │
│         │          │ - Schedule interviews          │   │
│         │          │ - Run full pipeline            │   │
│         │          └──────────┬───────────────────┘   │
│         │                    │                        │
│  ┌──────▼────────────────────▼──────────────────┐    │
│  │              Service Layer                    │    │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐  │    │
│  │  │Resume Svc  │ │GitHub Svc  │ │ AI Svc   │  │    │
│  │  │- Download  │ │- Fetch repos│ │- LLM eval│  │    │
│  │  │- PDF parse │ │- Languages │ │- Scoring │  │    │
│  │  └────────────┘ │- READMEs  │ └──────────┘  │    │
│  │                 └────────────┘                │    │
│  │  ┌────────────┐ ┌────────────────────────┐   │    │
│  │  │Email Svc   │ │Calendar Svc            │   │    │
│  │  │- SMTP send │ │- Google Calendar API   │   │    │
│  │  │- Templates │ │- Meet link generation  │   │    │
│  │  └────────────┘ │- Slot finding          │   │    │
│  │                 └────────────────────────┘   │    │
│  └──────────────────────────────────────────────┘    │
│                       │                               │
│              ┌────────▼────────┐                      │
│              │   SQLite DB     │                      │
│              │  - Jobs         │                      │
│              │  - Candidates   │                      │
│              └─────────────────┘                      │
└──────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ OpenAI   │  │ GitHub   │  │ Google APIs   │
   │ API      │  │ API      │  │ Calendar+Meet │
   └──────────┘  └──────────┘  └──────────────┘
```

## 4. AI Evaluation Approach

### 4.1 Multi-Dimensional Scoring

Each candidate is evaluated across 5 dimensions (0-100 each):

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Resume Score | 15% | Quality of experience, skills, education |
| GitHub Score | 15% | Code quality, project diversity, activity |
| JD Match Score | 20% | Alignment with job description requirements |
| Project Score | 15% | Quality and relevance of AI projects |
| Research Score | 10% | Research publications and contributions |

### 4.2 Test Score Integration

When test results are available, the scoring adjusts:
- AI evaluation: 75% weight
- Test scores (avg of logical aptitude + coding): 25% weight

### 4.3 Explainable AI

Every score includes:
- Per-dimension reasoning from the LLM
- Strengths and weaknesses list
- Overall summary
- Recommendation (strong_yes / yes / maybe / no)

### 4.4 GitHub Analysis

Repository-level evaluation including:
- Language diversity and proficiency
- Project descriptions and README quality
- Star count and community engagement
- Non-fork original work assessment
- Topic/tag relevance

## 5. Pipeline Workflow

```
1. Create Job → Define title + detailed job description
2. Upload Candidates → CSV/XLSX with candidate data
3. Upload Resumes → PDF files matched by student{N}.pdf pattern
4. Process Resumes → Extract text from PDFs (pdfplumber + PyPDF2)
5. Analyze GitHub → Fetch repos, languages, READMEs via GitHub API
6. AI Evaluate → GPT-4o-mini scores each candidate against JD
7. Shortlist → Top N candidates above minimum score threshold
8. Send Test Links → Email assessment links to shortlisted candidates
9. Upload Test Results → CSV with logical aptitude + coding scores
10. Score Tests → Combine AI + test scores for final ranking
11. Schedule Interviews → Google Calendar events with Meet links
```

Each step can be run individually or as a full pipeline.

## 6. Data Model

### Job
- id, title, description, created_at

### Candidate
- Basic: id, job_id, s_no, name, email, college, branch, cgpa
- Content: best_ai_project, research_work, github_url, resume_url
- Processed: resume_text, github_analysis, ai_evaluation
- Scores: resume_score, github_score, jd_match_score, project_score, research_score, ai_score, total_score
- Tests: test_la, test_code, test_total, final_score
- Pipeline: status, interview_time, meet_link, email_sent, score_breakdown

## 7. Scalability Considerations

- **Async throughout**: FastAPI + async SQLAlchemy + async HTTP clients
- **Stateless backend**: Can horizontally scale behind a load balancer
- **Database**: SQLite for demo; swap to PostgreSQL for production via DATABASE_URL
- **Rate limiting**: GitHub API calls are batched per candidate; OpenAI calls use gpt-4o-mini for cost efficiency
- **File processing**: Resume PDFs processed in-memory, no disk dependency
- **Modular services**: Each service (AI, GitHub, Email, Calendar) is independent and replaceable

## 8. Security

- CORS configured for production origins
- Environment variables for all secrets
- Google OAuth2 with token refresh
- No credentials stored in code
