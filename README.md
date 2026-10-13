# PacketLens

`index.html` is the whole UI (no build step, no external requests). `bridge.py` is the optional live-capture service.


Offline analysis (Capture > Import PCAP/PCAPNG) works anywhere. Files are parsed in the tab and never uploaded.

## Live capture

The bridge streams `tcpdump` output to the browser over `127.0.0.1`, protected by a one-time token.

```
python3 bridge.py -i eth0            # optional: -f "not port 22" -s 256
```

Paste the printed token into Capture, tick the authorization box, press Start.

**Desktop (Linux):** avoid running Python as root. Grant tcpdump the capability once instead:
`sudo setcap cap_net_raw,cap_net_admin=eip "$(command -v tcpdump)"`
**macOS:** `sudo python3 bridge.py -i en0` (root needed for BPF devices).
**Windows:** use Wireshark/dumpcap to record a file, then import it.
**Termux:** `pkg install python tcpdump`, then run the bridge as root (`tsu`). Without root, Android blocks raw sockets and capture will fail; use file import.

Safari may block an HTTPS page from calling `http://127.0.0.1`. Serve the UI locally in that case.

## Limits

- Parser is hand-written: Ethernet, Linux cooked, raw IP; IPv4/IPv6, ARP, TCP, UDP, ICMP; DNS, HTTP and TLS detected by port/signature. No IPv6 extension headers, no fragment reassembly, no TLS decryption.
- PCAPNG: SHB, IDB, EPB blocks; timestamps assume microsecond resolution.
- Only the first 256 bytes of each packet are kept (privacy), so PCAP re-export is not offered. CSV and JSON report export are.
- Viewer holds at most 250,000 packets; later ones are counted as viewer-dropped.
- Filters: `ip.addr ip.src ip.dst port tcp.port udp.port frame.len tcp.flags.<flag>`, protocol names, free text, `!`, `&&`, `||` (no parentheses).
- Demo data is synthetic, labeled SIMULATED in the header, and has no raw bytes.
- Not built: saved/compared sessions, dedicated Reports and Settings pages.
