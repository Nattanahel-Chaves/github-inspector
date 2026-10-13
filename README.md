# GitHub Inspector

## Description

A simple Python CLI tool that retrieves key information from a GitHub repository using the GitHub REST API. Given one or more repository URLs and a Personal Access Token, it returns:

- Repository name, description, language, stars, forks, and default branch
- List of contributors with their contribution count
- GitHub Actions job names (collected from the latest completed run of each workflow)

---

## Prerequisites

- Python 3.10 or higher
- A GitHub Personal Access Token (classic or fine-grained) with the appropriate permissions (see [Token Setup](#token-setup))

---

## Installation

1. Clone this repository and navigate into it:

   ```bash
   git clone <repo-url>
   cd github-inspector
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create your environment file from the provided example:

   ```bash
   cp .env.example .env
   ```

4. Open `.env` and set your token:

   ```env
   GITHUB_TOKEN=your_personal_access_token_here
   ```

---

## How to Run

Pass one or more GitHub repository URLs as arguments:

```bash
python github_inspector.py https://github.com/owner/repo
```

Multiple repositories in one call:

```bash
python github_inspector.py https://github.com/owner/repo1 https://github.com/owner/repo2
```

### Example output

```
============================================================
Inspecting: https://github.com/psf/requests
============================================================

Repo name   : psf/requests
Description : A simple, yet elegant, HTTP library.
Language    : Python
Stars       : 32000
Forks       : 5800
Default branch: main

--- Contributors ---
  kennethreitz (contributions: 2430)
  sigmavirus24 (contributions: 918)
  ...

--- GitHub Actions Job Names ---
  build
  lint
  publish
============================================================
```

---

## Token Setup

### Classic PAT

| Scope | Purpose |
|---|---|
| `repo` | Read repository metadata; required for private repositories |
| `read:user` | Read contributor profile information |
| `workflow` | Read GitHub Actions workflows and job names |

> For public repositories only, `repo` is optional but recommended to avoid hitting unauthenticated rate limits (60 req/hr vs 5,000 req/hr).

---

### Fine-Grained PAT

**Resource owner:** must be set to the **organization** that owns the repository, not your personal account. If the organization has restricted fine-grained token access, an admin must enable it and may need to approve your token before it works.

**Repository permissions:**

| Permission | Access level | Purpose |
|---|---|---|
| `Metadata` | Read-only | Baseline access — automatically included, cannot be removed |
| `Contents` | Read-only | Read repository metadata |
| `Actions` | Read-only | Read workflow definitions and job names |

**Account permissions:** none required — contributor data is covered by the repository `Metadata` permission.

---

## Error Handling & Troubleshooting

The tool processes each URL independently: if one repository fails, the error is printed and it moves on to the next URL. Within a single repository, a failure fetching contributors or workflow jobs is reported in that section only, and the rest of the output is still shown.

### Startup errors

| Message | Cause | Fix |
|---|---|---|
| `Error: GITHUB_TOKEN not set...` | No token found in `.env` or the environment | Copy `.env.example` to `.env` and set `GITHUB_TOKEN` (see [Installation](#installation)) |
| `Usage: python github_inspector.py <github-repo-url> ...` | No repository URL was passed | Pass at least one URL as an argument |

### Invalid URL

```
Error: Invalid GitHub repo URL: <url>
```

Only URLs in the form `https://github.com/<owner>/<repo>` are accepted (a trailing `/` or `.git` is fine). The following are **not** supported:

- SSH URLs: `git@github.com:owner/repo.git`
- Sub-pages: `https://github.com/owner/repo/tree/main`, `.../issues`, etc.
- `www.github.com` or GitHub Enterprise hosts
- Shorthand like `owner/repo`

### GitHub API errors

Errors on the main repository request are printed as:

```
GitHub API error for <url>: <status> Client Error: <reason> for url: <api-url>
```

| Status | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` | Token is invalid, expired, or revoked | Generate a new token and update `.env` |
| `403 Forbidden` | Token lacks the required scopes/permissions | Check the scopes in [Token Setup](#token-setup) |
| `403 Forbidden` | Organization uses SAML SSO and the token isn't authorized for it | On GitHub, go to **Settings → Developer settings → Tokens**, then **Configure SSO → Authorize** for the organization |
| `403 Forbidden` / `429 Too Many Requests` | API rate limit exceeded | Wait for the limit to reset (see below) |
| `404 Not Found` | Repository doesn't exist, URL has a typo, or the repo is private and the token can't access it | Verify the URL; for private repos, confirm the token has access. GitHub returns `404` rather than `403` for private repos you can't see |

> **Fine-grained tokens:** a `404` or `403` on an organization repository usually means the token's **Resource owner** is set to your personal account instead of the organization, or the organization hasn't approved the token yet. See [Fine-Grained PAT](#fine-grained-pat).

### Section-level messages

| Message | Meaning |
|---|---|
| `Could not fetch contributors: ...` | The contributors request failed (for example, missing permissions, or the repository has too much history for GitHub to list contributors). Repo info and jobs are still shown |
| `(none found or repo is empty)` | The request succeeded but returned no contributors |
| `Could not fetch workflow jobs: ...` | Listing the repository's workflows failed, typically because the token lacks the `workflow` scope (classic) or `Actions: Read` permission (fine-grained) |
| `(no workflow runs found)` | The repo has no workflows, GitHub Actions is disabled, or no workflow has a **completed** run yet |

Job names come from the **latest completed run** of each workflow. If fetching runs or jobs for a single workflow fails, that workflow is skipped silently, so the job list may be incomplete rather than showing an error.

### Rate limits

Each repository uses roughly `3 + (2 × number of workflows)` API requests, plus one per extra page of contributors. Authenticated tokens get 5,000 requests per hour. To check your remaining quota:

```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```

### Network errors

Connection problems (no internet, proxy, DNS, or TLS issues) are not caught by the tool and will stop it with a Python traceback. Check your connection and any proxy settings (`HTTPS_PROXY`), then try again.
