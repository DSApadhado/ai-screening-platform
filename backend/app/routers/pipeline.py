import json
import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Job, Candidate
from app.services.resume_service import download_and_extract_resume
from app.services.github_service import analyze_github_profile
from app.services.ai_service import evaluate_candidate, compute_final_score, generate_dynamic_weights
from app.services.email_service import send_test_link_email, send_interview_email
from app.services.calendar_service import schedule_interview, find_available_slots
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/{job_id}/process-resumes")
async def process_resumes(job_id: int, db: AsyncSession = Depends(get_db)):
    """Download and extract text from candidate resumes."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id))
    candidates = result.scalars().all()

    processed = 0
    for c in candidates:
        if c.resume_text:
            processed += 1
            continue
        if c.resume_url and str(c.resume_url).lower() != "nan":
            text = await download_and_extract_resume(c.resume_url, UPLOAD_DIR)
            if text:
                c.resume_text = text
                processed += 1

    await db.commit()
    return {"message": f"Processed {processed}/{len(candidates)} resumes"}


@router.post("/{job_id}/analyze-github")
async def analyze_github(job_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze GitHub profiles for all candidates."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id))
    candidates = result.scalars().all()

    analyzed = 0
    for c in candidates:
        if c.github_analysis:
            analyzed += 1
            continue
        data = await analyze_github_profile(c.github_url)
        c.github_analysis = json.dumps(data, default=str)
        analyzed += 1

    await db.commit()
    return {"message": f"Analyzed {analyzed}/{len(candidates)} GitHub profiles"}


@router.post("/{job_id}/evaluate")
async def evaluate_all(job_id: int, db: AsyncSession = Depends(get_db)):
    """Run AI evaluation on all candidates."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Generate dynamic weights based on job description
    weight_result = await generate_dynamic_weights(job.description)
    weights = weight_result["weights"]

    result = await db.execute(select(Candidate).where(Candidate.job_id == job_id))
    candidates = result.scalars().all()

    evaluated = 0
    for c in candidates:
        github_data = json.loads(c.github_analysis) if c.github_analysis else {}
        candidate_info = {
            "name": c.name, "college": c.college, "branch": c.branch,
            "cgpa": c.cgpa, "best_ai_project": c.best_ai_project,
            "research_work": c.research_work,
        }

        # Retry with backoff for rate limiting
        scores = None
        for attempt in range(3):
            scores = await evaluate_candidate(job.description, c.resume_text or "", github_data, candidate_info)
            if scores.get("resume_score", 0) > 0 or "failed" not in scores.get("overall_summary", "").lower():
                break
            await asyncio.sleep(5 * (attempt + 1))

        scores["weight_reasoning"] = weight_result.get("reasoning", "")
        scores["weights_used"] = weights

        c.ai_evaluation = json.dumps(scores, default=str)
        c.resume_score = scores.get("resume_score", 0)
        c.github_score = scores.get("github_score", 0)
        c.jd_match_score = scores.get("jd_match_score", 0)
        c.project_score = scores.get("project_score", 0)
        c.research_score = scores.get("research_score", 0)
        c.ai_score = scores.get("overall_score", 0)
        c.total_score = compute_final_score(scores, c.test_la, c.test_code, weights)
        c.score_breakdown = scores
        c.status = "evaluated"
        evaluated += 1

    await db.commit()
    return {"message": f"Evaluated {evaluated} candidates", "weights": weights, "weight_reasoning": weight_result.get("reasoning", "")}


@router.post("/{job_id}/shortlist")
async def shortlist_candidates(
    job_id: int,
    body: dict = Body(default={"top_n": 5, "min_score": 50}),
    db: AsyncSession = Depends(get_db),
):
    """Shortlist top candidates based on AI scores."""
    top_n = body.get("top_n", 5)
    min_score = body.get("min_score", 50)

    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.total_score.desc())
    )
    candidates = result.scalars().all()

    shortlisted = 0
    for c in candidates:
        if shortlisted < top_n and (c.total_score or 0) >= min_score:
            c.status = "shortlisted"
            shortlisted += 1
        elif c.status == "uploaded" or c.status == "evaluated":
            c.status = "rejected"

    await db.commit()
    return {"message": f"Shortlisted {shortlisted} candidates"}


@router.post("/{job_id}/send-test-links")
async def send_test_links(
    job_id: int,
    body: dict = Body(default={"test_link": "https://example.com/test"}),
    db: AsyncSession = Depends(get_db),
):
    """Send test links to shortlisted candidates."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    test_link = body.get("test_link", "https://example.com/test")
    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id, Candidate.status == "shortlisted")
    )
    candidates = result.scalars().all()

    sent = 0
    for c in candidates:
        success = await send_test_link_email(c.email, c.name, test_link, job.title)
        if success:
            c.email_sent = True
            c.status = "test_sent"
            sent += 1

    await db.commit()
    return {"message": f"Sent test links to {sent} candidates"}


@router.post("/{job_id}/score-tests")
async def score_tests(
    job_id: int,
    body: dict = Body(default={"min_test_score": 60}),
    db: AsyncSession = Depends(get_db),
):
    """Re-score candidates after test results are uploaded."""
    min_test_score = body.get("min_test_score", 60)

    result = await db.execute(
        select(Candidate).where(
            Candidate.job_id == job_id,
            Candidate.status.in_(["shortlisted", "test_sent"]),
        )
    )
    candidates = result.scalars().all()

    scored = 0
    for c in candidates:
        if c.test_la is not None and c.test_code is not None:
            c.test_total = (c.test_la + c.test_code) / 2
            ai_scores = json.loads(c.ai_evaluation) if c.ai_evaluation else {}
            c.final_score = compute_final_score(ai_scores, c.test_la, c.test_code, ai_scores.get("weights_used"))
            c.status = "test_scored" if c.test_total >= min_test_score else "rejected"
            scored += 1

    await db.commit()
    return {"message": f"Scored {scored} candidates with test results"}


@router.post("/{job_id}/schedule-interviews")
async def schedule_interviews(
    job_id: int,
    body: dict = Body(default={"top_n": 5, "start_date": None}),
    db: AsyncSession = Depends(get_db),
):
    """Schedule interviews for top candidates after tests."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    top_n = body.get("top_n", 5)
    start_str = body.get("start_date")
    start_date = datetime.datetime.fromisoformat(start_str) if start_str else datetime.datetime.now() + datetime.timedelta(days=2)

    result = await db.execute(
        select(Candidate).where(
            Candidate.job_id == job_id,
            Candidate.status.in_(["test_scored", "shortlisted", "evaluated"]),
        ).order_by(Candidate.final_score.desc(), Candidate.total_score.desc())
    )
    candidates = result.scalars().all()[:top_n]

    slots = await find_available_slots(start_date, num_slots=len(candidates))

    scheduled = 0
    for i, c in enumerate(candidates):
        if i >= len(slots):
            break
        slot = slots[i]
        cal_result = await schedule_interview(c.name, c.email, job.title, slot)

        c.interview_time = slot
        c.meet_link = cal_result.get("meet_link", "")
        c.status = "interview_scheduled"

        await send_interview_email(c.email, c.name, slot.strftime("%B %d, %Y at %I:%M %p IST"), c.meet_link or "TBD", job.title)
        scheduled += 1

    await db.commit()
    return {"message": f"Scheduled {scheduled} interviews"}


@router.post("/{job_id}/run-full-pipeline")
async def run_full_pipeline(
    job_id: int,
    body: dict = Body(default={"top_n": 5, "min_score": 50, "test_link": "https://example.com/test"}),
    db: AsyncSession = Depends(get_db),
):
    """Run the complete evaluation pipeline (resumes + github + AI eval + shortlist + score tests)."""
    r1 = await process_resumes(job_id, db)
    r2 = await analyze_github(job_id, db)
    r3 = await evaluate_all(job_id, db)
    r4 = await shortlist_candidates(job_id, body, db)
    r5 = await score_tests(job_id, {"min_test_score": body.get("min_test_score", 60)}, db)
    return {"steps": [r1, r2, r3, r4, r5]}
