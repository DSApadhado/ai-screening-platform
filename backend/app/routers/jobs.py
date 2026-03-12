import io
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Job, Candidate
from app.services.resume_service import extract_text_from_pdf_bytes, extract_text_from_pdf_file
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/")
async def create_job(title: str = Form(...), description: str = Form(...), db: AsyncSession = Depends(get_db)):
    job = Job(title=title, description=description)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return {"id": job.id, "title": job.title}


@router.get("/")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    jobs = result.scalars().all()
    return [{"id": j.id, "title": j.title, "created_at": str(j.created_at)} for j in jobs]


@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.total_score.desc()))
    candidates = result.scalars().all()
    return {
        "id": job.id, "title": job.title, "description": job.description,
        "created_at": str(job.created_at),
        "candidates": [_candidate_dict(c) for c in candidates],
    }


@router.post("/{job_id}/upload-candidates")
async def upload_candidates(
    job_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    content = await file.read()
    try:
        if file.filename and (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {e}")

    col_map = {}
    for col in df.columns:
        cl = col.strip().lower().replace(" ", "_")
        col_map[col] = cl
    df.rename(columns=col_map, inplace=True)

    required = {"name", "email"}
    if not required.issubset(set(df.columns)):
        raise HTTPException(400, f"CSV must contain columns: {required}. Found: {list(df.columns)}")

    added = 0
    for _, row in df.iterrows():
        c = Candidate(
            job_id=job_id,
            s_no=int(row.get("s_no", 0)) if pd.notna(row.get("s_no")) else None,
            name=str(row.get("name", "")),
            email=str(row.get("email", "")),
            college=str(row.get("college", "")),
            branch=str(row.get("branch", "")),
            cgpa=float(row["cgpa"]) if pd.notna(row.get("cgpa")) else None,
            best_ai_project=str(row.get("best_ai_project", "")) if pd.notna(row.get("best_ai_project")) else None,
            research_work=str(row.get("research_work", "")) if pd.notna(row.get("research_work")) else None,
            github_url=str(row.get("github", "")) if pd.notna(row.get("github")) else None,
            resume_url=str(row.get("resume", "")) if pd.notna(row.get("resume")) else None,
            test_la=float(row["test_la"]) if pd.notna(row.get("test_la")) else None,
            test_code=float(row["test_code"]) if pd.notna(row.get("test_code")) else None,
            status="uploaded",
        )
        db.add(c)
        added += 1

    await db.commit()
    return {"message": f"Uploaded {added} candidates", "count": added}


@router.post("/{job_id}/upload-resumes")
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload resume PDF files directly. Filenames should match student{N}.pdf pattern."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.s_no))
    candidates = result.scalars().all()

    processed = 0
    for upload_file in files:
        content = await upload_file.read()
        text = extract_text_from_pdf_bytes(content)

        # Try to match by filename pattern studentN.pdf
        fname = upload_file.filename or ""
        import re
        match = re.search(r"student(\d+)", fname.lower())
        if match:
            sno = int(match.group(1))
            for c in candidates:
                if c.s_no == sno:
                    c.resume_text = text
                    processed += 1
                    break
        else:
            # Assign to next candidate without resume text
            for c in candidates:
                if not c.resume_text:
                    c.resume_text = text
                    processed += 1
                    break

    await db.commit()
    return {"message": f"Processed {processed} resumes", "count": processed}


@router.post("/{job_id}/upload-test-results")
async def upload_test_results(
    job_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    content = await file.read()
    if file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))

    col_map = {}
    for col in df.columns:
        col_map[col] = col.strip().lower().replace(" ", "_")
    df.rename(columns=col_map, inplace=True)

    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id))
    candidates = {c.s_no: c for c in result.scalars().all()}

    updated = 0
    for _, row in df.iterrows():
        sno = int(row.get("s_no", 0)) if pd.notna(row.get("s_no")) else None
        if sno and sno in candidates:
            c = candidates[sno]
            c.test_la = float(row["test_la"]) if pd.notna(row.get("test_la")) else c.test_la
            c.test_code = float(row["test_code"]) if pd.notna(row.get("test_code")) else c.test_code
            if c.test_la is not None and c.test_code is not None:
                c.test_total = (c.test_la + c.test_code) / 2
                c.status = "test_scored"
            updated += 1

    await db.commit()
    return {"message": f"Updated test results for {updated} candidates"}


def _candidate_dict(c: Candidate) -> dict:
    return {
        "id": c.id, "s_no": c.s_no, "name": c.name, "email": c.email,
        "college": c.college, "branch": c.branch, "cgpa": c.cgpa,
        "best_ai_project": c.best_ai_project, "research_work": c.research_work,
        "github_url": c.github_url, "resume_url": c.resume_url,
        "resume_text": c.resume_text[:200] if c.resume_text else None,
        "github_analysis": c.github_analysis[:200] if c.github_analysis else None,
        "ai_evaluation": c.ai_evaluation, "ai_score": c.ai_score,
        "resume_score": c.resume_score, "github_score": c.github_score,
        "jd_match_score": c.jd_match_score, "project_score": c.project_score,
        "research_score": c.research_score, "total_score": c.total_score,
        "test_la": c.test_la, "test_code": c.test_code, "test_total": c.test_total,
        "final_score": c.final_score, "status": c.status,
        "interview_time": str(c.interview_time) if c.interview_time else None,
        "meet_link": c.meet_link, "email_sent": c.email_sent,
        "score_breakdown": c.score_breakdown,
    }
