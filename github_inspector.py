import os
import sys
import re
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    url = url.rstrip("/")
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        raise ValueError(f"Invalid GitHub repo URL: {url}")
    return match.group(1), match.group(2)


def make_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return session


def get_repo_info(session: requests.Session, owner: str, repo: str) -> dict:
    resp = session.get(f"https://api.github.com/repos/{owner}/{repo}")
    resp.raise_for_status()
    return resp.json()


def get_contributors(session: requests.Session, owner: str, repo: str) -> list[dict]:
    users = []
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    while url:
        resp = session.get(url, params={"per_page": 100, "anon": "false"})
        resp.raise_for_status()
        users.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
    return users


def get_workflow_jobs(session: requests.Session, owner: str, repo: str) -> list[str]:
    """Return unique job names from all workflow definitions in the repo."""
    workflows_resp = session.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows",
        params={"per_page": 100},
    )
    workflows_resp.raise_for_status()
    workflows = workflows_resp.json().get("workflows", [])

    job_names: set[str] = set()
    for wf in workflows:
        runs_resp = session.get(
            f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{wf['id']}/runs",
            params={"per_page": 1, "status": "completed"},
        )
        if runs_resp.status_code != 200:
            continue
        runs = runs_resp.json().get("workflow_runs", [])
        if not runs:
            continue
        run_id = runs[0]["id"]
        jobs_resp = session.get(
            f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            params={"per_page": 100},
        )
        if jobs_resp.status_code != 200:
            continue
        for job in jobs_resp.json().get("jobs", []):
            job_names.add(job["name"])

    return sorted(job_names)


def inspect(repo_url: str, token: str) -> None:
    owner, repo_name = parse_repo_url(repo_url)
    session = make_session(token)

    print(f"\n{'='*60}")
    print(f"Inspecting: {repo_url}")
    print(f"{'='*60}")

    # Repo info
    info = get_repo_info(session, owner, repo_name)
    print(f"\nRepo name   : {info['full_name']}")
    print(f"Description : {info.get('description') or '—'}")
    print(f"Language    : {info.get('language') or '—'}")
    print(f"Stars       : {info['stargazers_count']}")
    print(f"Forks       : {info['forks_count']}")
    print(f"Default branch: {info['default_branch']}")

    # Contributors
    print(f"\n--- Contributors ---")
    try:
        users = get_contributors(session, owner, repo_name)
        if users:
            for u in users:
                print(f"  {u['login']} (contributions: {u['contributions']})")
        else:
            print("  (none found or repo is empty)")
    except requests.HTTPError as e:
        print(f"  Could not fetch contributors: {e}")

    # Workflow jobs
    print(f"\n--- GitHub Actions Job Names ---")
    try:
        jobs = get_workflow_jobs(session, owner, repo_name)
        if jobs:
            for j in jobs:
                print(f"  {j}")
        else:
            print("  (no workflow runs found)")
    except requests.HTTPError as e:
        print(f"  Could not fetch workflow jobs: {e}")

    print(f"\n{'='*60}\n")


def main() -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python github_inspector.py <github-repo-url> [url2 ...]")
        print("Example: python github_inspector.py https://github.com/psf/requests")
        sys.exit(1)

    for url in sys.argv[1:]:
        try:
            inspect(url, token)
        except ValueError as e:
            print(f"Error: {e}")
        except requests.HTTPError as e:
            print(f"GitHub API error for {url}: {e}")


if __name__ == "__main__":
    main()
