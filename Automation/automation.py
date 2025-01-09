# import json
# import logging
# import os
# import smtplib
# import time
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import requests
# from requests.auth import HTTPBasicAuth
# # from dotenv import load_dotenv
#
# # load_dotenv()
#
# JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
# JIRA_USER = "automation.user@lendingkart.com"   # Super admin took jsession id to give access
# JIRA_API_TOKEN = "ATATT3xFfGF07jnnP2h7-tWWI1sV-ZPums3kvejb1zV4d8eCwrbXhY-MTLIQDv5rkCcOt6GU3o8BK03lBKB9kiUT8zZIu3JlZggC8yQwfpA_e-pfuHhCMX6yTv55KowjGhX8nMyYYzpSlpgILo0HNrTk4Rg2Fqto0EwJOUKeNDSrB2Um9wbua8Y=097D1ED1"
# JIRA_AUTH = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
# JIRA_PROJECT_KEY = "Tools Helpdesk"
# JIRA_REQUEST_TYPE = "Dashboard Access"   # Verify this
# JIRA_STATUS = "Approval Required"
# JIRA_TRANSITION_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/transitions"
# JIRA_COMMENT_URL = "https://lendingkart.atlassian.net/rest/api/2/issue/{issue_key}/comment"
# ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 465
# SMTP_USER = "automation.user@lendingkart.com"
# SMTP_PASS = "eehi jeqo tskb dbwb"
# FROM_EMAIL = SMTP_USER
# EMAIL_SUBJECT = "Your Dashboard Access Credentials"
# CONSTANT_PASSWORD = "Lendingkart@321"
# JSESSIONID = "7b6c4bd7-2e93-410e-8014-24c0b30be582"  # Replace with a valid JSESSIONID
#
# logging.basicConfig(
#     filename='access_automation.log',
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
#
# if not all([SMTP_USER, SMTP_PASS]):
#     raise EnvironmentError("Required environment variables are not set.")
#
#
# # Send email notification to user
# def send_email(to_email, password):
#     msg = MIMEMultipart()
#     msg['From'] = FROM_EMAIL
#     msg['To'] = to_email
#     msg['Subject'] = EMAIL_SUBJECT
#
#     body = f"""Your dashboard access has been granted.\n\nEmail: {to_email},\nPassword: {password}"""
#     msg.attach(MIMEText(body, 'plain'))
#
#     try:
#         with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
#             server.login(SMTP_USER, SMTP_PASS)
#             server.sendmail(FROM_EMAIL, to_email, msg.as_string())
#         logging.info(f"Email sent to {to_email}.")
#     except Exception as e:
#         logging.error(f"Failed to send email to {to_email}: {e}")
#
#
# # Write user data to JSON file
# def write_user_data_to_json(user_data):
#     try:
#         if os.path.exists('userss_data.json'):
#             with open('userss_data.json', 'r') as file:
#                 data = json.load(file)
#         else:
#             data = []
#
#         data.append(user_data)
#
#         with open('userss_data.json', 'w') as file:
#             json.dump(data, file, indent=4)
#
#     except Exception as e:
#         logging.error(f"Failed to write user data to JSON: {e}")
#
#
# # Fetch JIRA issues based on the provided JQL query and custom fields
# def get_jira_issues():
#     query = {
#         'jql': f'project="{JIRA_PROJECT_KEY}" AND status="{JIRA_STATUS}" ORDER BY created DESC',
#         'fields': 'customfield_12528,customfield_12420,customfield_12477,customfield_12529,customfield_12529'
#     }
#
#     try:
#         logging.info(f"Sending GET request to {JIRA_URL} with query: {query['jql']}")
#         response = requests.get(
#             JIRA_URL,
#             headers={"Content-Type": "application/json"},
#             auth=JIRA_AUTH,
#             params=query
#         )
#         logging.info(f"Response Status Code: {response.status_code}")
#         response.raise_for_status()
#
#         issues = response.json()
#         logging.info(f"Fetched {len(issues.get('issues', []))} issues from JIRA")
#         return issues.get('issues', [])
#
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to fetch JIRA issues: {e}")
#         return []
#
#
# # Process user details and update JIRA
# def process_user(issue):
#     issue_key = issue['key']
#     fields = issue['fields']
#
#     # Extracting the custom fields
#     name = fields.get('customfield_12528')
#     email = fields.get('customfield_12420')
#     mobile = fields.get('customfield_12477')
#     role_name = fields.get('customfield_12529')
#
#     if not (name and email and role_name):
#         logging.warning(f"Missing required fields for issue {issue_key}. Skipping...")
#         return
#
#     password = CONSTANT_PASSWORD
#     logging.info(f"Processing user: {name}, Email: {email}, Password: {password}, Role: {role_name}")
#
#     try:
#         # Add user via cURL-like request
#         cookies = {'JSESSIONID': JSESSIONID}
#         add_user_response = requests.post(
#             ADD_USER_URL,
#             headers={'Content-Type': 'application/json'},
#             cookies=cookies,
#             data=json.dumps({
#                 "contactNo": mobile,
#                 "email": email,
#                 "name": name,
#                 "password": password,
#                 "roleName": role_name
#             })
#         )
#         add_user_response.raise_for_status()
#
#         if add_user_response.status_code == 201:
#             logging.info(f"User {name} added successfully.")
#             user_data = {
#                 "name": name,
#                 "email": email,
#                 "contactNo": mobile,
#                 "role": role_name,
#                 "password": password
#             }
#             write_user_data_to_json(user_data)
#
#             # Add a comment in JIRA
#             comment_response = requests.post(
#                 JIRA_COMMENT_URL.format(issue_key=issue_key),
#                 auth=JIRA_AUTH,
#                 headers={'Content-Type': 'application/json'},
#                 data=json.dumps({"body": "Access has been granted."})
#             )
#             comment_response.raise_for_status()
#             logging.info(f"Comment added to issue {issue_key}.")
#
#             # Transition JIRA issue
#             transition_response = requests.post(
#                 JIRA_TRANSITION_URL.format(issue_key=issue_key),
#                 auth=JIRA_AUTH,
#                 headers={'Content-Type': 'application/json'},
#                 data=json.dumps({"transition": {"id": "761"}})
#             )
#             transition_response.raise_for_status()
#             logging.info(f"Issue {issue_key} transitioned to 'Resolved'.")
#
#             # Send email
#             send_email(email, password)
#         else:
#             logging.error(f"Failed to add user {name}. Status code: {add_user_response.status_code}")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to process user for issue {issue_key}: {e}")
#
#
# def main():
#     logging.info("Starting access automation script")
#
#     issues = get_jira_issues()
#
#     if not issues:
#         logging.info("No issues found.")
#         return
#
#     for issue in issues:
#         process_user(issue)
#
#     logging.info("Access automation script completed")
#
#
# if __name__ == "__main__":
#     main()




import json
import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from requests.auth import HTTPBasicAuth

# JIRA and SMTP Configurations
JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_USER = "automation.user@lendingkart.com"
JIRA_API_TOKEN = "ATATT3xFfGF07jnnP2h7-tWWI1sV-ZPums3kvejb1zV4d8eCwrbXhY-MTLIQDv5rkCcOt6GU3o8BK03lBKB9kiUT8zZIu3JlZggC8yQwfpA_e-pfuHhCMX6yTv55KowjGhX8nMyYYzpSlpgILo0HNrTk4Rg2Fqto0EwJOUKeNDSrB2Um9wbua8Y=097D1ED1"
JIRA_AUTH = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_REQUEST_TYPE = "Dashboard Access"
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
JSESSIONID = "7b6c4bd7-2e93-410e-8014-24c0b30be582"  # Replace with a valid JSESSIONID

# Logging setup
logging.basicConfig(
    filename='access_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create 'automation.json' file if it doesn't exist
if not os.path.exists('automation.json'):
    with open('automation.json', 'w') as file:
        json.dump([], file, indent=4)  # Initialize with an empty list

# Check for necessary environment variables
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
def write_user_data_to_json(automation):
    try:
        # Check if the file exists and if not, create it with an empty list
        if  os.path.exists('automation.json'):
            with open('automation.json', 'r') as file:
                data = json.dump(file)  # Initialize with an empty list

        else:
            data = []

        data.append(automation)

        # Read existing data from the file
        with open('automation.json', 'r') as file:
            json.jump(data, file, indent=4)  # Load existing data


        # Write the updated data back to the file
        with open('automation.json', 'w') as file:
            json.dump(data, file, indent=4)  # Save updated data

        logging.info("User data successfully written to automation.json.")

    except Exception as e:
        logging.error(f"Failed to write user data to JSON: {e}")


# Fetch JIRA issues based on the provided JQL query and custom fields
def get_jira_issues():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" AND status="{JIRA_STATUS}" ORDER BY created DESC',
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

        with open('automation.json', 'w') as file:
            json.dump(issues, file, indent=4)

        logging.info("JIRA issues written to automation.json")
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
    role_name = fields.get('customfield_12529')

    if not (name and email and role_name):
        logging.warning(f"Missing required fields for issue {issue_key}. Skipping...")
        return

    password = CONSTANT_PASSWORD
    logging.info(f"Processing user: {name}, Email: {email}, Password: {password}, Role: {role_name}")

    try:
        # Adding user via cURL-like request
        cookies = {'JSESSIONID': JSESSIONID}
        add_user_response = requests.post(
            ADD_USER_URL,
            headers={'Content-Type': 'application/json'},
            cookies=cookies,
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

            # Add a comment in JIRA
            comment_response = requests.post(
                JIRA_COMMENT_URL.format(issue_key=issue_key),
                auth=JIRA_AUTH,
                headers={'Content-Type': 'application/json'},
                data=json.dumps({"body": "Access has been granted."})
            )
            comment_response.raise_for_status()
            logging.info(f"Comment added to issue {issue_key}.")

            # Transition JIRA issue
            transition_response = requests.post(
                JIRA_TRANSITION_URL.format(issue_key=issue_key),
                auth=JIRA_AUTH,
                headers={'Content-Type': 'application/json'},
                data=json.dumps({"transition": {"id": "761"}})
            )
            transition_response.raise_for_status()
            logging.info(f"Issue {issue_key} transitioned to 'Resolved'.")

            # Send email
            send_email(email, password)
        else:
            logging.error(f"Failed to add user {name}. Status code: {add_user_response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to process user for issue {issue_key}: {e}")


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
