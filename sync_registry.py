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

def fetch_box_details(box):
    conn = http.client.HTTPSConnection("api.cloud.hashicorp.com")
    
    # Fetch versions
    conn.request("GET", f"/vagrant/2022-09-30/registry/utm/box/{box['name']}/versions")
    response = conn.getresponse()
    if response.status != 200:
        raise Exception(f"Failed to fetch versions for box {box['name']}")
    
    versions_data = json.loads(response.read().decode())
    latest_version = versions_data['versions'][0]['name']
    box['latest_version'] = latest_version
    
    # Fetch details for the latest version and architecture
    conn.request("GET", f"/vagrant/2022-09-30/registry/utm/box/{box['name']}/version/{latest_version}/provider/utm/architecture/arm64")
    response = conn.getresponse()
    if response.status != 200:
        raise Exception(f"Failed to fetch details for box {box['name']} version {latest_version}")
    
    details_data = json.loads(response.read().decode())
    size_bytes = int(details_data['architecture']['box_data']['size'])
    size_mb = size_bytes / (1024 * 1024)
    box['size'] = size_mb

    # Fetch architectures
    conn.request("GET", f"/vagrant/2022-09-30/registry/utm/box/{box['name']}/version/{latest_version}/provider/utm/architectures")
    response = conn.getresponse()
    if response.status != 200:
        raise Exception(f"Failed to fetch architectures for box {box['name']} version {latest_version}")
    
    architectures_data = json.loads(response.read().decode())
    architectures = [arch['architecture_type'] for arch in architectures_data['architectures']]
    box['architectures'] = ", ".join(architectures)

    return box

def load_user_data(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

def combine_data(box, user_data):
    combined_data = {**box, **user_data}
    return combined_data

def create_markdown_file(box):
    filename = f"_vms/{box['name']}.md"
    content = f"""---
### This file is auto-generated. Do not edit manually.
### To update this file , run `python3 sync_registry.py`
layout: vm
# API response data
name: "{box['name']}"
downloads: {box['downloads']}
description: '{box['description']}'
short_description: "{box['short_description']}"
is_private: {box['is_private']}
created_at: {box['created_at']}
updated_at: {box['updated_at']}
versions_count: {box['summary']['versions_count']}
provider_names: "{', '.join(box['summary']['provider_names'])}"
latest_released_at: {box['summary']['latest_released_at']}
state: "{box['state']}"
description_html: '{box['description_html']}'
versions: "{box['versions']}"

# API Response : Box details
size: {box.get('size', 'N/A')}
architectures: "{box.get('architectures', 'N/A')}"
# Hardcoded data
image_url: "assets/images/{box['name']}.png"

# User data
icon_url: "assets/images/icons/{box['icon']}.png"
packer_builder: "{box.get('packer_builder', 'N/A')}"
display_name: "{box.get('display_name', 'N/A')}"
serial_port: {box.get('serial_port', 'N/A')}
---
"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as file:
        file.write(content)

def main():
    boxes = fetch_boxes()
    for box in boxes:
        box = fetch_box_details(box)
        user_data_filepath = f"_data/{box['name']}.json"
        if os.path.exists(user_data_filepath):
            user_data = load_user_data(user_data_filepath)
            combined_data = combine_data(box, user_data)
            create_markdown_file(combined_data)
        else:
            print(f"User data file not found for {box['name']}")

if __name__ == "__main__":
    main()