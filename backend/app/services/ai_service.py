import json
import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq" if GROQ_API_KEY else "ollama")
GROQ_MODEL = "llama-3.1-8b-instant"
OLLAMA_MODEL = "llama3.2"


async def _call_groq(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.3, "max_tokens": 1024, "response_format": {"type": "json_object"}},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1024},
        })
        resp.raise_for_status()
        return resp.json()["response"]


async def _call_llm(prompt: str) -> str:
    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        return await _call_groq(prompt)
    return await _call_ollama(prompt)


async def evaluate_candidate(
    job_description: str, resume_text: str, github_data: dict, candidate_info: dict,
) -> dict:
    prompt = f"""You are an expert technical recruiter AI. Evaluate this candidate against the job description.

## Job Description
{job_description[:1500]}

## Candidate Info
- Name: {candidate_info.get('name', 'N/A')}
- College: {candidate_info.get('college', 'N/A')}
- Branch: {candidate_info.get('branch', 'N/A')}
- CGPA: {candidate_info.get('cgpa', 'N/A')}
- Best AI Project: {(candidate_info.get('best_ai_project') or 'N/A')[:500]}
- Research Work: {(candidate_info.get('research_work') or 'N/A')[:500]}

## Resume Content (excerpt)
{resume_text[:2000] if resume_text else 'No resume available'}

## GitHub Profile Summary
- Repos: {github_data.get('public_repos', 0)}
- Stars: {github_data.get('total_stars', 0)}
- Languages: {github_data.get('languages_used', [])}
- Top repos: {json.dumps([r.get('name','') for r in github_data.get('repos', [])[:5]], default=str)}

## Task
Score the candidate on each dimension from 0 to 100. Return ONLY valid JSON:
{{"resume_score": <0-100>, "resume_reasoning": "<one sentence>", "github_score": <0-100>, "github_reasoning": "<one sentence>", "jd_match_score": <0-100>, "jd_match_reasoning": "<one sentence>", "project_score": <0-100>, "project_reasoning": "<one sentence>", "research_score": <0-100>, "research_reasoning": "<one sentence>", "overall_score": <0-100>, "overall_summary": "<two sentences>", "strengths": ["<s1>", "<s2>"], "weaknesses": ["<w1>", "<w2>"], "recommendation": "<strong_yes|yes|maybe|no>"}}"""

    try:
        raw = await _call_llm(prompt)
        result = _extract_json(raw)
        for key in ["resume_score", "github_score", "jd_match_score", "project_score", "research_score", "overall_score"]:
            if key not in result or not isinstance(result[key], (int, float)):
                result[key] = 0
        for key in ["resume_reasoning", "github_reasoning", "jd_match_reasoning", "project_reasoning", "research_reasoning"]:
            result.setdefault(key, "")
        result.setdefault("overall_summary", "")
        result.setdefault("strengths", [])
        result.setdefault("weaknesses", [])
        result.setdefault("recommendation", "maybe")
        return result
    except Exception as e:
        return _error_result(f"Evaluation failed: {str(e)}")


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    import re
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find('{')
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{': depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break
    return _error_result("Could not parse LLM response")


def _error_result(msg: str) -> dict:
    return {
        "resume_score": 0, "github_score": 0, "jd_match_score": 0,
        "project_score": 0, "research_score": 0, "overall_score": 0,
        "overall_summary": msg, "strengths": [], "weaknesses": [],
        "recommendation": "no", "resume_reasoning": "", "github_reasoning": "",
        "jd_match_reasoning": "", "project_reasoning": "", "research_reasoning": "",
    }


async def generate_dynamic_weights(job_description: str) -> dict:
    """Ask the LLM to determine scoring weights based on the job description."""
    prompt = f"""Given this job description, determine the relative importance of each evaluation dimension.
Return ONLY valid JSON with weights that sum to 1.0:

Job Description: {job_description[:800]}

{{"resume_score": <0.0-1.0>, "github_score": <0.0-1.0>, "jd_match_score": <0.0-1.0>, "project_score": <0.0-1.0>, "research_score": <0.0-1.0>, "reasoning": "<one sentence explaining weight choices>"}}"""
    try:
        raw = await _call_llm(prompt)
        result = _extract_json(raw)
        keys = ["resume_score", "github_score", "jd_match_score", "project_score", "research_score"]
        weights = {k: float(result.get(k, 0.2)) for k in keys}
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}  # normalize to 1.0
        return {"weights": weights, "reasoning": result.get("reasoning", "")}
    except Exception:
        return {"weights": DEFAULT_WEIGHTS, "reasoning": "Using default weights (LLM weight generation failed)"}


DEFAULT_WEIGHTS = {"resume_score": 0.15, "github_score": 0.15, "jd_match_score": 0.20, "project_score": 0.15, "research_score": 0.10}


def compute_final_score(ai_scores: dict, test_la: float = None, test_code: float = None, weights: dict = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    ai_total = sum(ai_scores.get(k, 0) * w.get(k, 0) for k in DEFAULT_WEIGHTS)
    w_sum = sum(w.get(k, 0) for k in DEFAULT_WEIGHTS)
    if test_la is not None and test_code is not None:
        test_score = (test_la + test_code) / 2
        return (ai_total / w_sum * 0.75) + (test_score * 0.25) if w_sum > 0 else test_score
    return ai_total / w_sum if w_sum > 0 else 0
