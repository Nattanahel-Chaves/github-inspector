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
