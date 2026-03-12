import os
import httpx


async def analyze_github_profile(github_url: str) -> dict:
    """Fetch and analyze a GitHub profile's public repositories."""
    if not github_url or str(github_url).lower() == "nan":
        return {"error": "No GitHub URL provided", "repos": [], "summary": "No GitHub profile available."}

    username = github_url.rstrip("/").split("/")[-1]
    headers = {"Accept": "application/vnd.github.v3+json"}
    gh_token = os.getenv("GITHUB_TOKEN", "")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(f"https://api.github.com/users/{username}/repos",
                                    headers=headers, params={"sort": "updated", "per_page": 30})
            if resp.status_code == 403:
                return {"error": "GitHub rate limited", "repos": [], "username": username,
                        "summary": f"GitHub profile exists ({username}) but rate limited."}
            if resp.status_code != 200:
                return {"error": f"GitHub user not found: {username}", "repos": [], "summary": "GitHub profile not accessible."}
            repos = resp.json()
        except Exception as e:
            return {"error": str(e), "repos": [], "summary": "Failed to fetch GitHub data."}

    repo_details = []
    for repo in repos:
        if repo.get("fork"):
            continue
        repo_details.append({
            "name": repo.get("name", ""),
            "description": repo.get("description", ""),
            "language": repo.get("language", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at", ""),
            "size": repo.get("size", 0),
        })

    return {
        "username": username,
        "repos_analyzed": len(repo_details),
        "repos": repo_details,
        "total_stars": sum(r["stars"] for r in repo_details),
        "languages_used": list(set(r["language"] for r in repo_details if r["language"])),
    }
