import json
import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from requests.auth import HTTPBasicAuth

# from dotenv import load_dotenv

# load_dotenv()
#providong access use tse user and try to incooprate it using curl which ankur provided
JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_USER = "automation.user@lendingkart.com"
JIRA_API_TOKEN = "ATATT3xFfGF07jnnP2h7-tWWI1sV-ZPums3kvejb1zV4d8eCwrbXhY-MTLIQDv5rkCcOt6GU3o8BK03lBKB9kiUT8zZIu3JlZggC8yQwfpA_e-pfuHhCMX6yTv55KowjGhX8nMyYYzpSlpgILo0HNrTk4Rg2Fqto0EwJOUKeNDSrB2Um9wbua8Y=097D1ED1"
JIRA_AUTH = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_REQUEST_TYPE = "Test"
JIRA_STATUS = "Approval Required"
JIRA_TRANSITION_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/transitions"
JIRA_COMMENT_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/comment"
ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "automation.user@lendingkart.com"
SMTP_PASS = "eehi jeqo tskb dbwb"
FROM_EMAIL = SMTP_USER
EMAIL_SUBJECT = "Your Dashboard Access Credentials"
CONSTANT_PASSWORD = "Lendingkart@321"

logging.basicConfig(
    filename='access_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if not all([SMTP_USER, SMTP_PASS]):
    raise EnvironmentError("Required environment variables are not set.")


# Send email notification to user
def send_email(to_email, password):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = EMAIL_SUBJECT

    body = f"""Your dashboard access has been granted.\n\nEmail: {to_email},\nPassword: {password}"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}.")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")


# Write user data to JSON file
def write_user_data_to_json(user_data):
    try:
        if os.path.exists('users_data.json'):
            with open('users_data.json', 'r') as file:
                data = json.load(file)
        else:
            data = []

        data.append(user_data)

        with open('user_data.json', 'w') as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        logging.error(f"Failed to write user data to JSON: {e}")


def get_jira_issues():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" AND "Request Type" = "{JIRA_REQUEST_TYPE}" AND status="{JIRA_STATUS}" ORDER BY created DESC',
        'fields': 'customfield_12528,customfield_12420,customfield_12477,customfield_12529,customfield_12529'
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

        with open('user_data.json', 'w') as file:
            json.dump(issues, file, indent=4)

        logging.info("JIRA issues written to output.json")
        return issues.get('issues', [])

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch JIRA issues: {e}")
        return []


# Process user details and update JIRA
def process_user(issue):
    issue_key = issue['key']
    fields = issue['fields']

    # Extracting the custom fields
    name = fields.get('customfield_12528')
    email = fields.get('customfield_12420')
    mobile = fields.get('customfield_12477')
    # dashboard_name = fields.get('customfield_12529')
    role_name = fields.get('customfield_12529')

    if not (name and email and role_name):
        logging.warning(f"Missing required fields for issue {issue_key}. Skipping...")
        return

    password = CONSTANT_PASSWORD
    logging.info(f"Processing user: {name}, Email: {email}, Password: {password}, Role: {role_name}")

    try:
        add_user_response = requests.post(
            ADD_USER_URL,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                "contactNo": mobile,
                "email": email,
                "name": name,
                "password": password,
                "roleName": role_name
            })
        )
        add_user_response.raise_for_status()

        if add_user_response.status_code == 201:
            logging.info(f"User {name} added successfully.")
            user_data = {
                "name": name,
                "email": email,
                "contactNo": mobile,
                "role": role_name,
                "password": password
            }
            write_user_data_to_json(user_data)

            try:
                comment_response = requests.post(
                    JIRA_COMMENT_URL.format(issue_key=issue_key),
                    auth=JIRA_AUTH,
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({"body": "Access has been granted."})
                )
                comment_response.raise_for_status()

                if comment_response.status_code == 201:
                    logging.info(f"Comment added to issue {issue_key}.")
                    time.sleep(10)

                    try:
                        transition_response = requests.post(
                            JIRA_TRANSITION_URL.format(issue_key=issue_key),
                            auth=JIRA_AUTH,
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps({"transition": {"id": "761"}})
                        )
                        transition_response.raise_for_status()

                        if transition_response.status_code == 204:
                            logging.info(f"Issue {issue_key} transitioned to 'Resolved'.")
                            send_email(email, password)
                        else:
                            logging.error(
                                f"Failed to transition issue {issue_key}. Status code: {transition_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"Failed to transition issue {issue_key}: {e}")
                else:
                    logging.error(
                        f"Failed to add comment to issue {issue_key}. Status code: {comment_response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to add comment to issue {issue_key}: {e}")
        else:
            logging.error(f"Failed to add user {name}. Status code: {add_user_response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to add user {name}: {e}")


def main():
    logging.info("Starting access automation script")

    issues = get_jira_issues()

    if not issues:
        logging.info("No issues found.")
        return

    for issue in issues:
        process_user(issue)

    logging.info("Access automation script completed")


if __name__ == "__main__":
    main()
