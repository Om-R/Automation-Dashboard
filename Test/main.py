import json
import logging
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
JIRA_REQUEST_TYPE = "Test"
JIRA_STATUS = "Approval Required"

# TSE User credentials and URL
TSE_USER = "tse@lendingkart.com"  # Replace with actual TSE user email
JSESSION_ID = "48a529a8-bcd3-4591-943e-0affc3b105a0"  # Replace with actual JSESSIONID
ADD_USER_URL = "https://app.lendingkart.com/admin/addUser"  # Removed extra spaces
Accept = "/"


# Function to fetch JIRA issues
def get_jira_issues():
    query = {
        'jql': f'project="{JIRA_PROJECT_KEY}" AND "Request Type" = "{JIRA_REQUEST_TYPE}" AND status="{JIRA_STATUS}" ORDER BY created DESC',
        'fields': 'customfield_12528,customfield_12420,customfield_12477,customfield_12529,customfield_12529'
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
    # Ensure contact_no is a string
    contact_no = str(contact_no).strip()  # Convert to string and remove any whitespace

    # Validate mobile number length (for example, 10 digits for Indian numbers)
    if len(contact_no) != 10 or not contact_no.isdigit():
        logging.error(f"Invalid mobile number format: {contact_no}")
        return False

    # Extract the child value from role_name if it's a dictionary
    if isinstance(role_name, dict) and 'child' in role_name:
        role_name = role_name['child']['value']  # Get the value of the child

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
        "roleName": role_name  # Now this is just the child value
    }

    logging.info(f"Sending POST request to {ADD_USER_URL} with headers: {headers} and data: {data}")

    try:
        response = requests.post(ADD_USER_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        if response.status_code == 201:
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
        name = fields.get('customfield_12528')
        email = fields.get('customfield_12420')
        mobile = fields.get('customfield_12477')
        role_name = fields.get('customfield_12529')

        # Convert mobile number to string and remove any decimal point
        if isinstance(mobile, float):
            mobile = str(int(mobile))  # Convert float to int and then to string
        else:
            mobile = str(mobile).strip()  # Ensure it's a string and remove whitespace

        logging.info(f"Processing issue: {issue['key']} with name: {name}, email: {email}, mobile: {mobile}, role: {role_name}")

        if not (name and email and role_name):
            logging.warning(f"Missing required fields for issue {issue['key']}. Skipping...")
            continue

        password = "Pass@321"  # Set a default password or generate one
        success = add_user(mobile, email, name, password, role_name)

        if success:
            logging.info(f"User  {name} access granted successfully.")
        else:
            logging.info(f"Failed to grant access to user {name}.")



if __name__ == "__main__":
    main()