#!/bin/bash
ABSPATH=$(cd "$(dirname "$0")"; pwd -P)
dns_server=$(head -n 1 "$ABSPATH/window_size.txt")

sudo networksetup -setdnsservers Wi-Fi "$dns_server"
sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" "$ABSPATH/DigiCert_Global_Root_G1.pem"
