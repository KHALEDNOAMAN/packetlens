# PacketLens - Network Analysis Guide

## Overview
A modern responsive network packet analyzer for capturing, inspecting, and troubleshooting traffic.

## Capture Modes
| Mode | Description |
|------|-------------|
| Live Capture | Real-time packet sniffing |
| File Import | Analyze .pcap files |
| Filtered | Capture with BPF filters |

## Protocol Support
| Layer | Protocols |
|-------|----------|
| Network | IPv4, IPv6, ARP, ICMP |
| Transport | TCP, UDP |
| Application | HTTP, DNS, DHCP, TLS |

## Common Filters
| Filter | Purpose |
|--------|---------|
| tcp.port == 80 | HTTP traffic |
| dns | DNS queries |
| ip.src == 10.0.0.1 | Source IP filter |
| tcp.flags.syn == 1 | SYN packets |

## Troubleshooting Workflows
- DNS resolution failures: filter DNS, check responses
- Slow connections: analyze TCP handshake timing
- Dropped packets: check retransmissions
- Security: inspect TLS versions, detect cleartext