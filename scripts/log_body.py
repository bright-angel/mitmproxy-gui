"""Log full request and response bodies for debugging."""
from mitmproxy import ctx


def request(flow):
    url = flow.request.pretty_url
    method = flow.request.method
    body = flow.request.content
    ctx.log.info(f"[REQUEST] {method} {url}")
    ctx.log.info(f"[REQUEST] Headers: {dict(flow.request.headers)}")
    if body:
        try:
            text = body.decode("utf-8", errors="replace")
            if len(text) > 2000:
                text = text[:2000] + "...(truncated)"
            ctx.log.info(f"[REQUEST] Body: {text}")
        except Exception:
            ctx.log.info(f"[REQUEST] Body: {len(body)} bytes (binary)")


def response(flow):
    url = flow.request.pretty_url
    status = flow.response.status_code
    body = flow.response.content
    ctx.log.info(f"[RESPONSE] {status} {url}")
    ctx.log.info(f"[RESPONSE] Headers: {dict(flow.response.headers)}")
    if body:
        try:
            text = body.decode("utf-8", errors="replace")
            if len(text) > 2000:
                text = text[:2000] + "...(truncated)"
            ctx.log.info(f"[RESPONSE] Body: {text}")
        except Exception:
            ctx.log.info(f"[RESPONSE] Body: {len(body)} bytes (binary)")
