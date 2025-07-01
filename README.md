# Slack Bot Development with BigQuery Vector Search

## Overview

BigQuery has a RAG system using vector search. To see how good this vector search is 
I decided to build a RAG system with BigQuery using a chat framework called Slack Bolt.

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

## environment variables

Set the following environment variables in your terminal or in a `.env` file.

```bash
cp .env.example .env
```

You can edit the `.env` file to set your environment variables, or you can set them directly in your terminal.

```text
PROJECT_ID=your-project-id
APP_ENVIRONMENT=development
SLACK_BOT_TOKEN=your-slack-bot-token
PORT=8080
```

## Install dependencies

To run the Slack app, you need to install the required Python packages. You can do this by running the following command in your terminal:

```bash
pip install python-dotenv
```

### Google Cloud Project ID

If you are not using a `.env` file in this project, set the following environment variables directly in your terminal before running the Slack app.
If you are using a `.env` file, you can skip this step as the `PROJECT_ID` will be set automatically when you run the app.

Set the `PROJECT_ID` environment variables.

```bash
export PROJECT_ID=`gcloud config list --format 'value(core.project)'` && echo $PROJECT_ID
```

### Set SlackApp Token

If you are not using a `.env` file in this project, set the following environment variables directly in your terminal before running the Slack app.
If you are using a `.env` file, you can skip this step as the Slack app tokens will be set automatically when you run the app.

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

## Conclusion

This project demonstrates how to build a Slack bot that utilizes BigQuery's vector search capabilities for retrieving and summarizing web page content. By following the steps outlined above, you can set up your own Slack app, configure it to interact with BigQuery, and deploy it to Google Cloud. This setup allows for efficient retrieval of information and provides a foundation for further enhancements and features in your Slack bot.

As the amount of data increases, BigQuery's vector search tends to take more time. This is because a larger dataset requires more processing time for searches.

To address this, you can classify data into appropriate tables or use agents with MCP or A2A to narrow down the search scope based on content.

Specifically, consider the following approaches:

1. **Data Classification**: Divide data into different tables by category to narrow the search scope. For example, store news articles, blog posts, and product reviews in separate tables.

2. **Use of Indexes**: BigQuery allows you to create indexes on tables, which can speed up searches on specific columns. Setting indexes on frequently searched columns is especially effective.

3. **Query Optimization**: Optimize your queries to reduce search time. For example, select only the necessary columns, add filtering conditions, or use subqueries to reduce the amount of data processed.

4. **Partitioning**: Partition data by time or other criteria to reduce the amount of data searched. This allows you to search only the data that matches a specific period or condition.

5. **Use of Agents**: Create agents using MCP (Multi-Cloud Platform) or A2A (Agent-to-Agent) to narrow the search scope based on specific content. This enables searching only the most relevant data for a user's query.

6. **Caching**: Implement caching mechanisms to store frequently accessed data, reducing the need for repeated searches in BigQuery.
