#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 https://socks5-proxy.github.io/ 抓取免费代理，并生成 Clash 可用配置。

使用方法：
  python fetch_clash_proxies.py
  python fetch_clash_proxies.py -o clash.yaml
  python fetch_clash_proxies.py --url https://socks5-proxy.github.io/ -o clash.yaml
"""

import argparse
import html
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_URL = "https://socks5-proxy.github.io/"
DEFAULT_OUTPUT = "clash-free-proxies.yaml"
TEST_URL = "https://www.gstatic.com/generate_204"


def format_generated_time(now=None):
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S UTC")


COUNTRY_CODE = {
    "中国 香港": "HK",
    "香港": "HK",
    "荷兰": "NL",
    "南非": "ZA",
    "乌兹别克斯坦": "UZ",
    "俄罗斯": "RU",
    "德国": "DE",
    "摩尔多瓦": "MD",
    "孟加拉国": "BD",
    "巴西": "BR",
    "希腊": "GR",
    "巴拿马": "PA",
    "墨西哥": "MX",
    "泰国": "TH",
    "纳米比亚": "NA",
    "厄瓜多尔": "EC",
    "美国": "US",
    "西班牙": "ES",
}


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.in_th = False
        self.in_tr = False
        self.current_cell = []
        self.current_row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_tr:
            self.in_td = tag == "td"
            self.in_th = tag == "th"
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_tr and (self.in_td or self.in_th):
            text = " ".join("".join(self.current_cell).split())
            self.current_row.append(html.unescape(text))
            self.current_cell = []
            self.in_td = False
            self.in_th = False
        elif tag == "tr" and self.in_tr:
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_tr = False

    def handle_data(self, data):
        if self.in_tr and (self.in_td or self.in_th):
            self.current_cell.append(data)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ClashProxyFetcher/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def country_tag(location: str) -> str:
    for key, code in COUNTRY_CODE.items():
        if key in location:
            return code
    return "XX"


def parse_proxies(page_html: str):
    parser = TableParser()
    parser.feed(page_html)
    proxies = []
    seen = set()

    for row in parser.rows:
        if len(row) < 4:
            continue
        protocol, ip, port, location = row[0].lower(), row[1], row[2], row[3]
        if protocol not in {"socks5", "http", "https"}:
            continue
        if "x" in ip.lower():
            # 页面中被打码的 IP 无法直接使用，跳过
            continue
        if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", ip):
            continue
        if not port.isdigit():
            continue
        key = (protocol, ip, int(port))
        if key in seen:
            continue
        seen.add(key)
        proxies.append(
            {
                "protocol": protocol,
                "ip": ip,
                "port": int(port),
                "location": location,
                "tag": country_tag(location),
            }
        )
    return proxies


def clash_type(proxy):
    if proxy["protocol"] == "socks5":
        return "socks5"
    return "http"


def proxy_name(proxy, index):
    prefix = proxy["protocol"].upper()
    return f"{prefix}-{proxy['tag']}-{proxy['ip']}-{index:02d}"


def render_proxy_line(proxy, name):
    base = f'  - {{ name: "{name}", type: {clash_type(proxy)}, server: {proxy["ip"]}, port: {proxy["port"]}'
    if proxy["protocol"] == "https":
        base += ", tls: true, skip-cert-verify: true"
    return base + " }"


def indent_proxy_names(names, spaces=6):
    pad = " " * spaces
    return "\n".join(f'{pad}- "{name}"' for name in names)


def render_config(proxies, source_url):
    named = [(proxy_name(p, i + 1), p) for i, p in enumerate(proxies)]
    all_names = [name for name, _ in named]
    socks_names = [name for name, p in named if p["protocol"] == "socks5"]
    http_names = [name for name, p in named if p["protocol"] == "http"]
    https_names = [name for name, p in named if p["protocol"] == "https"]

    lines = []
    lines.append(f"# 由 fetch_clash_proxies.py 自动生成")
    lines.append(f"# 来源：{source_url}")
    lines.append("")
    lines.extend([
        "port: 7890",
        "socks-port: 7891",
        "mixed-port: 7892",
        "allow-lan: false",
        "mode: rule",
        "log-level: info",
        "external-controller: 127.0.0.1:9090",
        "",
        "profile:",
        "  store-selected: true",
        "  store-fake-ip: true",
        "",
        "dns:",
        "  enable: true",
        "  listen: 127.0.0.1:1053",
        "  ipv6: false",
        "  enhanced-mode: fake-ip",
        "  fake-ip-range: 198.18.0.1/16",
        "  default-nameserver:",
        "    - 223.5.5.5",
        "    - 119.29.29.29",
        "  nameserver:",
        "    - https://dns.alidns.com/dns-query",
        "    - https://doh.pub/dns-query",
        "  fallback:",
        "    - https://1.1.1.1/dns-query",
        "    - https://8.8.8.8/dns-query",
        "",
        "proxies:",
    ])

    for name, proxy in named:
        lines.append(render_proxy_line(proxy, name))

    lines.extend([
        "",
        "proxy-groups:",
        "  - name: \"PROXY\"",
        "    type: select",
        "    proxies:",
        "      - \"AUTO\"",
    ])
    if socks_names:
        lines.append('      - "SOCKS5"')
    if http_names:
        lines.append('      - "HTTP"')
    if https_names:
        lines.append('      - "HTTPS"')
    lines.append('      - "DIRECT"')
    lines.append(indent_proxy_names(all_names))

    lines.extend([
        "",
        "  - name: \"AUTO\"",
        "    type: url-test",
        f"    url: \"{TEST_URL}\"",
        "    interval: 300",
        "    tolerance: 100",
        "    proxies:",
        indent_proxy_names(all_names),
    ])

    group_defs = [("SOCKS5", socks_names), ("HTTP", http_names), ("HTTPS", https_names)]
    for group_name, names in group_defs:
        if not names:
            continue
        lines.extend([
            "",
            f"  - name: \"{group_name}\"",
            "    type: url-test",
            f"    url: \"{TEST_URL}\"",
            "    interval: 300",
            "    proxies:",
            indent_proxy_names(names),
        ])

    lines.extend([
        "",
        "rules:",
        "  - GEOIP,CN,DIRECT",
        "  - MATCH,PROXY",
        "",
    ])
    return "\n".join(lines)


def main():
    argp = argparse.ArgumentParser(description="抓取免费代理并生成 Clash 配置")
    argp.add_argument("--url", default=DEFAULT_URL, help="代理列表页面 URL")
    argp.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="输出 Clash YAML 文件路径")
    args = argp.parse_args()

    try:
        page = fetch_html(args.url)
        proxies = parse_proxies(page)
        if not proxies:
            raise RuntimeError("没有解析到可用代理，可能是页面结构变化或网络异常")
        config = render_config(proxies, args.url)
        out = Path(args.output)
        out.write_text(config, encoding="utf-8")
        print(f"已生成：{out.resolve()}")
        print(f"共写入 {len(proxies)} 个代理。")
    except Exception as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
