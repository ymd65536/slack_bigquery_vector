import datetime
import os
from dotenv import load_dotenv

from google.cloud import bigquery

from web import bigquery_vector

from slack_bolt import App, Ack
from slack_bolt.adapter.socket_mode import SocketModeHandler

from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_google_vertexai import VertexAI
from langchain.chains import RetrievalQA

load_dotenv()

PROJECT_ID = os.environ.get("PROJECT_ID", "")
APP_ENVIRONMENT = os.environ.get("APP_ENVIRONMENT", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
PORT = os.environ.get("PORT", 8080)
app = App(
    token=SLACK_BOT_TOKEN, process_before_response=True
)


def _get_web_page_document(url: str, start_tag: str, end_tag: str) -> list:
    """
        Webページのドキュメントを取得してBody部分だけ取り出すメソッド
    Returns:
        _type_: WebページのうちBodyタグで囲まれた文字列(htmlパース後の文字列)
    """
    loader = RecursiveUrlLoader(url)
    documents = loader.load()

    for document in documents:
        start_index = document.page_content.find(start_tag)
        end_index = document.page_content.find(end_tag)
        documents[0].page_content = document.page_content[start_index:end_index]

    html2text = Html2TextTransformer()
    plain_text = html2text.transform_documents(documents)

    # 1000文字単位で分割する際、1000文字未満の文字列だと1000文字分割は意味がないためそのまま格納
    text_li = []
    if len(plain_text[0].page_content) > 999:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["。"]
        )
        text_li.extend(text_splitter.split_documents(plain_text))

    else:
        text_li.extend(plain_text)

    return text_li


def _get_documents(link, start_tag='<main', end_tag='</main'):
    """
        Webページから本文とメタデータを取り出す
    Returns:
        _type_: 辞書型:vector_storeに利用するWebページのメタデータセット
    """

    docs = []
    metadatas = []

    DIFF_JST_FROM_UTC = 9
    result_time = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    yyyymmdd = f"{result_time.strftime('%Y')}-{result_time.strftime('%m')}-{result_time.strftime('%d')}"
    hourminsec = f" {result_time.strftime('%H')}:{result_time.strftime('%M')}:{result_time.strftime('%S')}"
    html_docs = _get_web_page_document(link, start_tag, end_tag)

    html_path = link.split('/')[-1]
    if html_path == "":
        html_path = link.split('/')[-2]

    for html_doc in html_docs:
        docs.append(f"\n [リンク]({link})\n,ページは{html_path}です。\n" + html_doc.page_content)
        metadatas.append(
            {
                "yyyymmdd": yyyymmdd,
                "hourminsec": hourminsec,
                "link": link,
                "html_path": html_path,
                "len": str(len(html_doc.page_content)),
                "update_time": str(result_time)
            }
        )
    return {"docs": docs, "metadatas": metadatas}


def _delete_article(html_path):
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
DELETE FROM `project_id.db.table` WHERE JSON_VALUE(metadata.html_path)='{html_path}'
"""

    try:
        client.query(query)  # Make an API request.
    except Exception as e:
        return str(e)
    client.close()
    return "データベースを更新中"


def _create_prompt(prompt, url):

    if url == "":
        must_prompt = f"""
以下の質問に回答してください。
質問内容：
{prompt}
---
回答方法：
回答は300文字以内で回答し、文章の最後に根拠となるリンクを1つつけてください。
根拠がつけられない回答についてはリンクをつけず、どのような回答になるか教えてください。
"""
    else:
        protocol = url.split('/')[0]
        domain = url.split('/')[-2]
        must_prompt = f"""
以下の質問に回答してください。
質問内容：
{prompt}
---
回答方法：
「{url}」が含まれる文章を参考に回答してください。
回答は300文字以内で回答し、文章の最後に根拠となる「{protocol}://{domain}」ではじまるリンクを1つつけてください。
根拠がつけられない回答についてはリンクをつけず、どのような回答になるか教えてください。
    """
    return must_prompt


def handle_mention(event, say):
    thread_id = event['ts']
    if "thread_ts" in event:
        thread_id = event['thread_ts']

    say("処理中", thread_ts=thread_id)

    for block in event['blocks']:
        elements = block.get('elements', [])

    for element in elements:
        eles = element['elements']

    urls = []
    texts = []
    for ele in eles:
        if ele['type'] == "link":
            urls.append(ele['url'])

        if ele['type'] == "text":
            texts.append(ele['text'])

    if len(urls) > 1:
        say("URLが2つ以上送信されました。チェックできるURLは1つのみです。", thread_ts=thread_id)
        return 0

    chat = VertexAI(
        model_name=os.environ.get("USE_TEXT_MODEL_NAME", None),
        temperature=0
    )
    vector_store = bigquery_vector.get_bigquery_vector_store(
        os.environ.get('BQ_DATASET', None),
        os.environ.get('BQ_TABLE', None)
    )

    prompt = "".join(texts)
    if not urls:
        say("リンクがなかったため、データベースから検索します。", thread_ts=thread_id)
        send_prompt = _create_prompt(prompt, "")
    else:
        url = "".join(urls)

        html_path = url.split('/')[-1]
        if html_path == "":
            html_path = url.split('/')[-2]
        send_prompt = _create_prompt(prompt, url)
        say(_delete_article(html_path), thread_ts=thread_id)

        if url in 'サイト名':
            docs_and_metadata = _get_documents(url)
        else:
            docs_and_metadata = _get_documents(url, '<body', '</body')

        vector_store.add_texts(
            docs_and_metadata['docs'],
            metadatas=docs_and_metadata['metadatas']
        )

    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3}
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever
    )

    answer = qa_chain.invoke(send_prompt)
    say(str(answer['result']), thread_ts=thread_id)


def slack_ack(ack: Ack):
    ack()


app.event("app_mention")(ack=slack_ack, lazy=[handle_mention])

if __name__ == "__main__":
    if APP_ENVIRONMENT == "prod":
        app.start(port=int(PORT))
    else:
        print("SocketModeHandler")
        SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
        SocketModeHandler(app, SLACK_APP_TOKEN).start()