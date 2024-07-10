from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN


def aarch64_asm(code: str):
    """
    Run AArch64 Little Endian assembler on given code.

    :param code: assembler code
    :return: raw assembly in bytes
    """

    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    assembly, _ = ks.asm(code, as_bytes=True)
    return assembly
