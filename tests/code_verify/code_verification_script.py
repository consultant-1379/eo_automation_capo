"""
Tests to check code consistency
"""

import glob
import logging
import os

import pycodestyle
from pyflakes.scripts import pyflakes
from pylint.lint import Run


from libs.utils.config_manager.config_reader import ConfigReader

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
config_dir = os.path.join('config', '**', '**.yaml')
eo_install_dir = os.path.join('eo_install', '**', '**.py')
libs_dir = os.path.join('libs', '**', '**.py')
list_of_dirs = (eo_install_dir, libs_dir)


class CodeVerificationScript:
    @staticmethod
    def __test_config_files_consistency():
        for filename in glob.glob(config_dir, recursive=True):
            ConfigReader.get_config(filename)
        logging.info('Config files are OK')

    @staticmethod
    def __test_pep8_requirements():
        file_errors = 0
        for directory in list_of_dirs:
            for filename in glob.glob(directory, recursive=True):
                file_errors += pycodestyle.Checker(filename, show_source=True,
                                                   ignore=['E501', 'W605', 'E731']).check_all()
        assert file_errors == 0, 'Please check PEP8 error.'
        logging.info('No PEP8 errors defined, libs are OK.')

    @staticmethod
    def __test_unused_import_and_vars():
        count_unused_import = 0
        for directory in list_of_dirs:
            for filename in glob.glob(directory, recursive=True):
                count_unused_import += pyflakes.checkPath(filename)
        assert count_unused_import == 0, 'Please check pyflakes errors'
        logging.info('No unused imports and variables defined, libs are OK.')

    @staticmethod
    def __pylint_check():
        Run(('libs', 'eo_install', '--disable=E0611,C0301,W1203,R0903,C0115,R0902,W0106,C0116,C0114,C0415,R0915,W0212'),
            exit=True)

    def run_all(self):
        self.__test_config_files_consistency()
        self.__test_pep8_requirements()
        self.__test_unused_import_and_vars()
        self.__pylint_check()


if __name__ == '__main__':
    CodeVerificationScript().run_all()
