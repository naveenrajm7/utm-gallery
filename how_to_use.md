---
layout: default
title: "How to use gallery VMs"
---

# How to use gallery VMs

Use directly with UTM or with Vagrant.

## UTM

1. Choose your VM from the [Gallery]({{ '/' | relative_url }}).
2. Click on **View Details**.
3. Click on **Open in UTM** button.
4. Copy the command presented, paste it into your terminal, and execute it.
5. The VM will be imported into UTM.
6. Add a Display to the VM, if it does not exist already.  
   *Since most VMs were built for Vagrant, they run headless with no display.*
7. Start the VM.

## Vagrant

```bash
vagrant init <box-name>
```

Check out [vagrant_utm](https://naveenrajm7.github.io/vagrant_utm/).