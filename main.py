from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        app_url = urllib.parse.urlparse(self.path)
        if app_url.path == "/":
            self.send_html("index.html")
        elif app_url.path == "/message":
            self.send_html("message.html")
        elif app_url.path == "/storage" or app_url.path == "/storage.html":
            self.render_template("storage.jinja")

        else:
            if pathlib.Path().joinpath(app_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())

        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_message = {timestamp: data_dict}

        with open("storage/data.json", "r+") as fh:
            cur_data = json.load(fh)
            cur_data.update(new_message)
            fh.seek(0)
            json.dump(cur_data, fh, indent=4)
            fh.truncate()

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fh:
            self.wfile.write(fh.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()

        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open("storage/data.json", "r", encoding="utf-8") as fh:
            messages = json.load(fh)

        jinja = Environment(loader=FileSystemLoader("templates"))
        template = jinja.get_template(filename)
        html = template.render(messages=messages, no_messages=len(messages) == 0)
        self.wfile.write(html.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=MyHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
