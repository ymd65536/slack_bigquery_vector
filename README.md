# Slack Bot Development with BigQuery Vector Search

## install gcloud

First, install gcloud using curl.

```bash
curl -sSL https://sdk.cloud.google.com | bash && exec -l $SHELL && gcloud init
```

Then, log in with gcloud.

```bash
gcloud auth login
```

To set the project ID in the `gcloud` command-line tool, you need to replace `{project_id}` with your actual Google Cloud project ID.

You can find your Project ID on the Google Cloud Welcome page.
※Check [welcome google cloud](https://console.cloud.google.com/welcome?)

The correct command is:
```bash
gcloud config set project PROJECT_ID
```

For example, if your project ID is `my-awesome-project-123`, you would run:
```bash
gcloud config set project my-awesome-project-123
```

This command sets the active Google Cloud project for all subsequent `gcloud` commands.

Next, you will set up Application Default Credentials (ADC).

```bash
gcloud auth application-default login
```

This completes the setup. / The setup is now complete.

## environment

Set the `PROJECT_ID` environment variable.

```bash
export PROJECT_ID=`gcloud config list --format 'value(core.project)'` && echo $PROJECT_ID
```

## Set SlackApp Token

To run the Slack app, you need to set the following environment variables with your Slack app credentials. You can create a Slack app and obtain these tokens from the [Slack API: Applications](https://api.slack.com/apps) page.

```bash
export SLACK_APP_TOKEN=
export SLACK_BOT_TOKEN=
export SLACK_SIGNING_SECRET=
```

### Create a Slack app

Create `WebPageSummarizer` app on Slack.

1. Go to the [Slack API: Applications](https://api.slack.com/apps) page.
2. Click on "Create New App".
3. Choose "From scratch".
4. Enter the app name `WebPageSummarizer` and select your workspace.
5. Click "Create App".
6. In the "Basic Information" section, you will find the `Signing Secret`. Copy it and set it as the `SLACK_SIGNING_SECRET` environment variable.
7. In the "OAuth & Permissions" section, scroll down to "Scopes" and add the following bot token scopes:
   - `app_mentions:read`
   - `chat:write`
   - `im:read`
   - `channels:history`
   - `groups:history`
   - `im:history`
   - `mpim:history`
8. On Event Subscriptions
    - Enable "Event Subscriptions".
    - Set the Request URL to `https://your-domain.com/slack/events` (you will need to set up a server to handle this).
    - Under "Subscribe to Bot Events", add the following events:
      - `app_mention`
      - `message.channels`
      - `message.groups`
      - `message.im`
      - `message.mpim`

## Set App Environment Variable

`APP_ENVIRONMENT` is an environment variable that changes the execution state of the application. If a value other than `prod` is set, the Slack application will be launched in Socket Mode.

In this case, we will set `APP_ENVIRONMENT` to `dev`.

```bash
export APP_ENVIRONMENT=dev
```

```bash
export USE_MODEL_NAME=text-embedding-005
export USE_TEXT_MODEL_NAME=gemini-2.0-flash
```

## Set BigQuery Dataset

To use BigQuery for storing and retrieving web page summaries, you need to set the following environment variables for the BigQuery dataset and table.

```bash
export BQ_DATASET=web_page_summarizer
export BQ_TABLE=web_page_summaries
```

Create the BigQuery dataset and table using the following commands:

```bash
bq --project_id $PROJECT_ID mk --dataset $BQ_DATASET
bq --project_id $PROJECT_ID mk --table $BQ_DATASET.$BQ_TABLE
```

## Install dependencies

```bash
cd docker
pip install -r requirements.txt
```

## Run Slack app locally

```bash
python app.py
```

## Prompt for Slack app

```text
@WebPageSummarizer
What are the new AI-powered tools announced at Google Cloud Next '25?
https://iret.media/150057
```

## Run Slack app on Google Cloud

```bash
export APP_ENVIRONMENT=prod
```

```bash
gcp_project=`gcloud config list --format 'value(core.project)'`
image_name=bigquery-vector

gcloud auth login
gcloud config set project $gcp_project

gcloud auth configure-docker asia-northeast1-docker.pkg.dev
gcloud artifacts repositories create $image_name --location=asia-northeast1 --repository-format=docker --project=$gcp_project

docker rmi asia-northeast1-docker.pkg.dev/$gcp_project/$image_name/$image_name && docker rmi $image_name
docker build . -t $image_name --platform linux/amd64
docker tag $image_name asia-northeast1-docker.pkg.dev/$gcp_project/$image_name/$image_name && docker push asia-northeast1-docker.pkg.dev/$gcp_project/$image_name/$image_name:latest
```
