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

```bash
export SLACK_BOT_TOKEN=
export SLACK_APP_TOKEN=
export SLACK_SIGNING_SECRET=
```

## Set App Environment Variable

`APP_ENVIRONMENT` is an environment variable that changes the execution state of the application. If a value other than `prod` is set, the Slack application will be launched in Socket Mode.

In this case, we will set `APP_ENVIRONMENT` to `dev`.

```bash
export APP_ENVIRONMENT=dev
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
