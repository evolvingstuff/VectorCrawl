import os
import multiprocessing
import sqlite3
from bottle import Bottle, request, run, response, static_file
from scrapy.crawler import CrawlerProcess
from crawler.spiders.document_crawler import DocumentSpider
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from langchain.chains import SimpleSequentialChain
from langchain.embeddings import OpenAIEmbeddings


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

    # def run_crawler():
    #     process.crawl(DocumentSpider, start_url=url, progress_callback=progress_callback)
    #     process.start(stop_after_crawl=True)
    #
    # def on_crawl_complete():
    #     print('crawl complete')

    print('about to run...')

    # TODO this can only be run once without crashing. Need to fix
    process = CrawlerProcess()
    process.crawl(DocumentSpider, start_url=url, progress_callback=progress_callback)
    process.start()
    process.stop()

    broadcast_message('Generating embeddings...')
    # TODO run embedding generation here

    return {'message': f'Successfully finished creating embeddings for {url}'}


@app.route('/search', method='POST')
def search():
    query = request.forms.get('query')
    if not query:
        response.status = 400
        return {'error': 'Search query is required'}

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
