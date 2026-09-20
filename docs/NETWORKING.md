# Networking, DNS, and exit-node coexistence

## Deployed topology

- Pi 5: `100.78.140.101` / `fd7a:115c:a1e0::5901:8c9c`
- Mac: `100.122.163.78`
- iPhone 14 Pro: `100.123.14.68`

Four Tailscale restricted DNS suffixes point to the Pi 5 and have **Use with exit node** enabled:

- `weatherkit.apple.com`
- `tthr.apple.com`
- `tether.edge.apple`
- `tether.v.aaplimg.com`

Existing global nameservers on the Pi 5, A1-JP (`100.91.87.20`), A1-US (`100.116.187.43`), and the `ts.net` split configuration remain in place.

The Pi 5 advertises and the control plane approves:

```text
17.253.0.0/16
2403:300:a00::/40
2620:149:a00::/40
2a01:b740:a00::/40
```

The existing LAN route `192.168.31.0/24` and exit-node advertisements `0.0.0.0/0`, `::/0` are unchanged. Normal traffic follows the device's selected exit or local network, while the relay prefixes and tailnet connection remain split through the Pi 5.

Destination-prefix routing can also carry unrelated Apple traffic that shares an address. Other tailnet devices accepting those routes may use the Pi 5. QUIC rejection is limited to enrolled CWA client addresses, and TLS interception is limited to WeatherKit.

## Client opt-in

`bridgectl.py` backs up AdGuard YAML, manages only marked rules, and preserves unrelated configuration. Dual-stack selectors come from the Tailscale peer list.

- WeatherKit A records return the Pi 5; AAAA/HTTPS queries are answered empty for enrolled clients to prevent bypass.
- Three relay domains are blocked for enrolled clients; relay-specific routes and nftables cover cached or literal relay addresses.
- macOS PAC and explicit system HTTP/HTTPS proxies remain off. Port 18940 is test-only.
- Certificate installation and full trust are separate steps. Enable a client only after trust is complete.

The Mac, iPhone, and paired Watch have real successful HTTPS/translation evidence.

## QUIC and IPv6 fallback

The Pi 5 `inet cwa_weather` table rejects enrolled clients' UDP/443 traffic to selected Pi 5/relay destinations so TCP can win. IPv6 relay UDP is handled in prerouting before a missing public IPv6 route causes a delay.

IPv6 TCP/443 is reset only when `fib daddr oif missing`; other TCP traffic is preserved. The rule naturally stops matching if the Pi 5 gains a usable route. An isolated UDP burst timeout was not conclusively diagnosed and may reflect ICMP rate limiting or transient loss.

## Reading status correctly

`split_routes.py status` reports advertisement, exact approval, DNS snapshot, and IPv6 availability separately. Approval of a default route does not prove approval of a specific prefix. `config/exit-dns-compatibility.json` records the saved exit-DNS flags and explicitly states `liveFlagMonitoring=false`.

`RouteAll=true` means subnet routes are accepted. Use `ExitNodeID` or `ExitNodeIP` to identify the selected exit node.

## Validation

After changing exit mode, verify the system resolver, `100.100.100.100`, public egress, Pi 5 route state, and a new native city request. Relaunching Weather can hit cache; a short period without a response is not by itself a failure. Preserve server proof with aligned timestamps.

Back up and restore client preferences around a test. The unhealthy `jarvis` host is excluded. iPhone behavior under every exit and network transition still requires device-specific evidence.

References: [Tailscale DNS](https://tailscale.com/docs/reference/dns-in-tailscale), [route injection](https://tailscale.com/docs/reference/route-injection), and [nftables](https://www.netfilter.org/projects/nftables/manpage.html).
