# PacketLens

A browser-based network packet analyzer. Created by [S4NTRX](https://github.com/S4NTRX).

Two files do everything:

- `index.html` is the whole interface. No build step, no dependencies, no external requests.
- `bridge.py` is optional. It serves the interface and streams live packets from `tcpdump`.

Only analyze networks you own or are authorized to monitor. Packets can contain passwords, cookies and private messages.

## Quick start

### A. Analyze a capture file (works everywhere)

1. Open browser.
2. Go to **Capture** in the sidebar and choose **Import PCAP / PCAPNG**.
3. Go to **Packets** to inspect, or **Dashboard** for statistics.

Files are parsed inside your browser tab and never uploaded. No file handy? Click **Load simulated demo**. Demo data is labeled SIMULATED in the header and is not real traffic.

### B. Capture live traffic (Kali, Ubuntu, Debian, macOS, rooted Termux)

1. Put `bridge.py` and `index.html` in the same folder.
2. Install tcpdump if missing: `sudo apt install tcpdump`
3. Run the bridge:

```
sudo python3 bridge.py
```

4. The terminal prints an address like `http://127.0.0.1:8787/#token=...`. Open it in a browser **on the same machine**.
5. The Capture page opens with the token filled in. Tick the authorization box and press **Start**.
6. Use **Pause / Resume** (key `p`) and **Stop** as needed. While paused, packets are skipped, not queued.

The bridge picks your default-route interface. To choose another: `python3 bridge.py --list` shows them, then `sudo python3 bridge.py -i eth0`. Add `-f "not port 22"` for a capture filter.

## Kali (or any Linux VM)

- **Browser inside the VM:** follow section B exactly.
- **Browser on the host machine:** `127.0.0.1` on the host is not the VM. Run `sudo python3 bridge.py --host 0.0.0.0`, then open `http://<vm-ip>:8787/` on the host (find the IP with `ip a`) and paste the token by hand. The stream is plain HTTP, so use a trusted network. In VirtualBox/VMware, use bridged or host-only networking so the host can reach the VM.
- **Avoid running as root:** grant tcpdump the capability once, then run the bridge as a normal user:
  `sudo setcap cap_net_raw,cap_net_admin=eip "$(command -v tcpdump)"`
- **VM traffic limits:** a NAT-mode VM only sees its own traffic. To see other devices you need bridged mode plus promiscuous mode, on a network you are authorized to monitor.

## Termux (Android)

- Without root, Android blocks raw sockets and live capture will fail. Use file import (section A).
- With root: `pkg install python tcpdump tsu`, copy both files to one folder, then `tsu` and `python3 bridge.py -i wlan0`. Open the printed address in the phone browser.


## Using the interface

| View | What it does |
| --- | --- |
| Dashboard | Totals, data volume, packets per second, TCP/UDP/DNS/ICMP counts, traffic chart, protocol bars, top sources, destinations and ports |
| Packets | Sortable, virtual-scrolled table. Click a row for the layer tree (Frame, Ethernet, IP, TCP/UDP, application) and a hex/ASCII dump |
| Capture | Import files, load demo data, start/pause/stop live capture |

**Filters** (Packets view). Combine terms with `&&`, `||` and `!`. Parentheses are not supported.

| Example | Meaning |
| --- | --- |
| `ip.addr==10.0.0.5` | Source or destination is that address |
| `ip.src==1.1.1.1`, `ip.dst==...` | One direction |
| `port==443`, `tcp.port==22`, `udp.port==53` | Either port matches |
| `frame.len>1000` | Also `<`, `>=`, `<=`, `!=` |
| `tcp.flags.syn && !tcp.flags.ack` | Flags: fin, syn, rst, psh, ack, urg |
| `dns`, `tls`, `http`, `icmp`, `arp`, `tcp`, `udp` | Protocol |
| `example.com` | Any other text searches addresses, protocol and info |

An invalid filter shows a message and keeps the previous results.

**Export:** *Export CSV* and *Export report* (JSON with summary and packets) both respect the current filter.

**Shortcuts:** `/` focus filter, `1` `2` `3` switch views, `Up`/`Down` move selection, `p` pause/resume, `Esc` leave the filter box.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Bridge exits immediately with an argparse error | Fixed: `-i` is now optional. Update `bridge.py` |
| `tcpdump not found` | `sudo apt install tcpdump` |
| `Cannot listen on ...` | Port busy. Use `-p 8800` |
| UI says tcpdump exited with code 1 | Run with `sudo`, or fix the interface name (`--list`) |
| Start button stays disabled | Paste the token and tick the authorization box |
| "Bridge rejected the token" | The token changes on every bridge start. Use the new one |
| Connected but no packets | Wrong interface, or an idle one. Generate traffic with `ping 1.1.1.1` |
| `any` interface shows odd results | Supported (Linux cooked v1 and v2). Prefer a specific interface |
| Import says "Not a PCAP or PCAPNG capture" | Re-save from Wireshark as pcap or pcapng. Compressed `.gz` is not supported |

## Security notes

- The bridge listens on `127.0.0.1` by default and requires a random token for `/stream`.
- The page's content security policy blocks every network request except to its own origin and localhost, so a bug cannot send your captures elsewhere.
- Only the first 256 bytes of each packet are kept in memory. Nothing is written to disk or sent to third parties.
- `--host 0.0.0.0` exposes the bridge to your network. The token protects it, but traffic is not encrypted.

## Limits

- Hand-written parser: Ethernet, Linux cooked (v1, v2), raw IP; IPv4, IPv6, ARP, TCP, UDP, ICMP. DNS, HTTP and TLS are detected by port or signature. No IPv6 extension headers, no fragment reassembly, no TLS decryption.
- PCAPNG: section, interface and enhanced packet blocks; timestamps assume microsecond resolution.
- The viewer holds up to 250,000 packets. Later ones count as viewer-dropped in the status bar.
- Not built: saved and compared sessions, PCAP re-export (packets are truncated), dedicated Reports and Settings pages.
