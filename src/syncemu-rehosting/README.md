# README for SyncEmu's rehosting framework
We strongly recommend using the Dockerfile to build SyncEmu.

## Project layout

This project is divided mainly into two components.

- `common` is a Python library that provides useful functionality shared among the actual scripts.
- `scripts` contains Python scripts that implement actual functionality to debug and assess software, as well as some useful helper scripts such as the QEMU serial server.