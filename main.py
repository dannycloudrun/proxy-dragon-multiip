from flask import Flask, request, Response
import requests
import os
import re

app = Flask(__name__)

# Extrae etiqueta completa: Cloud Run define IMAGE env
full_image = os.getenv("IMAGE", "") or os.getenv("K_REVISION", "")
ip_match = re.search(r":(\d{1,3}(?:\.\d{1,3}){3})$", full_image)
TARGET_IP = ip_match.group(1) if ip_match else None

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    if not TARGET_IP:
        return "IP no detectada.", 500

    url = f"http://{TARGET_IP}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        allow_redirects=False,
        timeout=15
    )
    return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
