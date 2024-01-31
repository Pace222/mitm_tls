import errno
import socket
import ssl
import threading
import time

from dns import resolver

from utils import Startable, Colors


class Proxy(Startable):
    def __init__(self, target_domain: str, quiet: bool, verbose: bool):
        super().__init__(self.handle_new_connections)
        self.res = resolver.Resolver()
        self.res.cache = resolver.Cache()
        self.res.nameservers = ['8.8.8.8']  # TODO: remove after local testing

        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy.bind(('127.0.0.1', 0))
        self.proxy.listen(100)
        self.proxy_port = self.proxy.getsockname()[1]
        self.target_domain = target_domain

        self.quiet = quiet
        self.verbose = verbose

        self.context = ssl.create_default_context()

    def handle_new_connections(self):
        if self.verbose:
            print(f'[{Colors.CYAN}*{Colors.END}] {Colors.CYAN}Proxy started{Colors.END} for {Colors.GREEN}{self.target_domain}{Colors.END} listening on port {self.proxy_port}...')

        try:
            with self.proxy:
                while True:
                    src_socket, src_address = self.proxy.accept()
                    if self.verbose:
                        print(f'Connection on {self.proxy_port} from {src_address}')

                    dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    dest_socket.connect((self.res.resolve(self.target_domain)[0].address, 443))
                    ssock = self.context.wrap_socket(dest_socket, server_hostname=self.target_domain)

                    client_handler = threading.Thread(target=forward_data, args=(src_socket, ssock, False, self.quiet, self.verbose, self.target_domain))
                    client_handler.start()
        except socket.error as e:
            print(f"{Colors.FAIL}{e}{Colors.END}")
            print(f"Restarting proxy {self.proxy_port}")
            self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.proxy.bind(('127.0.0.1', self.proxy_port))
            self.proxy.listen(100)
            self.handle_new_connections()

def forward_data(src_socket: socket.socket, dest_socket: socket.socket, http_proxy: bool, quiet: bool, verbose: bool, domain: str = ""):
    with src_socket, dest_socket:
        src_socket.setblocking(False)
        dest_socket.setblocking(False)

        src = src_socket.getpeername()
        if not quiet:
            if http_proxy:
                print(f"{Colors.BOLD}{Colors.GREEN}************** {src} >>> ", end="")
            else:
                print(f"{Colors.BOLD}{Colors.GREEN}{domain} opened **************{Colors.END}\n")

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

                            if not quiet and not http_proxy:
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
            if http_proxy:
                print(f"{Colors.BOLD}{Colors.FAIL}************** {src} >>> ", end="")
            else:
                print(f"{Colors.BOLD}{Colors.FAIL}{domain} closed **************{Colors.END}\n")
