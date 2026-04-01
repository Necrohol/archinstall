from .x86_64 import X86_64Handler
from .arm64 import Arm64Handler
from .riscv64 import Riscv64Handler

ARCH_MAP = {
    'x86_64': X86_64Handler,
    'aarch64': Arm64Handler,
    'arm64': Arm64Handler,
    'riscv64': Riscv64Handler
}

