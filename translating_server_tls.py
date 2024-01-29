import errno
import socket
import threading
import time
from typing import Tuple

import proxy_tls as proxy
from utils import Startable, Colors

import ssl

class TranslatingServer(Startable):
    def __init__(self, port: int, proxy_port: int, certs_files: Tuple[str, str], quiet: bool, verbose: bool):
        super().__init__(self.handle_translations, proxy_port)
        self.port = port
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(*certs_files)
        self.translating_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.translating_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.translating_socket.bind(("0.0.0.0", self.port))

        self.translating_socket.listen(100)

        self.quiet = quiet
        self.verbose = verbose

        self.stop = False
        self.client_handler = None

    def handle_translations(self, proxy_port: int):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting requests on port {self.port}, relaying to {proxy_port}")
        with self.context.wrap_socket(self.translating_socket, server_side=True) as ssock:
            ssock.settimeout(0.2)
            while not self.stop:
                if self.client_handler is not None:
                    self.client_handler.join()
                try:
                    client_socket, client_address = ssock.accept()
                except socket.timeout:
                    continue
                if self.verbose:
                    print(f'Connection on port {self.port} from {client_address}')

                dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dest_socket.connect(('127.0.0.1', proxy_port))

                self.client_handler = threading.Thread(target=proxy.forward_data, args=(client_socket, dest_socket, True,
                                                                                   self.quiet, self.verbose))
                self.client_handler.start()

    def terminate(self):
        self.stop = True
        if self.client_handler is not None:
            self.client_handler.join()
        super().join()
        self.translating_socket.close()

