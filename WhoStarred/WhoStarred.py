import requests
import json
from datetime import datetime

def get_user_repositories(username, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repositories = response.json()
        return [repo['full_name'] for repo in repositories if not repo['private']]
    else:
        print("Failed to fetch user repositories. Status code:", response.status_code)
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
    with open(filename, 'w') as file:
        json.dump(stargazers, file)

def load_stargazers(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def compare_stargazers(old_stargazers, new_stargazers):
    new_users = set(new_stargazers) - set(old_stargazers)
    missing_users = set(old_stargazers) - set(new_stargazers)
    return new_users, missing_users

def save_report(repo_name, new_users, missing_users, total_users):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"report_{timestamp}.log"
    with open(report_filename, 'a') as file:
        file.write(f"Report Timestamp: {timestamp}\n")
        file.write(f"Repository: {repo_name}\n")
        file.write("\nTotal users: {}\n".format(total_users))
        file.write("New users:\n")
        for user in new_users:
            file.write(user + '\n')
        file.write("\nMissing users:\n")
        for user in missing_users:
            file.write(user + '\n')
        file.write("=================================\n\n")
    print("Report saved as:", report_filename)

if __name__ == "__main__":
    username = "YOUR_GITHUB_USERNAME"
    token = "GITHUB_ACCESS_TOKEN"  # Replace with your personal access token
    stargazers_filename = "stargazers.json"

    repositories = get_user_repositories(username, token)
    if repositories:
        all_stargazers = {}
        for repo in repositories:
            repo_owner, repo_name = repo.split('/')
            new_stargazers = get_stargazers(repo_owner, repo_name, token)
            if new_stargazers:
                all_stargazers[repo] = new_stargazers
                print(f"Fetched stargazers for {repo}: {len(new_stargazers)}")

        save_stargazers(all_stargazers, stargazers_filename)

        old_stargazers = load_stargazers(stargazers_filename)
        if old_stargazers:
            for repo, new_stargazers in all_stargazers.items():
                if repo in old_stargazers:
                    old_stargazers_for_repo = old_stargazers[repo]
                    new_users, missing_users = compare_stargazers(old_stargazers_for_repo, new_stargazers)
                    total_users = len(new_stargazers)
                    save_report(repo, new_users, missing_users, total_users)
        else:
            print("No previous stargazers found.")
    else:
        print("No public repositories found for the user.")