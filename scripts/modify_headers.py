"""Add, modify, or remove request and response headers."""
from mitmproxy import ctx

# Headers to add/modify on requests
REQUEST_HEADERS = {
    "X-Custom-Header": "my-value",
    "Authorization": "Bearer token",
}

# Headers to remove from requests
REMOVE_REQUEST_HEADERS = [
    # "X-Unwanted-Header",
]

# Headers to add/modify on responses
RESPONSE_HEADERS = {
    # "X-Server": "mitmproxy",
    # "Access-Control-Allow-Origin": "*",
}

# Headers to remove from responses
REMOVE_RESPONSE_HEADERS = [
    # "X-Powered-By",
    # "Server",
]


def request(flow):
    for key, value in REQUEST_HEADERS.items():
        flow.request.headers[key] = value
    for key in REMOVE_REQUEST_HEADERS:
        if key in flow.request.headers:
            del flow.request.headers[key]


def response(flow):
    for key, value in RESPONSE_HEADERS.items():
        flow.response.headers[key] = value
    for key in REMOVE_RESPONSE_HEADERS:
        if key in flow.response.headers:
            del flow.response.headers[key]
