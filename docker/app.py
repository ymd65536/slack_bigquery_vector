import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from langchain.chains import RetrievalQA
from langchain.vectorstores.utils import DistanceStrategy

from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_vertexai import VertexAI

from langchain_community.vectorstores import BigQueryVectorSearch

NUMBER_OF_RESULTS = 3

PROJECT_ID = os.environ.get("PROJECT_ID", "")
LOCATION = os.environ.get("LOCATION", "asia-northeast1")

USE_EMBEDDING_MODEL_NAME = os.environ.get("USE_EMBEDDING_MODEL_NAME", "textembedding-gecko@latest")
USE_CHAT_MODEL_NAME = os.environ.get("USE_CHAT_MODEL_NAME", "text-bison-32k@002")

BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "")
BIGQUERY_TABLE = os.environ.get("BIGQUERY_TABLE", "")

APP_ENVIRONMENT = os.environ.get("APP_ENVIRONMENT", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

app = App(token=SLACK_BOT_TOKEN)


@app.event("app_mention")
def handle_mention(event, say):
    embedding = VertexAIEmbeddings(
        model_name=USE_EMBEDDING_MODEL_NAME, project=PROJECT_ID
    )

    vector_store = BigQueryVectorSearch(
        project_id=PROJECT_ID,
        dataset_name=BIGQUERY_DATASET,
        table_name=BIGQUERY_TABLE,
        location=LOCATION,
        embedding=embedding,
        distance_strategy=DistanceStrategy.EUCLIDEAN_DISTANCE,
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": NUMBER_OF_RESULTS}
    )

    chat = VertexAI(model_name=USE_CHAT_MODEL_NAME, temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever
    )

    query = event["text"]
    answer = qa_chain.invoke(query)
    say(answer.get("result", "No Response"))


# アプリを起動します
if __name__ == "__main__":
    if APP_ENVIRONMENT == "prod":
        app.start(port=int(os.environ.get("PORT", 8080)))
    else:
        print("SocketModeHandler")
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
