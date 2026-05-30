import httpx
import base64
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def fetch_user_repos(username: str, limit: int = 5):
    """Fetch public repositories for a given user."""
    url = f"https://api.github.com/users/{username}/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
            params={"sort": "updated", "per_page": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

async def fetch_repo_file_listing(owner: str, repo: str):
    """Fetch the root directory file listing of a repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
    except Exception:
        return []

def is_dependency_file(filename: str) -> bool:
    """Check if a file looks like it declares dependencies or config."""
    name = filename.lower()
    indicators = [
        'package.json', 'requirements', 'gemfile', 'cargo.toml', 
        'go.mod', 'build.gradle', 'pom.xml', 'dockerfile',
        'composer.json', 'mix.exs', 'pipfile', 'tox.ini',
        '.yml', '.yaml', 'config', 'setup.py', 'pyproject.toml'
    ]
    return any(ind in name for ind in indicators) or 'readme' in name

async def fetch_file_content(download_url: str):
    """Fetch the raw text content of a file."""
    if not download_url:
        return ""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, timeout=10)
            if response.status_code == 200:
                return response.text
            return ""
    except Exception:
        return ""

async def analyze_user_github_context(username: str):
    """Collect all dependency and readme contexts across top repos."""
    repos = await fetch_user_repos(username)
    
    collected_context = ""
    
    for repo in repos:
        repo_name = repo['name']
        collected_context += f"\\n--- Repository: {repo_name} ---\\n"
        
        # Add primary language info
        if repo.get('language'):
            collected_context += f"Primary Language: {repo['language']}\\n"
            
        files = await fetch_repo_file_listing(username, repo_name)
        
        for file in files:
            if file['type'] == 'file' and is_dependency_file(file['name']):
                content = await fetch_file_content(file['download_url'])
                if content:
                    # Truncate content to avoid blowing up context window
                    content = content[:2000] 
                    collected_context += f"\\nFile: {file['name']}\\n{content}\\n"
                    
    return collected_context
