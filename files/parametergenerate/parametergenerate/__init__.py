#!/usr/bin/python
# -*- coding: UTF-8 -*-
from . import find_text_value
from . import find_xml_value
from . import find_json_value
from . import find_ini_value
from . import find_reg_value
from . import find_list_value
from . import output_yaml
from . import specific
import errno
import os


class ParameterGenerate:
    key_value_table = {}
    collect_root = ""

    def __init__(self, collect_root):
        self.key_value_table = {}
        self.collect_root = collect_root

    def find_value_common(self, target):
        file_type_map = {
            'text': find_text_value.find_value,
            'xml': find_xml_value.find_value,
            'json': find_json_value.find_value,
            'ini': find_ini_value.find_value,
            'reg': find_reg_value.find_value,
            'list': find_list_value.find_value,
        }
        targetfile = target.get('src', None)
        file_type = target.get('type', None)
        params = target.get('params', None)
        encoding = target.get('encoding', None)
        trap_undefined_error = target.get('trap_undefined_error', False)

        if targetfile is None or file_type is None or params is None:
            raise Exception("parameter (config) is invalid.")

        targetfile = self.collect_root + '/' + targetfile
        if (not os.path.isfile(targetfile)):
            if trap_undefined_error:
                raise IOError(
                    errno.ENOENT, os.strerror(errno.ENOENT), targetfile)
            else:
                return

        try:
            # Search the parameter from target file.
            find_value = file_type_map[file_type]
        except KeyError:
            raise KeyError('Unknown value type ({}). Expected one of ({})'
                           ''.format(file_type, ','.join(file_type_map.keys())))
        key_value = find_value(targetfile, params, encoding, trap_undefined_error)
        self.key_value_table.update(key_value)

    def find_value_specific(self, command):
        key_value = specific.find_specific_value(command, self.collect_root)
        self.key_value_table.update(key_value)

    def save(self, file_name):
        output_yaml.save_yaml(file_name, self.key_value_table)
