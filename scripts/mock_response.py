"""Return a mock/static response instead of forwarding to the server."""
from mitmproxy import ctx, http

MOCK_RESPONSE = {
    "status": 200,
    "headers": {"Content-Type": "application/json; charset=utf-8"},
    "body": '{"status":"ok","message":"this is a mock response"}',
}


def request(flow):
    ctx.log.info(f"[MOCK] Mocking response for: {flow.request.pretty_url}")
    flow.response = http.Response.make(
        MOCK_RESPONSE["status"],
        MOCK_RESPONSE["body"].encode("utf-8"),
        MOCK_RESPONSE["headers"],
    )


def response(flow):
    pass
