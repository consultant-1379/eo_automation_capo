"""
YAML files reader
"""
import logging

import yaml


class ConfigReader:
    @staticmethod
    def get_config(config_name):
        with open(config_name, 'r', encoding='utf-8') as yaml_file:
            content = yaml_file.read()
            configuration = yaml.load(content, Loader=yaml.FullLoader)
            logging.debug(content)
        return configuration
