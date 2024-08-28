"""
Download manager - download EO packages
"""
import ast
import logging
import re
import time

import yaml

from libs.constants import ProjectFilesLocation
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.controller.controller_data import ControllerFilesLocation, ControllerCommands
from libs.eo_libs.controller.controller_vm import ControllerVm
from libs.eo_libs.director.eo_download_manager.download_data import EoPackageLinks, EoBasePackageLinks, AatPackageLinks


class DownloadManager(ControllerVm):
    def __init__(self, env: EoEnv):
        super().__init__(env)
        self.env = env
        self.products_versions = {}
        self.download_dir: str = ControllerFilesLocation.EO_PACKAGES_DIR
        self.__commands = ['All copy commands', ]
        if not re.match('\\d+.\\d+.\\d+-\\d+', self.env.helmfile_version):
            self.env.exit('Wrong EO version provided, stopping execution!')

    def download_packages(self):
        self.ssh_client.transfer_file(ProjectFilesLocation.WGETRC_FILE, f'{ControllerFilesLocation.HOME}/.wgetrc')
        dirs_to_create = (self.download_dir, self.env.workdir)
        for directory in dirs_to_create:
            if not self.__check_directory_exists(directory):
                self.execute_command(f'{ControllerCommands.CREATE_FOLDER(directory)}')
        self._download_dm()
        if self.env.is_cm_related or self.env.is_evnfm_related or self.env.is_lm_related:
            helmfile_link = EoPackageLinks.CM_HELMFILE.value if self.env.is_cm_related else EoPackageLinks.HELMFILE.value
            file_name = self._download_package(helmfile_link, self.env.helmfile_version, 'HelmFile')
            self.products_versions = self._parse_helmfile(file_name)
            self._download_base_csars()
        self.products_versions['AAT'] = self.env.helmfile_version
        self._download_eo_csars()
        logging.debug('\n'.join(map(str, self.__commands)))

    def _download_dm(self):
        logging.info('Package for Deployment Manager is going to be downloaded, please wait...')
        dm_name = f'deployment-manager-{self.env.dm_version}.zip'
        check_dm_exists = self.__check_package_exists(dm_name, EoPackageLinks.DM_FILE.value, self.env.dm_version)
        if check_dm_exists:
            logging.info('Package for Deployment Manager present and checked!')
            self.__copy_package_to_work_dir(dm_name)
            return
        self._download_package(EoPackageLinks.DM_FILE.value, self.env.dm_version, 'Deployment Manager')

    def _parse_helmfile(self, file_name):
        helmfile_location = 'eric-eo-cm-helmfile/helmfile.yaml' if self.env.is_cm_related else 'eric-eo-helmfile/helmfile.yaml'
        file_name_tgz = file_name.replace("csar", "tgz")
        tmp_helmfile_dir = f'{self.download_dir}/tmp_{self.env.env_name}'
        self.execute_command(f'mkdir {tmp_helmfile_dir}')
        self.execute_command(
            f'unzip -jo {self.download_dir}/{file_name} Definitions/OtherTemplates/{file_name_tgz} -d {tmp_helmfile_dir}')
        self.execute_command(f'tar -zxf {tmp_helmfile_dir}/{file_name_tgz} -C {tmp_helmfile_dir} {helmfile_location}')
        helmfile = self.execute_command(
            f'''sed -n '/releases/,$p' {tmp_helmfile_dir}/{helmfile_location} | grep -E "releases:|name:|version"''')
        versions = {}
        for release in yaml.load(helmfile, Loader=yaml.FullLoader)['releases']:
            versions[release.get('name').replace('-', '_').upper()] = release.get('version')
        self.execute_command(f'rm -rf {tmp_helmfile_dir}')
        return versions

    def _download_base_csars(self):
        for product in EoBasePackageLinks:
            if self.env.install_lm and product.name == 'ERIC_OSS_FUNCTION_ORCHESTRATION_COMMON':
                continue
            self.__perform_csar_download(product, EoBasePackageLinks)

    def __perform_csar_download(self, product, links_enum):
        product_name, product_link = product.name, product.value
        version = self.products_versions.get(product_name)
        self._download_package(links_enum(product_link).value, version, product_name)

    def _download_eo_csars(self):
        """
        Method to download selected EO packages
        """
        download_options: tuple = ((self.env.is_evnfm_related, EoPackageLinks.ERIC_EO_EVNFM_VM),
                                   (self.env.is_evnfm_related, EoPackageLinks.ERIC_EO_EVNFM),
                                   (self.env.is_cm_related, EoPackageLinks.ERIC_EO_CM),
                                   (self.env.is_cm_related, EoPackageLinks.ERIC_EO_ACT_CNA),
                                   (self.env.install_clm, EoPackageLinks.ERIC_OSS_EO_CLM),
                                   (self.env.install_aat, AatPackageLinks.AAT),
                                   (self.env.install_lm, EoPackageLinks.ERIC_SERVICE_EXPOSURE_FRAMEWORK),
                                   (self.env.install_lm, EoPackageLinks.ERIC_EO_LIFECYCLE_MANAGER))
        [self._download_package(option[1].value, self.products_versions.get(option[1].name), option[1].name) for option
         in download_options if option[0]]

    def __check_directory_exists(self, path: str):
        check_dir = self.execute_command(f'test -d {path} && echo "True" || echo "False"')
        return ast.literal_eval(check_dir)

    def _download_package(self, package_link, version, product_name):
        lock_file = f"{self.download_dir}/{product_name.lower().replace(' ', '_').replace('-', '_')}_{version}.lock"
        self.__check_lock_file(lock_file, product_name)
        try:
            self.execute_command(f'touch {lock_file}')
            with open(ProjectFilesLocation.LOCKFILE_INFO, 'w', encoding="utf-8") as file:
                file.write(lock_file)
            product_name = product_name.replace('_', '-').lower()
            if not version:
                logging.warning(f'Package {product_name} seems not needed for the current installation, skipping.')
                return None
            logging.info(f'Package for {product_name} is going to be downloaded, please wait...')
            file_name = self.execute_command(f'basename {package_link(version)}')
            if self.__check_package_exists(file_name, package_link, version):
                self.__copy_package_to_work_dir(file_name)
                logging.info(f'Package for {product_name} present and checked!')
                return file_name
            self.execute_command(f"find ./ -name '{product_name}-[0-9]*' -delete")

            def download_link(link):
                return ControllerCommands.DOWNLOAD_FILE(self.download_dir, link(version))

            self.execute_command(download_link(package_link), pty=True, log_output=False)
            assert self.__check_package_exists(file_name, package_link, version), \
                f'Error during downloading package for {product_name}, check the file!'
            logging.info(f'Package for {product_name} downloaded successfully!')
            self.__copy_package_to_work_dir(file_name)
            return file_name
        finally:
            self.execute_command(f'rm -f {lock_file}')

    def __copy_package_to_work_dir(self, file_name):
        command = f'cp {self.download_dir}/{file_name} {self.env.workdir}/{file_name}'
        self.execute_command(command)
        self.__commands.append(command)

    def __check_lock_file(self, lock_file, product_name, tries=100):
        while tries > 0:
            is_lock_exists = self.execute_command(f'test -f {lock_file} && echo "True" || echo "False"')
            if ast.literal_eval(is_lock_exists):
                logging.info(
                    f"Package for {product_name.replace('_', '-').lower()} is downloading by another job, waiting...")
                time.sleep(60)
                tries -= 1
            else:
                return
        self.execute_command(f'rm -f {lock_file}')

    def __check_package_exists(self, file_name, package_link, version):
        is_file_exists_not_empty = self.execute_command(
            f'test -f {self.download_dir}/{file_name} && echo "True" || echo "False"')
        if ast.literal_eval(is_file_exists_not_empty):
            check_sum = 'sha1' if "eo-test-service" in file_name else 'sha256'
            return self.__check_checksum(file_name, package_link, version, check_sum=check_sum)
        return False

    def __check_checksum(self, file_name, package_link, version, check_sum='sha256'):
        if self.env.skip_checksum:
            return True
        file_location = f'{self.download_dir}/{file_name}'
        self.execute_command(f'rm -f {file_location}.{check_sum}')
        self.execute_command(
            ControllerCommands.DOWNLOAD_FILE(self.download_dir, f'{package_link(version)}.{check_sum}'))
        package_sum = self.execute_command(
            ControllerCommands.CHECK_SHA256(file_location)) if check_sum == 'sha256' else self.execute_command(
            ControllerCommands.CHECK_SHA1(file_location))
        remote_sum = self.execute_command(f'cat {file_location}.{check_sum}')
        self.execute_command(f'rm -f {file_location}.{check_sum}')
        return package_sum == remote_sum
