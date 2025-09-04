#!/usr/bin/env python3
import csv
import os
import re
import sys
from urllib.parse import urlparse


EXTINF_PATTERN = re.compile(r"#EXTINF:[^,]*,(.*)")
ATTR_PATTERN = re.compile(r"(\w+?)=\"(.*?)\"")


def parse_m3u(m3u_path: str):
    channels = []
    pending_meta = None

    def parse_attrs(line: str) -> dict:
        attrs = {}
        for key, value in ATTR_PATTERN.findall(line):
            attrs[key] = value
        return attrs

    with open(m3u_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#EXTM3U"):
                # header; could contain url-tvg etc., not used per-row
                continue

            if line.startswith("#EXTINF"):
                attrs = parse_attrs(line)
                match = EXTINF_PATTERN.search(line)
                name = match.group(1).strip() if match else ""
                pending_meta = {
                    "name": name,
                    "group": attrs.get("group-title", ""),
                    "tvg_id": attrs.get("tvg-id", ""),
                    "tvg_logo": attrs.get("tvg-logo", ""),
                }
                continue

            if pending_meta and (line.startswith("http://") or line.startswith("https://")):
                url = line
                parsed = urlparse(url)
                record = {
                    **pending_meta,
                    "url": url,
                    "protocol": parsed.scheme,
                    "domain": parsed.hostname or "",
                    "path": parsed.path or "",
                }
                channels.append(record)
                pending_meta = None
                continue

            # Ignore other lines

    return channels


def write_csv(channels, csv_path: str):
    fieldnames = [
        "name",
        "group",
        "tvg_id",
        "tvg_logo",
        "protocol",
        "domain",
        "path",
        "url",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in channels:
            writer.writerow(row)


def main():
    if len(sys.argv) < 3:
        print("Usage: export_m3u_to_csv.py INPUT.m3u OUTPUT.csv")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    if not os.path.isfile(input_path):
        print(f"Input not found: {input_path}")
        sys.exit(2)
    channels = parse_m3u(input_path)
    write_csv(channels, output_path)
    print(f"Wrote {len(channels)} rows to {output_path}")


if __name__ == "__main__":
    main()

