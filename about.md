---
layout: default
title: "About UTM VM Gallery"
---

# UTM VM Gallery

Welcome to the UTM VM Gallery! This gallery provides various virtual machine images built using Packer.

## Problem

[UTM gallery](https://mac.getutm.app/gallery/) is heavily used to get pre-built UTM VMs.  
Total download metrics: [Check download metrics](https://tooomm.github.io/github-release-stats/?username=utmapp&repository=vm-downloads)

- However, a few VMs are hosted on archive.org, which provides slow download times.
- The gallery has stopped updating for new OS or new versions of existing OS, citing the unavailability of automated and scalable solutions.

## Solution

- There is now a [packer plugin](https://github.com/naveenrajm7/packer-plugin-utm) for UTM, which automates the VM building process.
- UTM VMs for popular OS are already built using [packer recipes](https://github.com/naveenrajm7/utm-box) and published at the [HCP Vagrant registry](https://portal.cloud.hashicorp.com/vagrant/discover/utm) for use with [Vagrant UTM](https://naveenrajm7.github.io/vagrant_utm/).

Given the demand for pre-built UTM VMs, this gallery, with the help of a simple script, opens up the HCP Vagrant registry boxes to be used by UTM without the need for Vagrant, and addresses the shortcomings of the UTM gallery.

## Features

- Pre-configured VM images
- Easy to download and use
- Version control for VMs
- Support for multiple architectures

## UTM Plugins

Check out UTM plugins:

- **Vagrant**: [vagrant_utm](https://naveenrajm7.github.io/vagrant_utm/)
- **Packer**: [packer-plugin-utm](https://github.com/naveenrajm7/packer-plugin-utm)
- **UTM Web**: [Coming soon...](https://github.com/utmapp/UTM/issues/6767)