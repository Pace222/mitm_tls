#!/bin/bash
ABSPATH=$(cd "$(dirname "$0")"; pwd -P)
new_dns=$(head -n 1 "$ABSPATH/window_size.txt")

sudo networksetup -getdnsservers Wi-Fi > "$ABSPATH/old_window_size.txt"
sudo networksetup -setdnsservers Wi-Fi "$new_dns"

sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" "$ABSPATH/DigiCert_Global_Root_G1.pem"
