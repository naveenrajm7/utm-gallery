---
layout: default
title: "How it works"
---

# How the images are built

All images are built automatically using the UTM Packer plugin. The eventual goal is to build VMs in CI. You can learn more about the UTM Packer plugin [here](https://github.com/naveenrajm7/packer-plugin-utm).

## Builder Types

There are currently two types of builders:

- **ISO**:  
  Images are built using ISO files. These are large boxes with a GUI installed where possible.
  
- **Cloud**:  
  Images are built using cloud QCOW2 files. These are small boxes with only a terminal interface.

## Naming Conventions

- **Cloud Images**:  
  - Use release names if they exist. For example: `bookworm` for Debian 12.
  - If no release name exists, the naming convention is `name<version>-ce` (Cloud Edition). For example: `fedora41-ce`.

- **ISO Images**:  
  Use the format `osname-version`. For example: `debian-12`.

## Labels

- **Packer Builder**:  
  - `iso`: Indicates the image was built using packer iso builder.
  - `cloud`: Indicates the image was built using packer cloud builder.
