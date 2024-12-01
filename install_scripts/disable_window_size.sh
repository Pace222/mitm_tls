#!/bin/bash
ABSPATH=$(cd "$(dirname "$0")"; pwd -P)
dns_server=$(head -n 1 "$ABSPATH/old_window_size.txt")
thumbprint="642F01402DD64234431026199BF3C9CAECFB4239"

sudo networksetup -setdnsservers Wi-Fi "$dns_server"

sudo security delete-certificate -Z $thumbprint /Library/Keychains/System.keychain
