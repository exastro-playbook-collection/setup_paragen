#!/usr/bin/python
# -*- coding: UTF-8 -*-
import io
import re

from jinja2 import Template

from parametergenerate import utility


def find_value(target_file, search_params, encoding=None, trap_undefined_error=False):

    # auto encoding
    if encoding is None:
        encoding = utility.check_encode(target_file)

    # return value list.
    key_value_table = {}

    # open a file. if raise exception, caller catches exception.
    with io.open(target_file, "r", encoding=encoding) as f:
        # read and process line by line.
        for line in f:
            # process parameters one by one.
            for param in search_params:
                # processed parameter is skipped.
                if 'processed' in param:
                    continue
                match = re.match(param['regexp'], line)
                if match:
                    # found match.
                    value = match.group(1)
                    # processed flag is set.
                    param['processed'] = True
                    if 'value' in param:
                        template = Template(param['value'])
                        value = template.render({'VALUE': value})
                    value = utility.cast(value, param.get('value_type'), trap_undefined_error)
                    tmp_table = utility.path2dict(param, value)
                    utility.dict_list_marge(key_value_table, tmp_table)

    # all value have benn found?
    if trap_undefined_error:
        for param in search_params:
            # raise an exception if there is one that is not found even for one case.
            if 'processed' not in param:
                raise ValueError('Regex(' + param['regexp'] + ') does not match.')

    return key_value_table
