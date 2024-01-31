import socket
import threading
from typing import Tuple, Dict

import proxy as proxy
from utils import Startable, Colors

import ssl

class TranslatingServer(Startable):
    def __init__(self, listening_port: int, use_tls: bool, quiet: bool, verbose: bool):
        super().__init__(self.handle_translations, use_tls)
        self.port = listening_port
        self.domains_to_ports: Dict[str, int] = {}
        self.domains_to_certs: Dict[str, Tuple[str, str]] = {}
        self.connection_to_port: Dict[socket.socket, int] = {}

        self.translating_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.translating_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.translating_socket.bind(("0.0.0.0", self.port))
        self.translating_socket.listen(100)

        if use_tls:
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.context.sni_callback = self.sni_callback
            self.translating_socket = self.context.wrap_socket(self.translating_socket, server_side=True)

        self.quiet = quiet
        self.verbose = verbose

    def sni_callback(self, ssl_socket: ssl.SSLSocket, sni_name: str, ssl_context: ssl.SSLContext) -> None:
        new_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        self.connection_to_port[ssl_socket] = self.domains_to_ports[sni_name]
        certfile, keyfile = self.domains_to_certs[sni_name]
        new_context.load_cert_chain(certfile, keyfile)
        ssl_socket.context = new_context
        return None

    def handle_translations(self, use_tls: bool):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting requests on port {self.port}")
        try:
            with self.translating_socket:
                while True:
                    client_socket, client_address = self.translating_socket.accept()

                    if self.verbose:
                        print(f'Connection on port {self.port} from {client_address}')

                    dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    dest_socket.connect(('127.0.0.1', self.connection_to_port[client_socket]))
                    # TODO: find a way to get the correct port when plain HTTP
                    self.connection_to_port.pop(client_socket, None)

                    client_handler = threading.Thread(target=proxy.forward_data, args=(client_socket, dest_socket, True,
                                                                                       self.quiet, self.verbose))
                    client_handler.start()
        except socket.error as e:
            print(f"{Colors.FAIL}{e}{Colors.END}")
            print(f"Restarting relay")
            self.translating_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.translating_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.translating_socket.bind(("0.0.0.0", self.port))
            self.translating_socket.listen(100)
            if use_tls:
                self.translating_socket = self.context.wrap_socket(self.translating_socket, server_side=True)
            self.handle_translations(use_tls)
