from libs.constants import ProjectFilesLocation
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.director.eo_download_manager.download_mgr import DownloadManager


class PostSteps(DownloadManager):

    def remove_lock_file(self):
        with open(ProjectFilesLocation.LOCKFILE_INFO, 'r') as file:
            lockfile = file.read()
        self.execute_command(f'rm -rf {lockfile}')


if __name__ == '__main__':
    PostSteps(EoEnv()).remove_lock_file()
