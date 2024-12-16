import os

import requests
import json
import random
import string
import time
import logging
from requests.auth import HTTPBasicAuth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_AUTH = HTTPBasicAuth(os.getenv("JIRA_USER"), os.getenv("JIRA_API_TOKEN"))
JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_REQUEST_TYPE = "Dashboard access (TH)"
JIRA_STATUS = "In Progress"
JIRA_TRANSITION_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/transitions"
JIRA_COMMENT_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/comment"
ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = SMTP_USER
EMAIL_SUBJECT = "Your Dashboard Access Credentials"

logging.basicConfig(filename='access_granting.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

if not all([SMTP_USER, SMTP_PASS, JIRA_AUTH.username, JIRA_AUTH.password]):
    raise EnvironmentError("Required environment variables are not set.")


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


def send_email(to_email, password):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = EMAIL_SUBJECT

    body = f"""Your dashboard access has been granted.\n\nEmail: {to_email},\nPassword: {password}"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}.")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")


def main():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" and "Request Type" = "{JIRA_REQUEST_TYPE}" and status = "{JIRA_STATUS}" order by created DESC',
        'fields': 'customfield_12305,customfield_12420,customfield_12477,customfield_12313,customfield_12334'
    }

    try:
        response = requests.get(JIRA_URL, auth=JIRA_AUTH, params={'jql': query['jql']})
        response.raise_for_status()
        issues = response.json().get('issues', [])

        for issue in issues:
            issue_key = issue['key']
            fields = issue['fields']
            name = fields.get('customfield_12305')
            email = fields.get('customfield_12420')
            mobile = fields.get('customfield_12477')
            dashboard_name = fields.get('customfield_12313')
            role_name = fields.get('customfield_12334')

            if not (name and email and role_name):
                logging.warning(f"Missing required fields for issue {issue_key}. Skipping...")
                continue

            password = generate_random_password()

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
                            time.sleep(10)  ### Delay before transitioning status

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

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()