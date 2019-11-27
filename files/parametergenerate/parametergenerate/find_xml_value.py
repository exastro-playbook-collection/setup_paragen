#!/usr/bin/python
# -*- coding: UTF-8 -*-
import io
import re
import xml.etree.ElementTree as ET

from jinja2 import Template

from parametergenerate import utility


def find_value(target_file, search_params, encoding=None, trap_undefined_error=False):
    key_value_table = {}

    if encoding is None:
        encoding = utility.check_encode(target_file)

    with io.open(target_file, 'r', encoding=encoding) as xml_file:

        codeline = xml_file.readlines()
        match = re.search(r'^\<\?.*xml.*?encoding.*\?>', codeline[0])
        if match:
            xmlread = ''.join(codeline[1:])
        else:
            xmlread = ''.join(codeline[0:])

        xmlencode = xmlread.encode('utf-8')
        root = ET.fromstring(xmlencode)

    for param in search_params:

        if root.find(param['xpath']) is None:
            if trap_undefined_error:
                raise LookupError('The specified xpath is missing : %s' % param['xpath'])
            else:
                continue

        for e in root.findall(param['xpath']):

            if e.get(param['key']) is None:
                if trap_undefined_error:
                    raise LookupError('The specified KEY is missing : %s' % param['key'])
                else:
                    continue

            value = e.get(param['key'])
            if 'value' in param:
                template = Template(param['value'])
                value = template.render({'VALUE': value})
            value = utility.cast(value, param.get('value_type'), trap_undefined_error)
            tmp_table = utility.path2dict(param, value)
            utility.dict_list_marge(key_value_table, tmp_table)
            break

    return key_value_table
