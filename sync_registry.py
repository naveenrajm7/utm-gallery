import glob
import http.client
import json
import os
import sys
import time
import urllib.parse

API_HOST = "api.cloud.hashicorp.com"
API_BASE = "/vagrant/2022-09-30/registry"
PROVIDER = "utm"
PREFERRED_ARCH = "arm64"
VMS_DIR = "_vms"
DATA_DIR = "_data"
ICONS_DIR = "assets/images/icons"
GENERATED_MARKER = "### This file is auto-generated."

# Each source is an HCP Vagrant Registry org. `file_prefix` keeps generated
# filenames (and therefore page URLs and `_data` lookups) unique across orgs.
# Sources with `require_user_data` only publish boxes that have a curated
# `_data/<file>.json`; the others fall back to defaults derived from the API.
SOURCES = [
    {
        "source": "utm",
        "label": "UTM",
        "org": "utm",
        "file_prefix": "",
        "require_user_data": True,
    },
    {
        "source": "bento",
        "label": "Bento",
        "org": "bento",
        "file_prefix": "bento-",
        "require_user_data": False,
    },
]


class Raw(str):
    """A front matter value written verbatim (e.g. timestamps)."""


def api_get(path, params=None, retries=3):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(1, retries + 1):
        conn = http.client.HTTPSConnection(API_HOST, timeout=30)
        try:
            conn.request("GET", url)
            response = conn.getresponse()
            body = response.read()
            if response.status == 200:
                return json.loads(body)
            error = f"{response.status} {response.reason}"
            if response.status < 500 and response.status != 429:
                break
        except (OSError, http.client.HTTPException) as e:
            error = str(e)
        finally:
            conn.close()
        if attempt < retries:
            time.sleep(2 ** attempt)
    raise Exception(f"GET {url} failed: {error}")


def api_get_paginated(path, key):
    items = []
    token = ""
    while True:
        params = {"pagination.next_page_token": token} if token else None
        data = api_get(path, params)
        items.extend(data.get(key, []))
        token = data.get("pagination", {}).get("next_page_token", "")
        if not token:
            return items


def fetch_boxes(org):
    return api_get_paginated(f"/{org}/boxes", "boxes")


def has_provider(summary):
    return PROVIDER in (summary or {}).get("provider_names", [])


def latest_provider_version(org, box_name):
    """Newest version of the box that ships the UTM provider."""
    token = ""
    while True:
        params = {"pagination.next_page_token": token} if token else None
        data = api_get(f"/{org}/box/{box_name}/versions", params)
        for version in data.get("versions", []):
            if has_provider(version.get("summary")):
                return version["name"]
        token = data.get("pagination", {}).get("next_page_token", "")
        if not token:
            return None


def fetch_box_details(org, box):
    version = latest_provider_version(org, box["name"])
    if version is None:
        return None
    box["latest_version"] = version

    provider_path = f"/{org}/box/{box['name']}/version/{version}/provider/{PROVIDER}"
    architectures_data = api_get(f"{provider_path}/architectures")
    architectures = [a["architecture_type"] for a in architectures_data["architectures"]]
    if not architectures:
        return None
    box["architectures"] = ", ".join(architectures)

    arch = PREFERRED_ARCH if PREFERRED_ARCH in architectures else architectures[0]
    box["download_arch"] = arch
    details_data = api_get(f"{provider_path}/architecture/{arch}")
    size_bytes = int(details_data["architecture"]["box_data"]["size"])
    box["size"] = size_bytes / (1024 * 1024)
    return box


def load_user_data(filepath):
    with open(filepath, "r") as file:
        return json.load(file)


def combine_data(box, user_data):
    combined_data = {**box, **user_data}
    return combined_data


def available_icons():
    return {os.path.splitext(f)[0] for f in os.listdir(ICONS_DIR) if f.endswith(".png")}


def guess_icon(box_name, icons):
    for token in box_name.lower().replace(".", "-").split("-"):
        if token in icons:
            return token
    return "default"


def yaml_value(value):
    if isinstance(value, Raw):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    # JSON strings are valid YAML double-quoted scalars, so quotes, newlines
    # and other special characters in API descriptions are escaped safely.
    return json.dumps(str(value))


def build_front_matter(box, source, file_stem, icons):
    summary = box.get("summary", {})
    icon = box.get("icon") or guess_icon(box["name"], icons)
    icon_url = f"assets/images/icons/{icon}.png"
    image_url = f"assets/images/{file_stem}.png"
    if not os.path.exists(image_url):
        image_url = icon_url

    return [
        ("# API response data", None),
        ("name", box["name"]),
        ("downloads", int(box.get("downloads", 0))),
        ("description", box.get("description", "")),
        ("short_description", box.get("short_description", "")),
        ("is_private", bool(box.get("is_private", False))),
        ("created_at", Raw(box["created_at"])),
        ("updated_at", Raw(box["updated_at"])),
        ("versions_count", int(summary.get("versions_count", 0))),
        ("provider_names", ", ".join(summary.get("provider_names", []))),
        ("latest_released_at", Raw(summary.get("latest_released_at", box["updated_at"]))),
        ("state", box.get("state", "")),
        ("description_html", box.get("description_html", "")),
        ("versions", str(box.get("versions", []))),
        ("", None),
        ("# API Response : Box details", None),
        ("latest_version", box["latest_version"]),
        ("size", box["size"]),
        ("architectures", box["architectures"]),
        ("download_arch", box["download_arch"]),
        ("", None),
        ("# Source registry", None),
        ("source", source["source"]),
        ("source_label", source["label"]),
        ("registry_org", source["org"]),
        ("box_ref", f"{source['org']}/{box['name']}"),
        ("", None),
        ("# Hardcoded data", None),
        ("image_url", image_url),
        ("", None),
        ("# User data (null when no _data file exists)", None),
        ("icon_url", icon_url),
        ("packer_builder", box.get("packer_builder")),
        ("display_name", box.get("display_name")),
        ("serial_port", box.get("serial_port")),
    ]


def create_markdown_file(filename, fields):
    lines = [
        "---",
        "### This file is auto-generated. Do not edit manually.",
        "### To update this file , run `python3 sync_registry.py`",
        "layout: vm",
    ]
    for key, value in fields:
        if key == "" or key.startswith("#"):
            lines.append(key)
        else:
            lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as file:
        file.write("\n".join(lines) + "\n")


def warn(message):
    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") else "WARNING: "
    print(f"{prefix}{message}")


def sync_source(source, icons, written, kept):
    org = source["org"]
    boxes = fetch_boxes(org)
    print(f"[{org}] {len(boxes)} boxes in registry")
    for box in boxes:
        if not has_provider(box.get("summary")):
            continue
        file_stem = f"{source['file_prefix']}{box['name']}"
        filename = os.path.join(VMS_DIR, f"{file_stem}.md")

        user_data_filepath = os.path.join(DATA_DIR, f"{file_stem}.json")
        user_data = {}
        if os.path.exists(user_data_filepath):
            user_data = load_user_data(user_data_filepath)
        elif source["require_user_data"]:
            print(f"User data file not found for {box['name']}")
            continue

        try:
            box = fetch_box_details(org, box)
        except Exception as e:
            warn(f"[{org}] skipping {box['name']}, keeping any existing page: {e}")
            kept.add(filename)
            continue
        if box is None:
            print(f"[{org}] {file_stem}: no {PROVIDER} provider version, skipping")
            continue

        combined_data = combine_data(box, user_data)
        create_markdown_file(filename, build_front_matter(combined_data, source, file_stem, icons))
        written.add(filename)
        print(f"[{org}] wrote {filename}")


def prune_stale_pages(keep):
    """Remove generated pages for boxes that no longer exist or lost UTM support."""
    for filename in glob.glob(os.path.join(VMS_DIR, "*.md")):
        if filename in keep:
            continue
        with open(filename, "r") as file:
            if GENERATED_MARKER not in file.read(512):
                continue
        os.remove(filename)
        print(f"removed stale {filename}")


def main():
    icons = available_icons()
    written, kept = set(), set()
    for source in SOURCES:
        sync_source(source, icons, written, kept)
    prune_stale_pages(written | kept)
    print(f"{len(written)} pages written, {len(kept)} kept after errors")


if __name__ == "__main__":
    sys.exit(main())
