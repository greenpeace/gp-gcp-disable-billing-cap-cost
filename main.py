import logging
import os
import requests

# Install Google Libraries
from google.cloud import secretmanager

# Setup the Secret manager Client
client = secretmanager.SecretManagerServiceClient()
# Get the sites environment credentials
project_id = os.environ["PROJECT_NAME"]

# Get the secret for Slack
secret_name = "slack-hook-key"
resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
response = client.access_secret_version(resource_name)
slackhookkeyurl = response.payload.data.decode('UTF-8')

# Get the secret for Mailgun
secret_name = "mailgun_domain"
resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
response = client.access_secret_version(resource_name)
mailgundomain = response.payload.data.decode('UTF-8')

# Get the secret for Mailgun
secret_name = "mailgun-api"
resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
response = client.access_secret_version(resource_name)
mailgunapi = response.payload.data.decode('UTF-8')

# Request Header
headers = {
    'Content-Type': 'application/json'
}

def gpi_disable_billing_cap_cost(data, context):

    import base64
    import json
    pubsub_budget_notification_data = json.loads(base64.b64decode(data['data']).decode('utf-8'))
    logging.info('Logging Details: {}'.format(pubsub_budget_notification_data))

    # The budget alert name must be created with the project_id you want to cap
    budget_project_id = pubsub_budget_notification_data['budgetDisplayName']

    # The budget amount to cap costs
    budget = pubsub_budget_notification_data['budgetAmount']

    logging.info('Handling budget notification for project id: {}'.format(budget_project_id))
    logging.info('The budget is set to {}'.format(budget))
    logging.info('Handling the cost amount of : {} for the budget notification period / month, or technically '
                 'the costIntervalStart : {}'.format(pubsub_budget_notification_data['costAmount'],
                                                     pubsub_budget_notification_data['costIntervalStart']))

    # If the billing is already disabled, stop Cloud Function execution
    if not __is_billing_enabled(budget_project_id):
        raise RuntimeError('Billing already in disabled state')
    else:
        # get total costs accrued per budget alert period

        # Calculating the total as the sum of the cost amounts which are values to start intervals keys in the dict
        monthtotal = pubsub_budget_notification_data['costAmount']
        logging.info('The month to date total is {}'.format(monthtotal))

        # Disable or not the billing for the project id depending on the total and the budget
        if monthtotal < budget:
            logging.info('No action will be taken on the total amount of {} for the period {} .'
                        .format(monthtotal, pubsub_budget_notification_data['costIntervalStart']))
        else:
            logging.info('The monthly total is more than {} euros for period {}, the monthly budget amount is set to {}, the billing will be disable for project id {}.'
                        .format(budget, pubsub_budget_notification_data['costIntervalStart'], monthtotal, budget_project_id))
            payload = '{{"text":"The monthly total is more than {} euros for period {}, the monthly budget amount is set to {}, the billing will be disable for project id {}."}}'\
                        .format(monthtotal, pubsub_budget_notification_data['costIntervalStart'], budget, budget_project_id)
            response = requests.request("POST", slackhookkeyurl, headers=headers, data=payload)
            emailtext = 'The monthly total is more than {} euros for period {}, the monthly budget amount is set to {}, the billing will be disable for project id {}.'\
                        .format(monthtotal, pubsub_budget_notification_data['costIntervalStart'],  budget, budget_project_id)
            __send_email_message_mailgun(emailtext)
            #__disable_billing_for_project(budget_project_id)
            
def __is_billing_enabled(project_id):

    service = __get_cloud_billing_service()
    billing_info = service.projects().getBillingInfo(name='projects/{}'.format(project_id)).execute()
    if not billing_info or 'billingEnabled' not in billing_info:
        return False
    return billing_info['billingEnabled']

def __get_cloud_billing_service():
    # Creating credentials to be used for authentication, by using the Application Default Credentials
    # The credentials are created  for cloud-billing scope
    from oauth2client.client import GoogleCredentials
    credentials = GoogleCredentials.get_application_default()

    # The name and the version of the API to use can be found here https://developers.google.com/api-client-library/python/apis/
    from apiclient import discovery
    return discovery.build('cloudbilling', 'v1', credentials=credentials, cache_discovery=False)

def __disable_billing_for_project(project_id):

    service = __get_cloud_billing_service()
    billing_info = service.projects()\
        .updateBillingInfo(name='projects/{}'.format(project_id), body={'billingAccountName': ''}).execute()
    assert 'billingAccountName' not in billing_info

def __send_email_message_mailgun(emailtext):
	return requests.post(
        "https://api.mailgun.net/v3/" + mailgundomain + "/messages",
        auth=("api", mailgunapi),
        data={"from": "Excited User <notify@test.com>",
                "to": "notify@test.com",
                "subject": "Budget Notification",
                "text": emailtext})