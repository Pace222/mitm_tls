import socket
from subprocess import check_call, DEVNULL, STDOUT

from dnslib import DNSRecord, DNSHeader, QTYPE, RR, A

import proxy
import translating_server
from utils import Startable, Colors


class DNSServer(Startable):
    def __init__(self, response_ip: str, translator: translating_server.TranslatingServer, quiet: bool, verbose: bool):
        super().__init__(self.handle_requests)
        self.response_ip = response_ip
        self.dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns_socket.bind(("0.0.0.0", 53))

        self.quiet = quiet
        self.verbose = verbose

        self.translator = translator

    def handle_requests(self):
        if self.verbose:
            print(f"[{Colors.CYAN}*{Colors.END}] Accepting DNS requests")
        with self.dns_socket:
            while True:
                data, addr = self.dns_socket.recvfrom(1024)

                dns_request = DNSRecord.parse(data)

                if dns_request.q.qtype == QTYPE.A or dns_request.q.qtype == QTYPE.AAAA:
                    target_domain = str(dns_request.q.qname)[:-1]
                    if self.verbose:
                        print(f"[{Colors.CYAN}*{Colors.END}] Received {Colors.GREEN}DNS{Colors.END} request from {addr} for {Colors.GREEN}{target_domain}{Colors.END}")

                    if target_domain not in self.translator.domains_to_ports:
                        org = '.'.join(target_domain.split('.')[-2:-1]).capitalize()
                        check_call(['./gen_cert.sh', target_domain, org], stdout=DEVNULL, stderr=STDOUT)

                        self.translator.domains_to_certs[target_domain] = (f'./certs/{target_domain}_chain.pem', f'./certs/{target_domain}.key')

                        new_proxy = proxy.Proxy(target_domain, self.quiet, self.verbose)
                        self.translator.domains_to_ports[target_domain] = new_proxy.proxy_port
                        new_proxy.start()

                    dns_response = DNSRecord(
                        DNSHeader(id=dns_request.header.id, qr=1, aa=1, ra=1),
                        q=dns_request.q,
                        a=RR(dns_request.q.qname, rtype=QTYPE.A, rdata=A(self.response_ip)),
                    )
                    self.dns_socket.sendto(dns_response.pack(), addr)

