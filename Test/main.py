import json
import logging
from http.client import responses

import requests
import os

# Configure logging
logging.basicConfig(
    filename='main_log.log',  # Log file name
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



# JIRA Configuration
JIRA_URL = "https://lendingkart.atlassian.net/rest/api/2/search"
JIRA_USER = "automation.user@lendingkart.com"  # Replace with actual JIRA user email
JIRA_API_TOKEN = "ATATT3xFfGF07jnnP2h7-tWWI1sV-ZPums3kvejb1zV4d8eCwrbXhY-MTLIQDv5rkCcOt6GU3o8BK03lBKB9kiUT8zZIu3JlZggC8yQwfpA_e-pfuHhCMX6yTv55KowjGhX8nMyYYzpSlpgILo0HNrTk4Rg2Fqto0EwJOUKeNDSrB2Um9wbua8Y=097D1ED1"
JIRA_PROJECT_KEY = "Tools Helpdesk"
JIRA_REQUEST_TYPE = "LK Dashboards"
JIRA_STATUS = "Approval Required"

# TSE User credentials and URL
TSE_USER = "tse@lendingkart.com"
JSESSION_ID = "3b762075-1d85-4350-bf0e-f70e7b3a52f1"
ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"
Accept = "/"

# domain_email_mapping = {
#     'gmail.com': 'customfield_12396',
#     'lendingkart.com': 'customfield_12420',
#
# }

# Function to fetch JIRA issues
def get_jira_issues():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" AND "Request Type" = "{JIRA_REQUEST_TYPE}" AND status="{JIRA_STATUS}" ORDER BY created DESC',
        # 'fields': 'customfield_12528,customfield_12420,customfield_12477,customfield_12529,customfield_12529'
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"Sending GET request to {JIRA_URL} with query: {query['jql']}")
        response = requests.get(
            JIRA_URL,
            headers=headers,
            auth=(JIRA_USER, JIRA_API_TOKEN),
            params=query
        )
        response.raise_for_status()
        print(response)

        issues = response.json()
        logging.info(f"Fetched {len(issues.get('issues', []))} issues from JIRA")

        # Store fetched data in data_main.json
        with open('data_main.json', 'w') as json_file:
            json.dump(issues, json_file, indent=4)
            logging.info("JIRA issues written to data_main.json")

            return issues.get('issues', [])

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch JIRA issues: {e}")
        return []


# Function to add user using TSE credentials with JSESSIONID
def add_user(contact_no, email, name, password, role_name):
    contact_no = str(contact_no).strip()

    if len(contact_no) != 10 or not contact_no.isdigit():
        logging.error(f"Invalid mobile number format: {contact_no}")
        return False

    if isinstance(role_name, dict) and 'child' in role_name:
        role_name = role_name['child']['value']

    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Cookie': f'JSESSIONID={JSESSION_ID}',
        'cache-control': 'no-cache'
    }

    data = {
        "contactNo": contact_no,
        "email": email,
        "name": name,
        "password": password,
        "roleName": role_name
    }

    logging.info(f"Sending POST request to {ADD_USER_URL} with data: {data}")

    response = None

    try:
        response = requests.post(ADD_USER_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        if response.status_code == 200:
            logging.info(f"User   {name} added successfully.")
            return True
        else:
            logging.error(f"Failed to add user {name}. Status code: {response.status_code}, Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while adding user {name}: {e}")
        if response is not None:
            logging.error(f"Response content: {response.text}")
        return False


# Function to extract domain from email
def get_domain(email):
    return email.split('@')[-1] if '@' in email else None


# def main():
#     logging.info("Starting TSE user access script")
#
#     # Fetch JIRA issues
#     issues = get_jira_issues()
#
#     if not issues:
#         logging.info("No issues found.")
#         return
#
#     # Process each issue to add users
#     for issue in issues:
#         fields = issue['fields']
#
#         # Initialize variables
#         email = fields.get('customfield_12420')
#         name = fields.get('customfield_12528')
#         mobile = fields.get('customfield_12477')
#         role_name = fields.get('customfield_12529')
#
#         # Check the email domain email_field_id = None
#         # for domain, field_id in domain_email_mapping.items():
#         #     email = fields.get(field_id)  # Get the email from the mapped custom field
#         #     if email:
#         #         email_field_id = field_id
#         #         break
#         #
#         # if email_field_id:
#         #     domain = get_domain(email)  # Extract domain from the fetched email
#         # else:
#         #     logging.warning(f"No email found in mapped fields for issue {issue['key']}. Skipping...")
#         #     continue
#
#         # Convert mobile number to string and remove any decimal point
#         if isinstance(mobile, float):
#             mobile = str(int(mobile))  # Convert float to int and then to string
#         else:
#             mobile = str(mobile).strip()  # Ensure it's a string and remove whitespace
#
#         logging.info(
#             f"Processing issue: {issue['key']} with name: {name}, email: {email}, mobile: {mobile}, role: {role_name}")
#
#         if not (name and email and role_name):
#             logging.warning(f"Missing required fields for issue {issue['key']}. Skipping...")
#             continue
#
#         password = "Pass@321"  # Set a default password or generate one
#         success = add_user(mobile, email, name, password, role_name)
#
#         if success:
#             logging.info(f"User  {name} access granted successfully.")
#         else:
#             logging.info(f"Failed to grant access to user {name}.")

def main():
    logging.info("Starting TSE user access script")

    # Fetch JIRA issues
    issues = get_jira_issues()

    if not issues:
        logging.info("No issues found.")
        return

    # Process each issue to add users
    for issue in issues:
        fields = issue['fields']

        # Initialize variables
        email = fields.get('customfield_12420')
        name = fields.get('customfield_12305')
        mobile = fields.get('customfield_12477')
        role_name = fields.get('customfield_12334')

        # Convert mobile number to string and remove any decimal point
        if isinstance(mobile, float):
            mobile = str(int(mobile))  # Convert float to int and then to string
        else:
            mobile = str(mobile).strip()  # Ensure it's a string and remove whitespace

        logging.info(
            f"Processing issue: {issue['key']} with name: {name}, email: {email}, mobile: {mobile}, role: {role_name}")

        if not (name and email and role_name):
            logging.warning(f"Missing required fields for issue {issue['key']}. Skipping...")
            continue

        # Check if role_name is not "Account-Read-Only"
        if role_name != "Account Read Only":
            logging.warning(
                f"Access denied for user {name}. Role '{role_name}' is not allowed to be granted access. Skipping...")
            continue

        password = "Pass@321"  # Set a default password
        success = add_user(mobile, email, name, password, role_name)

        if success:
            logging.info(f"User {name} access granted successfully.")
        else:
            logging.info(f"Failed to grant access to user {name}.")


if __name__ == "__main__":
    main()