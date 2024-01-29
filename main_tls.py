import sys

import dns_server_tls as dns_server

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 main <REDIRECTION_IP>")
        sys.exit(1)

    # TODO: enable verbose/quiet output
    quiet = False
    verbose = True

    dns_serv = dns_server.DNSServer(sys.argv[1], quiet, verbose)
    dns_serv.start()

    dns_serv.join()
