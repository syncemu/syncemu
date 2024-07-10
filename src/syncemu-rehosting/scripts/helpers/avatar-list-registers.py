"""
Small helper script that prints the GDB register IDs, as received by Avatar2.
These IDs can be used in Architecture classes to tell Avatar2 how to access
specific registers.
"""

import logging
import os
import shutil

import click
from avatar2 import Avatar, ARM, AARCH64, QemuTarget


@click.command()
@click.argument("arch_name")
def main(arch_name: str):
    arch_name = arch_name.lower()

    if arch_name == "arm":
        arch = ARM
    elif arch_name == "aarch64":
        arch = AARCH64
    else:
        print("Unknown architecture:", arch_name)
        return 1

    # hide all log messages
    logging.basicConfig(level=logging.CRITICAL)

    avatar = Avatar(arch=arch)

    qemu_target = avatar.add_target(QemuTarget)

    avatar.init_targets()

    for i, name in enumerate(qemu_target.protocols.registers.get_register_names()):
        print(str(i).rjust(3), name)

    avatar.shutdown()

    if os.path.isdir(avatar.output_directory):
        shutil.rmtree(avatar.output_directory)


if __name__ == "__main__":
    main()
