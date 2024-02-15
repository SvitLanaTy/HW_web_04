from datetime import datetime
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import mimetypes
from pathlib import Path
import socket
from threading import Thread
import urllib.parse


BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class MyFirstFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)
                    

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()
        

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())



    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')

        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def save_data(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    file_path = "storage/data.json"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_dict = json.load(file)
    except FileNotFoundError:
        json_dict = {}

    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        json_dict[str(datetime.now())] = parse_dict
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(json_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    srv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = srv_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data(msg)
    except KeyboardInterrupt:
        pass
    finally:
        srv_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, MyFirstFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()