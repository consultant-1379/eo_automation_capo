"""
Main method - entry point
"""

from eo_install.capo_runner import CAPORunner
from eo_install.eccd_runner import ECCDRunner
from eo_install.eo_install_runner import EoInstall
from libs.environment_init.env_initializer import InitEnv


def execute_procedure():
    env = InitEnv()

    if env.install_evnfm or env.install_cm:
        EoInstall().install_eo()

    elif env.upgrade_cm or env.upgrade_evnfm:
        EoInstall().upgrade_eo()

    if env.install_eccd:
        ECCDRunner().install()
    elif env.upgrade_eccd:
        ECCDRunner().upgrade()

    if env.install_capo:
        CAPORunner().install_capo()

    elif env.upgrade_capo:
        CAPORunner().upgrade_capo()

    elif env.install_lm:
        EoInstall().install_eo()


if __name__ == '__main__':
    execute_procedure()
