import requests
import json
import time
import os

def get_public_repos(username):
    response = requests.get(f"https://api.github.com/users/{username}/repos")
    if response.status_code == 200:
        repos = [repo['full_name'] for repo in response.json()]
        return repos
    else:
        print("Failed to fetch public repositories. Status code:", response.status_code)
        return []

def get_stargazers(repo_owner, repo_name, token):
    headers = {"Authorization": f"Bearer {token}"}
    stargazers = []

    # Initial cursor for pagination
    cursor = None
    while True:
        # GraphQL query for stargazers with pagination
        query = """
        query {
          repository(owner:"%s", name:"%s") {
            stargazers(first: 100, after: %s) {
              pageInfo {
                endCursor
                hasNextPage
              }
              edges {
                node {
                  login
                }
              }
            }
          }
        }
        """ % (repo_owner, repo_name, f'"{cursor}"' if cursor else "null")

        response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)

        if response.status_code != 200:
            print("Failed to fetch stargazers. Status code:", response.status_code)
            return []

        data = response.json()
        edges = data['data']['repository']['stargazers']['edges']
        for edge in edges:
            stargazers.append(edge['node']['login'])

        hasNextPage = data['data']['repository']['stargazers']['pageInfo']['hasNextPage']
        if not hasNextPage:
            break
        
        cursor = data['data']['repository']['stargazers']['pageInfo']['endCursor']

    return stargazers


def save_stargazers(stargazers, filename):
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    with open(filename, 'w') as file:
        json.dump(stargazers, file)

def load_stargazers(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def compare_stargazers(old_stargazers, new_stargazers):
    new_users = set(new_stargazers) - set(old_stargazers)
    missing_users = set(old_stargazers) - set(new_stargazers)
    return new_users, missing_users

def send_webhook(embed_data):
    webhook_url = "YOUR_WEBHOOK"
    response = requests.post(webhook_url, json=embed_data)
    if response.status_code != 204:
        print("Failed to send webhook. Status code:", response.status_code)

def check_stargazers(username, token, stargazers_filename):
    repos = get_public_repos(username)
    if not repos:
        print("No public repositories found for the user.")
        return
    
    for repo in repos:
        owner, name = repo.split('/')
        new_stargazers = get_stargazers(owner, name, token)
        old_stargazers = load_stargazers(stargazers_filename.format(repo))
        
        if new_stargazers:
            save_stargazers(new_stargazers, stargazers_filename.format(repo))

            new_users, missing_users = compare_stargazers(old_stargazers, new_stargazers)
            total_users = len(new_stargazers)

            if new_users or missing_users:
                print("Repo:", repo)
                print("New users:", new_users)
                print("Missing users:", missing_users)
                print("Total users:", total_users)
                
                # Sending webhook embed
                embed_data = {
                    "content": "Stargazers Update",
                    "embeds": [{
                        "title": f"Stargazers Update - {repo}",
                        "fields": [
                            {"name": "New Users", "value": ", ".join(new_users) if new_users else "None"},
                            {"name": "Missing Users", "value": ", ".join(missing_users) if missing_users else "None"},
                            {"name": "Total Users", "value": total_users}
                        ],
                        "color": 16776960  # Yellow color
                    }]
                }
                send_webhook(embed_data)

if __name__ == "__main__":
    username = "YOUR_GITHUB_USERNAME"
    token = "GITHUB_ACCESS_TOKEN"
    stargazers_filename = "{}_stargazers.json"

    # Initial check
    check_stargazers(username, token, stargazers_filename)

    # Check stargazers every 30 minutes
    while True:
        time.sleep(1800)  # 30 minutes in seconds
        check_stargazers(username, token, stargazers_filename)