document.addEventListener('DOMContentLoaded', () => {
const crawlButton = document.getElementById('crawl-button');
const searchButton = document.getElementById('search-button');
const urlInput = document.getElementById('url');
const queryInput = document.getElementById('query');
const apiKeyInput = document.getElementById('api_key');
const resultsDiv = document.getElementById('results');
const statusBox = document.getElementById('status-box');
const statusText = document.getElementById('status-text');

let api_key = localStorage.getItem("api_key");
if (api_key !== null) {
    apiKeyInput.value = api_key;
}

apiKeyInput.addEventListener('input', () => {
    localStorage.setItem('api_key', apiKeyInput.value);
});

// Disable the search query input initially
queryInput.value = '';

crawlButton.addEventListener('click', async () => {
    const url = urlInput.value;
    if (!url) return;

    // Call the crawl function here and wait for it to finish
    urlInput.disabled = true;
    crawlButton.disabled = true;
    const waitCursorStyle = document.createElement('style');
    waitCursorStyle.innerHTML = `* { cursor: wait !important; }`;
    document.head.appendChild(waitCursorStyle);
    statusBox.classList.remove('hidden');
    statusText.textContent = 'Crawling...';
    await crawl(url);

    // Enable the search query input after crawling is done
    statusBox.classList.add('hidden');
    document.head.removeChild(waitCursorStyle);
    queryInput.disabled = false;
    urlInput.disabled = false;
    crawlButton.disabled = false;
    searchButton.disabled = false;
});

searchButton.addEventListener('click', async () => {
        const query = queryInput.value;
        if (!query) return;

        // Call the search function here
        const searchResults = await search(query);

        // Display the search results
        displayResults(searchResults, resultsDiv);
    });
});

// Add your `crawl` and `search` functions here
async function crawl(url) {
    try {
        const response = await fetch('/crawl', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `url=${encodeURIComponent(url)}`,
        });

        if (!response.ok) {
            throw new Error('Crawl failed');
        }

        const data = await response.json();
        alert(data.message);
        console.log(data.message);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function search(query) {
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `query=${encodeURIComponent(query)}`,
        });

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const data = await response.json();
        return data.results;
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

const websocket = new WebSocket('ws://localhost:8080/websocket');
console.log('connected to websocket');

websocket.onopen = (event) => {
    console.log('WebSocket is open now.');
};

websocket.onclose = (event) => {
    console.log('WebSocket is closed now.');
};

websocket.onerror = (event) => {
    console.error('WebSocket error observed:', event);
};

websocket.onmessage = (event) => {
    let statusText = document.getElementById('status-text');
    statusText.textContent = event.data;
};

function displayResults(results, resultsDiv) {
    // Your display implementation
    alert('TODO: display results');
}