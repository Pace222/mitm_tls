import socket
import threading
from typing import Tuple, Dict

from utils import Startable, Colors

from dns import resolver
import ssl


class Proxy(Startable):
    # TODO: enum with different possible ports (80 and 443 for now)

    def __init__(self, listening_port: int, quiet: bool, verbose: bool):
        super().__init__(self.handle_connections)
        self.port = listening_port
        self.domains_to_certs: Dict[str, Tuple[str, str]] = {}
        self.connection_to_domain: Dict[socket.socket, str] = {}

        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy_socket.bind(("0.0.0.0", self.port))
        self.proxy_socket.listen(100)

        if self.port == 443:
            self.server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.server_context.sni_callback = self.sni_callback
            self.proxy_socket = self.server_context.wrap_socket(self.proxy_socket, server_side=True)
            self.client_context = ssl.create_default_context()

        self.res = resolver.Resolver()
        self.res.cache = resolver.Cache()
        self.res.nameservers = ['8.8.8.8']  # TODO: remove after local testing

        self.quiet = quiet
        self.verbose = verbose

    def sni_callback(self, ssl_socket: ssl.SSLSocket, sni_name: str, ssl_context: ssl.SSLContext) -> None:
        new_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        self.connection_to_domain[ssl_socket] = sni_name
        certfile, keyfile = self.domains_to_certs[sni_name]
        new_context.load_cert_chain(certfile, keyfile)
        ssl_socket.context = new_context
        return None

    def handle_connections(self):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting requests on port {self.port}")
        try:
            with self.proxy_socket:
                while True:
                    client_socket, client_address = self.proxy_socket.accept()
                    if self.verbose:
                        print(f'Connection on port {self.port} from {client_address}')

                    self.handle_client(client_socket)
        except socket.error as e:
            print(f"{Colors.FAIL}{e}{Colors.END}")
            print(f"Restarting relay {self.port}")
            self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.proxy_socket.bind(("0.0.0.0", self.port))
            self.proxy_socket.listen(100)
            if self.port == 443:
                self.proxy_socket = self.server_context.wrap_socket(self.proxy_socket, server_side=True)
            self.handle_connections()

    def handle_client(self, client_socket: socket.socket):
        if self.port == 443:
            domain = self.connection_to_domain.pop(client_socket)
            dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest_socket.connect((self.res.resolve(domain)[0].address, 443))
            dest_socket = self.client_context.wrap_socket(dest_socket, server_hostname=domain)

            s = threading.Thread(target=self.forward, args=(client_socket, dest_socket, domain, True))
            r = threading.Thread(target=self.forward, args=(dest_socket, client_socket, domain, False))

            s.start()
            r.start()
        elif self.port == 80:
            # TODO: find a way to get the correct port when plain HTTP
            raise "HTTP port not yet implemented"
        else:
            raise "Proxy port not yet implemented"

    def forward(self, src_socket: socket.socket, dest_socket: socket.socket, domain: str, direction: bool):
        with src_socket, dest_socket:
            src = src_socket.getpeername()

            if not self.quiet and direction:
                print(f"{Colors.BOLD}{Colors.GREEN}************** {src} >>> {domain} opened **************{Colors.END}\n")

            while True:
                try:
                    data = src_socket.recv(4096)
                    if len(data) == 0:
                        break

                    if not self.quiet:
                        if direction:
                            print(f"{Colors.GREEN}>>> [{domain}]: {Colors.END}", end="")
                        else:
                            print(f"{Colors.BLUE}<<< [{domain}]: {Colors.END}", end="")
                        print(data)

                    dest_socket.send(data)
                except Exception as e:
                    print(f"{Colors.FAIL}{e}{Colors.END}")
                    break

            if not self.quiet and direction:
                print(f"{Colors.BOLD}{Colors.FAIL}************** {src} >>> {domain} closed **************{Colors.END}\n")
