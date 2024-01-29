import socket
import threading

import dns_server
import proxy
from utils import Startable, Colors


class TranslatingServer(Startable):
    def __init__(self, port: int, dns_server: dns_server.DNSServer, quiet: bool, verbose: bool):
        super().__init__(self.handle_translations, dns_server)
        self.port = port
        self.translating_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.translating_socket.bind(("0.0.0.0", self.port))
        self.translating_socket.listen(100)

        self.quiet = quiet
        self.verbose = verbose

    def handle_translations(self, dns_server: dns_server.DNSServer):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting requests on port {self.port}")
        with self.translating_socket:
            while True:
                client_socket, client_address = self.translating_socket.accept()
                if self.verbose:
                    print(f'Connection on port {self.port} from {client_address}')

                dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dest_socket.connect(('127.0.0.1', dns_server.domains_to_ports[dns_server.client_ips_to_domains[client_address[0]]]))

                client_handler = threading.Thread(target=proxy. forward_data, args=(client_socket, dest_socket, True,
                                                                                   self.quiet, self.verbose))
                client_handler.start()

