import os
import re
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Headless AI SWE API")

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_KEY", "")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


class FixRequest(BaseModel):
    issue_url: str


class FixResponse(BaseModel):
    fix: str


def parse_issue_url(url: str) -> tuple[str, str, str]:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid GitHub issue URL")
    return m.group(1), m.group(2), m.group(3)


@app.post("/fix-issue", response_model=FixResponse)
async def fix_issue(req: FixRequest):
    owner, repo, issue_number = parse_issue_url(req.issue_url)

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"

    gh_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"

    async with httpx.AsyncClient() as client:
        gh_resp = await client.get(gh_url, headers=headers, timeout=15)
        if gh_resp.status_code != 200:
            detail = gh_resp.json().get("message", "GitHub API error")
            raise HTTPException(status_code=gh_resp.status_code, detail=detail)

        issue = gh_resp.json()
        title = issue.get("title", "")
        body = issue.get("body", "")

    if not GROQ_KEY:
        raise HTTPException(status_code=500, detail="GROQ_KEY not configured")

    prompt = (
        f"You are an expert developer. Write the code to fix this issue: "
        f"{title} - {body}"
    )

    groq_payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient() as client:
        groq_resp = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json=groq_payload,
            timeout=60,
        )
        if groq_resp.status_code != 200:
            detail = groq_resp.json().get("error", {}).get("message", "Groq API error")
            raise HTTPException(status_code=502, detail=detail)

        result = groq_resp.json()
        code = result["choices"][0]["message"]["content"]

    return FixResponse(fix=code)
