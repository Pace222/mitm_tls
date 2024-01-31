import sys

import dns_server
import proxy

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 main <REDIRECTION_IP>")
        sys.exit(1)

    # TODO: enable verbose/quiet output
    quiet = False
    verbose = True

    proxy_serv = proxy.Proxy(443, quiet, verbose)
    dns_serv = dns_server.DNSServer(sys.argv[1], proxy_serv, quiet, verbose)

    proxy_serv.start()
    dns_serv.start()

    proxy_serv.join()
    dns_serv.join()
