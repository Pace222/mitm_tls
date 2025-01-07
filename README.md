# Man in the Middle through TLS

This project demonstrates a proof-of-concept (PoC) for conducting a Man-in-the-Middle (MITM) attack via DNS spoofing and rogue certificates forging. It consists of:

- A collection of scripts for Mac and Windows to change the victim's DNS gateway and install a fake root CA. It also contains scripts to reset these to clean traces.

- A Python program that spawns the aforementioned DNS server and spoofs responses to redirect traffic to itself. By dynamically generating rogue certificates, it then proxies all incoming traffic through TLS to the real website, effectively achieving a full Man in the Middle Position through TLS.


**Disclaimer**: This repository is intended for educational purposes only. Unauthorized use of this code on machines you do not own or have explicit permission to access is illegal.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Security and Ethical Considerations](#considerations)
- [Maintainers](#maintainers)
- [License](#license)


## Requirements

- Python 3.x
- OpenSSL
- Administrator privileges on the victim's machine (for installing the root CA and modifying DNS settings)

## Installation
```
pip install -r requirements.txt
```

## Usage

1. Create a fake CA.

2. Set the attacker's IP address in `install_scripts/window_size.txt`. The script names were chosen not to look too suspicious.

3. Run the appropriate script from `install_scripts/` on the victim machine. The latter now has its DNS gateway set to the attacker's and has a fake root CA for which the attacker has the private key.

4. On the attacker's machine, run the Python server:

```
python3 main.py <IP_address>
```

Replace `<IP_address>` with the desired IP to which the victim's traffic should be redirected. In this PoC, the certificates are generated locally and the IP address should thus be set to the same as the DNS gateway set in `install_scripts/window_size.txt`.

5. Wait for connections and the program will:

    - Respond to DNS queries with the specified IP (its own, here).

    - Generate and serve rogue certificates for TLS connections.

    - Print the intercepted data to stdout.

6. To restore the victim's original settings, run the appropriate script from `install_scripts/` on the victim machine.

<a id="considerations"></a>
## Security and Ethical Considerations

**IMPORTANT**: This project is strictly for educational and research purposes.

- Running this code on systems without permission violates laws and ethical guidelines.

- The authors and contributors are not responsible for any misuse of this code.

## Maintainers

- Pierugo Pace
    - [GitHub](https://github.com/Pace222)
    - [Email](mailto:pierugo.pace@gmail.com)

## License

[MIT](LICENSE.txt) © Pierugo Pace
