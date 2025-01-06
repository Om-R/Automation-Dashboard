import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# JIRA Configurations
JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_USER = "automation.user@lendingkart.com"
JIRA_API_TOKEN="ATATT3xFfGF07jnnP2h7-tWWI1sV-ZPums3kvejb1zV4d8eCwrbXhY-MTLIQDv5rkCcOt6GU3o8BK03lBKB9kiUT8zZIu3JlZggC8yQwfpA_e-pfuHhCMX6yTv55KowjGhX8nMyYYzpSlpgILo0HNrTk4Rg2Fqto0EwJOUKeNDSrB2Um9wbua8Y=097D1ED1"
JIRA_AUTH = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_STATUS = "Approval Required"
SMTP_USER="automation.user@lendingkart.com"
SMTP_PASSWORD="eehi jeqo tskb dbwb"


logging.basicConfig(
    filename='access_granting.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



# Fetch JIRA issues
def get_jira_issues():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" AND status="{JIRA_STATUS}" ORDER BY created DESC'
    }

    try:
        logging.info(f"Sending GET request to {JIRA_URL} with query: {query['jql']}")
        response = requests.get(
            JIRA_URL,
            headers={"Content-Type": "application/json"},
            auth=JIRA_AUTH,
            params=query
        )
        print(response)
        logging.info(f"Response Status Code: {response.status_code}")
        response.raise_for_status()

        issues = response.json()
        logging.info(f"Fetched {len(issues.get('issues', []))} issues from JIRA")
        print(issues)

        with open('users_data.json', 'w') as file:
            json.dump(issues, file, indent=4)

        logging.info("JIRA issues written to output.json")
        return issues.get('issues', [])

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch JIRA issues: {e}")
        return []

# Main script logic
def main():
    logging.info("Starting access automation script")
    issues = get_jira_issues()

    if not issues:
        logging.info("No issues found.")
        return

    logging.info(f"Fetched {len(issues)} issues from JIRA.")
    # You can add additional processing logic here if needed for the fetched issues

    logging.info("Access automation script completed")

if __name__ == "__main__":
    main()
