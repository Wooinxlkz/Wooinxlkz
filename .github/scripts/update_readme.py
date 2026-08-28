import os
import re
import requests

USERNAME = os.environ.get("USERNAME", "Wooinxlkz")
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

# Repos to check for latest releases (edit this list as your project lineup changes)
RELEASE_REPOS = [
    "Speusis-Downloader",
    "glyf",
    "kinetic",
    "fine-print-guardian",
    "NutriLLM",
    "athlete-core",
    "solair-core",
    "UnderCtrl",
    "Tokka",
]

README_PATH = "README.md"


def get_user():
    r = requests.get(f"https://api.github.com/users/{USERNAME}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def get_all_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_latest_release(repo):
    r = requests.get(
        f"https://api.github.com/repos/{USERNAME}/{repo}/releases/latest",
        headers=HEADERS,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    return {
        "repo": repo,
        "name": data.get("name") or data.get("tag_name", ""),
        "url": data.get("html_url", ""),
        "date": (data.get("published_at") or "")[:10],
    }


def build_stats_line(user, repos):
    non_fork = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in non_fork)
    forks = sum(r.get("forks_count", 0) for r in non_fork)
    followers = user.get("followers", 0)
    return f"{followers:,} followers, {stars:,} stars, {forks:,} forks"


def build_releases_block():
    releases = []
    for repo in RELEASE_REPOS:
        rel = get_latest_release(repo)
        if rel and rel["date"]:
            releases.append(rel)
    releases.sort(key=lambda r: r["date"], reverse=True)
    releases = releases[:6]
    if not releases:
        return "No releases yet."
    return "<br>".join(
        f"• [{r['repo']} {r['name']}]({r['url']}) - {r['date']}" for r in releases
    )


def replace_between(content, marker, new_value):
    start = f"<!-- {marker} starts -->"
    end = f"<!-- {marker} ends -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pattern.sub(f"{start}{new_value}{end}", content)


def main():
    user = get_user()
    repos = get_all_repos()

    stats_line = build_stats_line(user, repos)
    releases_block = build_releases_block()

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = replace_between(content, "github_stats", stats_line)
    content = replace_between(content, "recent_releases", releases_block)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
