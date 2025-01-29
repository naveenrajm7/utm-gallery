import json
import os

# Load the data from the JSON file
with open('_data/boxes.json') as f:
    data = json.load(f)

# Read the template file
with open('_layouts/vm.html') as f:
    template = f.read()

# Ensure the output directory exists
os.makedirs('_site/vm', exist_ok=True)

# Generate the VM pages
for box in data['boxes']:
    content = template
    content = content.replace('{{name}}', box['name'])
    content = content.replace('{{description}}', box['description_html'])
    content = content.replace('{{downloads}}', str(box['downloads']))
    content = content.replace('{{version}}', str(box['summary']['versions_count']))
    content = content.replace('{{arch}}', ', '.join(box['summary']['provider_names']))

    # Write the generated content to a file
    with open(f'_vm/{box["name"]}.md', 'w') as f:
        f.write(content)

print('VM pages generated successfully')