#!/usr/bin/python
# -*- coding: UTF-8 -*-
import io
import json
import re

from jinja2 import Template

from parametergenerate import utility


def __peeler(_expr, _path):
    _path = _path.strip()
    ismatch = re.match(_expr, _path)
    if ismatch is None:
        return None
    _value = ismatch.group()
    _path = re.sub('^' + _expr, '', _path)

    return [_value, _path]


def __opener(_path):
    result = __peeler(r'\[', _path)
    if result is None:
        return None
    _path = result[1]

    _type = "list"
    result = __peeler(r'[0-9]+', _path)
    if result is None:
        _type = "dict"
        result = __peeler(r'(\"[^\"]*\"|\'[^\']*\')', _path)
        if result is None:
            return None
        result[0] = result[0][1:-1]
    _path = result[1]
    _content = {
        "value": result[0],
        "type": _type}

    result = __peeler(r'\]', _path)
    if result is None:
        return None
    _path = result[1]

    return [_content, _path]


def find_value(target_file, search_params, encoding=None, trap_undefined_error=False):

    # auto encoding
    if encoding is None:
        encoding = utility.check_encode(target_file)

    key_value_table = {}

    # load jsondata
    with io.open(target_file, 'r', encoding=encoding) as json_file:
        json_data = json.load(json_file)

    for param in search_params:
        json_path = []

        # parse json_path string
        result = __peeler(r'\$', param["path"])
        if result is None:
            msg = 'no root found in path({0})'
            raise KeyError(msg.format(param["path"]))

        # parse json_path string
        while result is not None:
            if result[0] != '$':
                json_path.append(result[0])
                if result[1] == '':
                    break
            result = __opener(result[1])
        if result is None:
            msg = 'syntax error found in path({0})'
            raise KeyError(msg.format(param["path"]))

        try:
            # pickup value
            result = json_data
            for key in json_path:
                if key["type"] == "list":
                    suffix = key["value"]
                    suffix = int(suffix)
                    if type(result) != list:
                        msg = 'key([{1}]) in path({0}) points to non-array'
                        raise KeyError(msg.format(param["path"], suffix))
                    if len(result) <= suffix:
                        msg = 'key([{1}]) in path({0}) out of range'
                        raise KeyError(msg.format(param["path"], suffix))
                else:
                    suffix = key["value"]
                    if type(result) != dict:
                        msg = 'key([{1}]) in path({0}) points to non-object'
                        raise KeyError(msg.format(param["path"], suffix))
                    if suffix not in result:
                        msg = 'invalid key([{1}]) found in path({0})'
                        raise KeyError(msg.format(param["path"], suffix))
                result = result[suffix]
            value = result

            # push table
            if 'value' in param:
                template = Template(param['value'])
                value = template.render({'VALUE': value})
            value = utility.cast(value, param.get('value_type'), trap_undefined_error)
            tmp_table = utility.path2dict(param, value)
            utility.dict_list_marge(key_value_table, tmp_table)

        except KeyError as e:
            if trap_undefined_error is True:
                raise e
        except Exception as e:
            raise e

    return key_value_table
