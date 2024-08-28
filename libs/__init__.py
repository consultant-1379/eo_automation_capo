import ast
import os

get_environ = os.environ.get


def get_bool_environ(env_var, default='False'):
    return ast.literal_eval(get_environ(env_var, default).capitalize())
