from .helper import HardwareHelper
from .optimizer import HardwareOptimizer
from .validator import PackageValidator
from .integrity import BootIntegrityGuard

__all__ = [
    'HardwareHelper',
    'HardwareOptimizer',
    'PackageValidator',
    'BootIntegrityGuard'
]

def get_engine(config):
    """
    Convenience factory to initialize the full stack at once.
    """
    helper = HardwareHelper(config)
    return {
        "helper": helper,
        "optimizer": HardwareOptimizer(helper.target, helper.hw_def, helper.distro),
        "validator": PackageValidator(helper.hw_def, helper.distro),
        "guard": BootIntegrityGuard(config, helper.hw_def)
    }
