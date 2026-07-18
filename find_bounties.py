import requests
import json

# GitHub API to find issues labeled as bounties
url = "https://api.github.com/search/issues?q=label:bounty+state:open+language:python&sort=created&order=desc"

headers = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Hy3-Agent'
}

print("Scanning GitHub for Open Crypto Bounties...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    bounties = data.get('items', [])
    
    print(f"\nFound {len(bounties)} open bounties. Top 5 targets:\n")
    
    for i, issue in enumerate(bounties[:5]):
        title = issue.get('title')
        repo = issue.get('repository_url').split('/')[-1]
        url = issue.get('html_url')
        print(f"{i+1}. [Repo: {repo}] {title}")
        print(f"   Link: {url}\n")
else:
    print(f"Error: {response.status_code}")