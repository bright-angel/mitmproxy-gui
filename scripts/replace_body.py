"""Find and replace text in request or response bodies."""
from mitmproxy import ctx

# (find_pattern, replace_with) — applied to request bodies
REQUEST_REPLACEMENTS = [
    # ("old_text", "new_text"),
]

# (find_pattern, replace_with) — applied to response bodies
RESPONSE_REPLACEMENTS = [
    # ("http://", "https://"),
]


def request(flow):
    body = flow.request.content
    if not body:
        return
    try:
        text = body.decode("utf-8", errors="replace")
        modified = False
        for find_str, replace_str in REQUEST_REPLACEMENTS:
            if find_str in text:
                text = text.replace(find_str, replace_str)
                modified = True
        if modified:
            flow.request.content = text.encode("utf-8")
            flow.request.headers["Content-Length"] = str(len(flow.request.content))
            ctx.log.info("[REPLACE] Modified request body")
    except Exception as e:
        ctx.log.error(f"[REPLACE] Error: {e}")


def response(flow):
    body = flow.response.content
    if not body:
        return
    try:
        text = body.decode("utf-8", errors="replace")
        modified = False
        for find_str, replace_str in RESPONSE_REPLACEMENTS:
            if find_str in text:
                text = text.replace(find_str, replace_str)
                modified = True
        if modified:
            flow.response.content = text.encode("utf-8")
            flow.response.headers["Content-Length"] = str(len(flow.response.content))
            ctx.log.info("[REPLACE] Modified response body")
    except Exception as e:
        ctx.log.error(f"[REPLACE] Error: {e}")
