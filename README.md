# AI-Powered Candidate Screening Platform

An intelligent recruitment automation system that evaluates candidates using AI-powered resume analysis, GitHub profile assessment, and job description matching. Automates the full hiring pipeline from candidate upload to interview scheduling.

## Features

- **CSV/XLSX Upload** — Import candidate data dynamically
- **Resume Processing** — PDF parsing with pdfplumber + PyPDF2
- **GitHub Analysis** — Repository-level evaluation via GitHub API
- **AI Evaluation** — GPT-4o-mini multi-dimensional scoring with explainable reasoning
- **Candidate Ranking** — Weighted scoring across resume, GitHub, JD match, projects, research
- **Automated Emails** — Send test links and interview invitations via SMTP
- **Test Result Integration** — Upload and combine test scores with AI evaluation
- **Interview Scheduling** — Google Calendar + Meet link generation
- **Recruiter Dashboard** — Visual charts, score breakdowns, pipeline controls

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key
- Gmail App Password (for emails)
- Google Cloud OAuth credentials (for Calendar)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

### Google Calendar Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to the `backend/` directory
5. On first run, a browser window will open for OAuth consent
6. The token is saved as `token.json` for subsequent runs

### Docker

```bash
# Build frontend first
cd frontend && npm run build && cd ..

# Build and run
docker build -t ai-screening .
docker run -p 8000:8000 --env-file backend/.env ai-screening
```

## Usage

1. **Create a Job** — Enter title and detailed job description
2. **Upload Candidates** — CSV/XLSX with columns: s_no, name, email, college, branch, cgpa, best_ai_project, research_work, github, resume
3. **Upload Resumes** — PDF files named `student{N}.pdf`
4. **Run Pipeline** — Click "Run Full Pipeline" or execute steps individually
5. **Review Results** — Click any candidate for detailed AI evaluation breakdown
6. **Upload Test Results** — CSV with s_no, test_la, test_code columns
7. **Schedule Interviews** — Auto-creates Google Calendar events with Meet links

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs/` | Create job |
| GET | `/api/jobs/` | List jobs |
| GET | `/api/jobs/{id}` | Get job with candidates |
| POST | `/api/jobs/{id}/upload-candidates` | Upload candidate CSV |
| POST | `/api/jobs/{id}/upload-resumes` | Upload resume PDFs |
| POST | `/api/jobs/{id}/upload-test-results` | Upload test results |
| POST | `/api/pipeline/{id}/process-resumes` | Extract resume text |
| POST | `/api/pipeline/{id}/analyze-github` | Analyze GitHub profiles |
| POST | `/api/pipeline/{id}/evaluate` | AI evaluate candidates |
| POST | `/api/pipeline/{id}/shortlist` | Shortlist top candidates |
| POST | `/api/pipeline/{id}/send-test-links` | Email test links |
| POST | `/api/pipeline/{id}/score-tests` | Score with test results |
| POST | `/api/pipeline/{id}/schedule-interviews` | Schedule interviews |
| POST | `/api/pipeline/{id}/run-full-pipeline` | Run complete pipeline |
