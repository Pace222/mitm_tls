import errno
import socket
import threading
import time
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

                    if self.port == 443:
                        target_domain = self.connection_to_domain.pop(client_socket)
                        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        dest_socket.connect((self.res.resolve(target_domain)[0].address, 443))
                        dest_socket = self.client_context.wrap_socket(dest_socket, server_hostname=target_domain)
                    elif self.port == 80:
                        # TODO: find a way to get the correct port when plain HTTP
                        raise "HTTP port not yet implemented"
                    else:
                        raise "Proxy port not yet implemented"

                    client_handler = threading.Thread(target=forward_data, args=(
                    client_socket, dest_socket, self.quiet, self.verbose, target_domain))
                    client_handler.start()
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


def forward_data(src_socket: socket.socket, dest_socket: socket.socket, quiet: bool, verbose: bool, domain: str = ""):
    with src_socket, dest_socket:
        src_socket.setblocking(False)
        dest_socket.setblocking(False)

        src = src_socket.getpeername()
        if not quiet:
            print(f"{Colors.BOLD}{Colors.GREEN}************** {src} >>> {domain} opened **************{Colors.END}\n")

        st = time.time()
        timeout = False
        color = Colors.GREEN
        arrows = ">>>"
        while not timeout:
            try:
                while True:
                    try:
                        data = src_socket.recv(4096)
                        if len(data) > 0:
                            st = time.time()

                            if not quiet:
                                print(f"{color}{arrows} [{domain}]: {Colors.END}", end="")
                                print(data)

                            dest_socket.send(data)
                        else:
                            if time.time() - st > 5:
                                timeout = True
                            break
                    except socket.error as e:
                        if e.errno == errno.EAGAIN or e.errno == errno.ENOENT:
                            if time.time() - st > 5:
                                timeout = True
                            break
                        raise e

                tmp = src_socket
                src_socket = dest_socket
                dest_socket = tmp
                color = Colors.GREEN if color == Colors.BLUE else Colors.BLUE
                arrows = "<<<" if arrows == ">>>" else ">>>"

            except socket.error as e:
                print(f"{Colors.FAIL}{e}{Colors.END}")
                print(f"{e.errno}")
                break

        if not quiet:
            print(f"{Colors.BOLD}{Colors.FAIL}************** {src} >>> {domain} closed **************{Colors.END}\n")
