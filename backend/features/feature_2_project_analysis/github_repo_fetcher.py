import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def fetch_repo_metadata(owner: str, repo: str):
    """Fetch basic repository metadata and languages."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    async with httpx.AsyncClient() as client:
        # Repo info
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return None
        repo_data = response.json()
        
        # Languages
        lang_res = await client.get(f"{url}/languages", headers=headers)
        languages = lang_res.json() if lang_res.status_code == 200 else {}
        
        # Check files for contributor environment
        files_to_check = ['CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', '.github/ISSUE_TEMPLATE', '.github/PULL_REQUEST_TEMPLATE']
        env_status = {
            "has_contributing": False,
            "has_code_of_conduct": False,
            "has_issue_template": False,
            "has_pr_template": False
        }
        
        # Fetch root contents to check existence roughly (or use specific path requests)
        for file_path in files_to_check:
            file_res = await client.get(f"{url}/contents/{file_path}", headers=headers)
            if file_res.status_code == 200:
                if 'CONTRIBUTING' in file_path: env_status['has_contributing'] = True
                if 'CODE_OF_CONDUCT' in file_path: env_status['has_code_of_conduct'] = True
                if 'ISSUE_TEMPLATE' in file_path: env_status['has_issue_template'] = True
                if 'PULL_REQUEST_TEMPLATE' in file_path: env_status['has_pr_template'] = True
        
        # Fetch readme context for Gemini
        readme_res = await client.get(f"{url}/readme", headers=headers)
        readme_content = ""
        if readme_res.status_code == 200:
            import base64
            readme_data = readme_res.json()
            if 'content' in readme_data:
                try:
                    readme_content = base64.b64decode(readme_data['content']).decode('utf-8')[:3000] # truncate
                except:
                    pass

        return {
            "metadata": repo_data,
            "languages": languages,
            "contributor_env": env_status,
            "readme": readme_content
        }
