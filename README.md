# Techlab disable billing to cap the cost

I will explain how you can create a Google Cloud Platform (GCP) Cloud Function, that you can use to cap the cost, if the cost is higher than the budget the billing will be disabled.

You may ask why do I want to do this, you can set up billing notifications in GCP that sends you an email when your budget limits are achieved, yes that works well sometimes. There are times when you may have installed an updated to Cloud Engine App that occurs on the network edge starting to generate a large amount of traffic, your billing increase dramatically.

I had an issue once when I wrote a Cloud Function, I published it, there was something wrong in the code within minutes the wrong code had generated over 100 dollars to my billing in seconds, things happen it’s better to be sorry and playing it safe than just go in a wimp till you get a bill and you say what did happen?

Google was very good with my Cloud Function that went down, I contacted there billing department and explain what happens and they paid back the money. If it happens again, I now have a Cloud Function that will stop the billing and limited the cost.

# The GCP Architect Services
In the GCP I’m using the following services as show in the diagram below:
![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/2fa8ace5-disable-billing-function.png "GCP Architecture")

# Disabling Billing
If the total spend of a project exceeds the budget fixed for the project, the billing will be disabled for the project using Cloud Billing API and also send a notification. One word about disabling Billing through the Google Billing API, when you programmatically sends a diable billing through the BIlling API, your billing account will go from active to inactive. It will shut down any services that you have on the GCP project. Say you running your WordPress site on the Google Compute Engine, your WordPress site will go down, be careful when using the Cloud Function to disable billing.

# Let’s get started
Let’s get started to set up all the GCP services to tie all the pieces together so that you will be able to disable billing for your GCP project.

## Billing Notifications
The first thing we need to do is to create a budget alert for our GCP Billing, in the Google Cloud Platform Console navigate to Billing -> Budgets & alerts.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/2fa8ace5-disable-billing-function.png "GCP Architecture")

Create an alert use the project id as the name of your billing alert and select the alert to be sent to Pub/Sub – named the Sub/Pub topic to budgets-notifications.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/3bc17977-cloud-billing-pubsub.png "GCP Billing Alerts")

When you save the billing alert you would see something like this.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/3fb7fb9f-budget-alert.png "GCP Budget Alert")

## Cloud Pub/Sub
When you created a budget alert, you had that the option to create a Pub/Sub topic – you can now navigate to Pub/Sub and look at your topic and to verify after you have published your Cloud Function that the Cloud Function is subscribed to your Pub/Sub topic.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/ce844aa6-pubsub-topic-subscriptions.png "GCP Pub/Sub Topic")

## Enable Cloud Billing API
For the Cloud Function to be able to disable billing we need to enable the Cloud Billing API, navigate to Google Cloud Platform Console APIs & Services, and enable the Cloud Billing API.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/fc91741a-cloudbilling.png "GCP Billing API")

## Secret Manager
I store all my secrets for the Cloud Function with the Secret Manager, you can read how to use the Secret Manager in this article [Using Secret Manager in a Google Cloud Function with Python] (https://torbjornzetterlund.com/using-secret-manager-in-a-google-cloud-function-with-python/)

## The Cloud Function Code in Python
Below is the code for the cloud function, I’m using the Secret Manager to manage my Slack Hook Key, the mailgun credentials as I using Slack and Mailgun to send me a notification at the same time as I disable the billing account, hopefully, I will catch the notification on these mediums in time, so I can analyze why the billing was shutdown and enable billing if required. I also use Environment variables to set my Environment variables.

![Alt text](https://storage.googleapis.com/wordpress_file_storage/2020/06/8dcc2de3-cloudfunctionenvironmentvariable.png "GCP Cloud Function Environment Variable")

## Cloud Function Environment Variable
I’m not going to explain all the lines of code, basically, we have a Pub/Sub trigger Cloud Function, when data starts flowing from billing it will trigger the function to execute, the cloud function just lives for a short time. The payload that comes from the Pub/Sub topic looks like this.

{'budgetDisplayName': 'torbjorn-zetterlund', 'costAmount': 0.59, 'costIntervalStart': '2020-06-01T07:00:00Z', 'budgetAmount': 50.0, 'budgetAmountType': 'SPECIFIED_AMOUNT', 'currencyCode': 'EUR'}

The Cloud Functions read this data and make a determination if the costAmount is higher than the budgetAmount, if that is the case it will trigger the disabling of the cloud billing and send email notification via mailgun and Slack notification to the Slack webhook. Below is the full code snippet.

## Authorization for the Cloud Function
At runtime, the Cloud Function uses a service account, which is listed at the bottom of the Cloud Function details page in the Google Cloud Platform Console.

You can manage Billing Admin permissions on the Google Cloud Platform Console Billing page. Add the Cloud Function runtime service account as a member and give it Billing Account Administrator privileges.

To give the Cloud Function runtime service account the Browser role, you need to add it as a member to each project to monitor through Google Cloud Platform IAM page and give it the Browser role.

## Cost
The Cloud Billing API, Cloud Pub/Sub and Cloud Function calls and data is on the free tier.

# Deploy command line
gcloud functions deploy gpi_cap_budget --region=europe-west1 --memory=128MB --runtime=python37 --trigger-topic=budgets-notifications

## Enable Secrets API with command line
gcloud services enable secretmanager.googleapis.com cloudfunctions.googleapis.com

## Creat the secret
echo -n "<slack url>" | \
    gcloud beta secrets create slack_secret \
      --data-file=- \
      --replication-policy automatic

## View Secret
gcloud beta secrets versions access 1 --secret="slack_secret"

# Setup Cloud Build
Included in the repository is a .yaml file that you can use with Cloud Build to automate deployment after the first install of the Cloud Function.
