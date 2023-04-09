from bottle import Bottle, request, run, response, static_file

app = Bottle()


@app.route('/')
def index():
    return static_file('index.html', root='./static')


@app.route('/crawl', method='POST')
def crawl():
    url = request.forms.get('url')
    if not url:
        response.status = 400
        return {'error': 'URL is required'}

    # Your crawl implementation here
    # For now, return a stubbed response
    return {'message': f'Successfully crawled {url}'}


@app.route('/search', method='POST')
def search():
    query = request.forms.get('query')
    if not query:
        response.status = 400
        return {'error': 'Search query is required'}

    # Your search implementation here
    # For now, return a stubbed response
    return {'results': [{'title': 'Sample result', 'url': 'https://example.com'}]}


if __name__ == '__main__':
    run(app, host='localhost', port=8080)
