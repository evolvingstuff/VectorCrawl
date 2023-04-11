import os
import multiprocessing
from langchain import OpenAI
from langchain.chains import VectorDBQAWithSourcesChain
import sqlite3
from bottle import Bottle, request, run, response, static_file
from scrapy.crawler import CrawlerProcess
from crawler.spiders.document_crawler import DocumentSpider
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from langchain.chains import SimpleSequentialChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
import pickle
import faiss


app = Bottle()
process = CrawlerProcess()
clients = set()


@app.route('/')
def index():
    return static_file('index.html', root='./static')


@app.route('/<filename:re:.*\.(js|css)>')
def serve_static(filename):
    static_folder = 'static'
    return static_file(filename, root=static_folder)


@app.route('/crawl', method='POST')
def crawl():
    data = request.json
    url = data['url']
    api_key = data['api_key']
    if not url:
        response.status = 400
        return {'error': 'URL is required'}

    def progress_callback(msg):
        print(f'clients = {len(clients)} | broadcast: {msg}')
        broadcast_message(msg)

    print('about to run...')

    # TODO this can only be run once without crashing. Need to fix
    process = CrawlerProcess()
    process.crawl(DocumentSpider, start_url=url, progress_callback=progress_callback)
    process.start()
    process.stop()

    broadcast_message('Generating embeddings...')
    conn = sqlite3.connect('extracted_texts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM extracted_texts')
    rows = cursor.fetchall()

    docs = []
    metadatas = []
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    docs = []
    metadatas = []
    for row in rows[:25]:  # TODO: just first 25 for now
        text = row[3][:1500]  # TODO: figure this out later
        splits = text_splitter.split_text(text)
        docs.extend(splits)
        # metadatas.extend([{'id': row[0], 'url': row[1], 'title': row[2]}] * len(splits))
        metadatas.extend([{'source': row[1]}] * len(splits))

    store = FAISS.from_texts(docs, OpenAIEmbeddings(openai_api_key=api_key), metadatas=metadatas)
    faiss.write_index(store.index, "docs.index")
    store.index = None
    print('storing faiss index...')
    with open("faiss_store.pkl", "wb") as f:
        pickle.dump(store, f)
    print('done')

    return {'message': f'Successfully finished creating embeddings for {url}'}


@app.route('/search', method='POST')
def search():
    data = request.json
    query = data['query']
    api_key = data['api_key']
    if not query:
        response.status = 400
        return {'error': 'Search query is required'}

    # Load the FAISS index from disk.
    index = faiss.read_index("docs.index")

    # Load the vector store from disk.
    with open("faiss_store.pkl", "rb") as f:
        store = pickle.load(f)

    # merge the index and store
    store.index = index

    # Build the question answering chain.
    chain = VectorDBQAWithSourcesChain.from_llm(
        llm=OpenAI(openai_api_key=api_key, temperature=0, max_tokens=1500, model_name='text-davinci-003'), vectorstore=store)

    # Run the chain.
    result = chain({"question": query})

    # Print the answer and the sources.
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")

    # Your search implementation here
    # For now, return a stubbed response
    return {'results': [{'title': 'Sample result', 'url': 'https://example.com'}]}


class WebSocketHandler(WebSocketApplication):
    def on_open(self):
        clients.add(self.ws)

    def on_message(self, message):
        if message is not None:
            # Send the received message to all clients
            broadcast_message("Received: " + message)

    def on_close(self, reason):
        clients.remove(self.ws)


def broadcast_message(message):
    for client in clients.copy():
        try:
            client.send(message)
        except Exception as e:
            print(f"Error sending message to client: {e}")
            clients.remove(client)


if __name__ == '__main__':
    server = WebSocketServer(('localhost', 8080), Resource({'/': app, '/websocket': WebSocketHandler}))
    server.serve_forever()
