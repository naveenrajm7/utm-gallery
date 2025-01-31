# UTM VM Gallery

This repository hosts [UTM VM Gallery](https://naveenrajm7.github.io/utm-gallery/), which exposes [UTM Vagrant Registry](https://portal.cloud.hashicorp.com/vagrant/discover/utm) VMs to be used in UTM without Vagrant.

## How to use

Check [How to use](https://naveenrajm7.github.io/utm-gallery/how_to_use).

## How this works

The site just presents a simple command to execute to open the VMs in UTM. 
 
Check [getbox script](getbox.sh)

### getbox.sh

The sript does 3 main things
1. Download the requested VM from HCP, which is in .box format (a tar file)
2. Extract the .utm file from the downloaded .box file.
3. Import the .utm file to UTM using osascript.

> Initially, an attempt was made to allow users to download VM directly using `utm://downloadVM?url=\<zipfile>, this attempt failed as it was not possible to untar a large file or create a large zip file within the browser. All this because we are using a static site.

### UI

The UI is just a wrapper around [HCP Vagrant Registry APIs](https://developer.hashicorp.com/hcp/api-docs/vagrant-box-registry).
Because we cannot do API request (CORS) from static pages (github pages), we reply on sync service script to pull down the data from HCP and store it as static data.

[sync service](sync_registry.py)

1. Gets boxes and its details from HCP.
2. Combines API data with user data `_data` about the each VM.
3. Generates static pages in `_vms` with all VM data, which will be rendered by jekyll.

> This means the details you see in the [Gallery](https://naveenrajm7.github.io/utm-gallery/) is a static conent, usually  outdated from [HCP Registry](https://portal.cloud.hashicorp.com/vagrant/discover/utm). Again, because we are using a static site.