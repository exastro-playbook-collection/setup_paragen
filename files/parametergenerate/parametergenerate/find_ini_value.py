#!/usr/bin/python
# -*- coding: utf-8 -*-
import io
import re

from jinja2 import Template

from parametergenerate import utility


def find_value(target_file, search_params, encoding=None, trap_undefined_error=False):

    if encoding is None:
        encoding = utility.check_encode(target_file)

    key_value_table = {}

    # if INI_FILE in codeList:
    with io.open(target_file, 'r', encoding=encoding) as testfile:
        lines = testfile.readlines()

    for param in search_params:
        findsection = False
        findkey = False
        for line in lines:
            # Section not found
            if not findsection:
                # Find a section
                ls = line.strip()
                if ls == '[%s]' % param['section']:
                    # Find it if found
                    findsection = True
            else:
                # Search for KEY. When I'm looking for a section, I get an error
                linereplace = re.sub(
                    r'^\s*%s\s*=' % param['inikey'], '%s' % param['inikey']+' = ', line)
                linesplit = linereplace.split(' = ', 1)
                if len(linesplit) >= 2:
                    # Exact match with 'inikey'
                    if linesplit[0] == param['inikey']:
                        # Delete blanks and newlines
                        iniValue = linesplit[1].strip()
                        if 'value' in param:
                            template = Template(param['value'])
                            iniValue = template.render({'VALUE': iniValue})
                        iniValue = utility.cast(iniValue, param.get('value_type'), trap_undefined_error)
                        tmp_table = utility.path2dict(param, iniValue)
                        utility.dict_list_marge(key_value_table, tmp_table)
                        findkey = True
                        break
                # If no key is found and there is a section
                if line.strip().startswith('['):
                    if trap_undefined_error:
                        raise LookupError(
                            'The specified KEY is missing : %s' % param['inikey'])
                    else:
                        break

        if not findsection:
            if trap_undefined_error:
                raise LookupError(
                    'The specified section is missing : %s' % param['section'])

        if not findkey:
            if trap_undefined_error:
                raise LookupError(
                    'The specified KEY is missing : %s' % param['inikey'])

    # Error when key_value_table is empty & 'trap_undefined_error' is true
    if len(key_value_table) == 0:
        if trap_undefined_error:
            raise LookupError('Value can not be acquired.')

    return key_value_table
