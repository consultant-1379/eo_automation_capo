from eo_install.eo_install_runner import EoInstall


class AatInstall(EoInstall):
    def __init__(self):
        super().__init__()
        self.namespace = f'aat_{self.env.env_name}'

    def install_eo(self):
        self.eo_download_manager.download_packages()
        self.eo_env_manager.prepare_env_for_aat()
        self.eo_env_manager.install_aat_test_service()
