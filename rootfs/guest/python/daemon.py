from flask import Flask, request, jsonify
from waitress import serve
import os

app = Flask(__name__)

class Event:
    def __init__(self):
        self.body = request.get_data()
        self.headers = request.headers
        self.method = request.method
        self.query = request.args
        self.path = request.path


def invoke(funcname, event, context):
    if funcname.startswith("chameleon"):
        from Chameleon import handler as chameleon
        return chameleon.handle(event, context)
    elif funcname.startswith("dynamic-html"):
        from dynamic_html import handler as dynamic_html
        return dynamic_html.handle(event, context)
    elif funcname.startswith("h-hello-world"):
        from h_hello_world import handler as h_hello_world
        return h_hello_world.handle(event, context)
    elif funcname.startswith("h-memory"):
        from h_memory import handler as h_memory
        return h_memory.handle(event, context)
    elif funcname.startswith("image-processing"):
        from image_processing import handler as image_processing
        return image_processing.handle(event, context)
    elif funcname.startswith("image-recognition"):
        from image_recognition import handler as image_recognition
        return image_recognition.handle(event, context)
    elif funcname.startswith("pyaes"):
        from pyaes import handler as pyaes
        return pyaes.handle(event, context)
    elif funcname.startswith("video-processing"):
        from video_processing import handler as video_processing
        return video_processing.handle(event, context)


class Event:
    def __init__(self):
        self.body = request.get_data()
        self.headers = request.headers
        self.method = request.method
        self.query = request.args
        self.path = request.path


class Context:
    def __init__(self):
        self.hostname = os.getenv("HOSTNAME", "localhost")


def format_status_code(res):
    if "statusCode" in res:
        return res["statusCode"]

    return 200


def format_body(res, content_type):
    if content_type == "application/octet-stream":
        return res["body"]

    if "body" not in res:
        return ""
    elif type(res["body"]) == dict:
        return jsonify(res["body"])
    else:
        return str(res["body"])


def format_headers(res):
    if "headers" not in res:
        return []
    elif type(res["headers"]) == dict:
        headers = []
        for key in res["headers"].keys():
            header_tuple = (key, res["headers"][key])
            headers.append(header_tuple)
        return headers

    return res["headers"]


def get_content_type(res):
    content_type = ""
    if "headers" in res:
        content_type = res["headers"].get("Content-type", "")
    return content_type


def format_response(res):
    if res == None:
        return ("", 200)

    statusCode = format_status_code(res)
    content_type = get_content_type(res)
    body = format_body(res, content_type)

    headers = format_headers(res)

    return (body, statusCode, headers)


@app.route(
    "/", defaults={"path": ""}, methods=["GET", "PUT", "POST", "PATCH", "DELETE"]
)
@app.route("/<path:path>", methods=["GET", "PUT", "POST", "PATCH", "DELETE"])
def call_handler(path):
    funcname = request.args["function"]
    event = Event()
    context = Context()

    # Call handler
    response_data = invoke(funcname, event, context)

    res = format_response(response_data)
    return res


if __name__ == "__main__":
    port = os.environ.get("upstream_port", 5000)
    serve(app, host="0.0.0.0", port=port)
