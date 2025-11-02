import urllib.parse
import mimetypes
import pathlib
import json
from datetime import datetime
from typing import Type, Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader

STATIC_DIR = pathlib.Path("static")
TEMPLATES_DIR = pathlib.Path("templates")


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.send_read_page()
        else:
            static_file = STATIC_DIR / pr_url.path.lstrip("/")
            try:
                static_file = static_file.resolve()
                if STATIC_DIR.resolve() in static_file.parents and static_file.exists():
                    self.send_static(static_file)
                else:
                    self.send_html_file("error.html", status=404)
            except Exception:
                self.send_html_file("error.html", status=404)

    def do_POST(self):
        # Parse incoming data
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parsed: Dict[str, list[str]] = urllib.parse.parse_qs(data.decode())
        data_dict: Dict[str, str] = {
            key: values[0] for key, values in data_parsed.items() if values
        }

        # Ensure storage directory exists
        storage_dir = pathlib.Path("storage")
        storage_dir.mkdir(exist_ok=True)
        storage_file = storage_dir / "data.json"

        # Load existing data
        if storage_file.exists():
            with open(storage_file, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        else:
            all_data = {}

        # Add new message with timestamp
        timestamp = str(datetime.now())
        all_data[timestamp] = data_dict

        # Save updated data
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, file_name: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(file_name, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, file_path: pathlib.Path):
        self.send_response(200)
        mt = mimetypes.guess_type(str(file_path))
        if mt and mt[0]:
            self.send_header("Content-Type", mt[0])
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(file_path, "rb") as file:
            self.wfile.write(file.read())

    def send_read_page(self):
        # Load messages from storage/data.json
        storage_file = pathlib.Path("storage/data.json")
        if storage_file.exists():
            with open(storage_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
        else:
            messages = {}

        # Render Jinja2 template
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("read.html")
        rendered = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(rendered.encode("utf-8"))


def run(
    server_class: Type[HTTPServer] = HTTPServer,
    handler_class: Type[HttpHandler] = HttpHandler,
    port: int = 3000,
):
    server_address = ("", port)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
