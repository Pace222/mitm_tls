import sys

import dns_server
import translating_server

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 main <REDIRECTION_IP>")
        sys.exit(1)

    # TODO: enable verbose/quiet output
    quiet = False
    verbose = True

    trans_serv = translating_server.TranslatingServer(443, quiet, verbose)
    dns_serv = dns_server.DNSServer(sys.argv[1], trans_serv, quiet, verbose)

    trans_serv.start()
    dns_serv.start()

    trans_serv.join()
    dns_serv.join()
