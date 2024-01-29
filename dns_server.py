import socket
from typing import Dict

from dnslib import DNSRecord, DNSHeader, QTYPE, RR, A

import proxy
from utils import Startable, Colors


class DNSServer(Startable):
    def __init__(self, response_ip: str, quiet: bool, verbose: bool):
        super().__init__(self.handle_requests)
        self.response_ip = response_ip
        self.dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns_socket.bind(("0.0.0.0", 53))

        self.domains_to_ports: Dict[str, int] = {}
        self.client_ips_to_domains: Dict[str, str] = {}

        self.quiet = quiet
        self.verbose = verbose

    def handle_requests(self):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting DNS requests")
        with self.dns_socket:
            while True:
                data, addr = self.dns_socket.recvfrom(1024)

                if self.verbose:
                    print(f"[{Colors.CYAN}*{Colors.END}] Received {Colors.GREEN}DNS{Colors.END} request from {addr}")
                dns_request = DNSRecord.parse(data)

                if dns_request.q.qtype == QTYPE.A or dns_request.q.qtype == QTYPE.AAAA:
                    target_domain = str(dns_request.q.qname)
                    self.client_ips_to_domains[addr[0]] = target_domain

                    if target_domain not in self.domains_to_ports:
                        # TODO: generate certificate
                        new_proxy = proxy.Proxy(target_domain, self.quiet, self.verbose)
                        self.domains_to_ports[target_domain] = new_proxy.proxy_port
                        new_proxy.start()

                    dns_response = DNSRecord(
                        DNSHeader(id=dns_request.header.id, qr=1, aa=1, ra=1),
                        q=dns_request.q,
                        a=RR(dns_request.q.qname, rtype=QTYPE.A, rdata=A(self.response_ip)),
                    )
                    self.dns_socket.sendto(dns_response.pack(), addr)

