import http.client
import json
import os

def fetch_boxes():
    conn = http.client.HTTPSConnection("api.cloud.hashicorp.com")
    conn.request("GET", "/vagrant/2022-09-30/registry/utm/boxes")
    response = conn.getresponse()
    if response.status != 200:
        raise Exception(f"Failed to fetch boxes: {response.status} {response.reason}")
    data = response.read()
    conn.close()
    return json.loads(data)["boxes"]

def create_markdown_file(box):
    filename = f"_vms/{box['name']}.md"
    content = f"""---
layout: vm
name: "{box['name']}"
downloads: {box['downloads']}
description: '{box['description']}'
short_description: "{box['short_description']}"
is_private: {box['is_private']}
created_at: {box['created_at']}
updated_at: {box['updated_at']}
versions_count: {box['summary']['versions_count']}
provider_names: "{', '.join(box['summary']['provider_names'])}"
latest_released_at: "{box['summary']['latest_released_at']}"
state: "{box['state']}"
description_html: '{box['description_html']}'
versions: "{box['versions']}"
---
"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as file:
        file.write(content)

def main():
    boxes = fetch_boxes()
    for box in boxes:
        create_markdown_file(box)

if __name__ == "__main__":
    main()