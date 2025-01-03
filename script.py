import json
import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

# JIRA API URLs and authentication
JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_AUTH = HTTPBasicAuth(os.getenv("JIRA_USER"), os.getenv("JIRA_API_TOKEN"))

JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_REQUEST_TYPE = "Dashboard Access"  ###Ask ankur for the type
JIRA_STATUS = "Approval Required"
JIRA_TRANSITION_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/transitions"
JIRA_COMMENT_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/comment"

ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = SMTP_USER
EMAIL_SUBJECT = "Your Dashboard Access Credentials"

CONSTANT_PASSWORD = "Lendingkart@321"

logging.basicConfig(
    filename='access_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if not all([SMTP_USER, SMTP_PASS, JIRA_AUTH.username, JIRA_AUTH.password]):
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


# Function to write user data to a JSON file
def write_user_data_to_json(user_data):
    try:
        # Load existing data
        if os.path.exists('users_data.json'):
            with open('users_data.json', 'r') as file:
                data = json.load(file)
        else:
            data = []

        # Append the new user data
        data.append(user_data)

        with open('users_data.json', 'w') as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        logging.error(f"Failed to write user data to JSON: {e}")


def main():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" and "Request Type" = "{JIRA_REQUEST_TYPE}" and status = "{JIRA_STATUS}" order by created DESC',
        'fields': 'customfield_12305,customfield_12420,customfield_12477,customfield_12313,customfield_12334'
    }

    try:
        logging.info(f"Sending GET request to {JIRA_URL}")
        logging.info(f"Request Headers: {JIRA_AUTH}")
        logging.info(f"Request Params: {query}")

        response = requests.request(
            "GET",
            JIRA_URL,
            auth=JIRA_AUTH,
            params={'jql': query['jql']}
        )

        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Text: {response.text}")

        response.raise_for_status()

        issues = json.loads(response.text)

        for issue in issues.get('issues', []):
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

            password = CONSTANT_PASSWORD

            logging.info(f"Processing user: {name}, Email: {email}, Password: {password}, Role: {role_name}")

            try:
                add_user_response = requests.post(
                    ADD_USER_URL,
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({
                        "contactNo": mobile,
                        "email": os.environ.get('SMTP_USER'),
                        "name": name,
                        "password": os.environ.get('SMTP_PASS'),
                        "roleName": role_name
                    })
                )
                add_user_response.raise_for_status()

                if add_user_response.status_code == 201:
                    logging.info(f"User {name} has been added successfully.")

                    # Write user data to JSON
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
                                    data=json.dumps({"transition": {"id": "761"}})  ##ask to ankur for id to know whether it resolved or not
                                )
                                transition_response.raise_for_status()

                                if transition_response.status_code == 204:
                                    logging.info(f"Issue {issue_key} transitioned to 'Resolved'.")
                                    # Send email with credentials to user
                                    send_email("om.jain@lendingkart.com", password)  # Set receiver to test email
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
