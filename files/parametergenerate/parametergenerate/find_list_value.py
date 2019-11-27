# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import namedtuple, OrderedDict
import io
import re

from jinja2 import Template

from parametergenerate import utility


try:
    #py2
    unicode=unicode
except NameError:
    #py3
    unicode=str


def find_value(target_file, search_params,
               encoding=None, trap_undefined_error=False):
    # auto encoding
    if encoding is None:
        encoding = utility.check_encode(target_file)
    collector = ListCollector(target_file, encoding=encoding)

    v_params = [ValidatedParam(p) for p in search_params]
    param_elements = [[] for _ in v_params]
    for i, element in collector.elements_many(v_params):
        p = v_params[i]
        if p.template:
            element = _apply_template(p.template, element)
        element = _apply_cast(p.value_type, element, trap_undefined_error)
        # pyyamlはOrderedDict対応していないため、一般のdictに変更。
        # 入力の順番通りにする方法１つはpyyamlをruamel.yamlに更新
        param_elements[i].append(dict(element))

    # 収集した複数のelementを結ぶ
    key_value_table = {}
    for s_param, elements in zip(search_params, param_elements):
        if not elements:
            if trap_undefined_error:
                raise KeyError('no matches found for {}'.format(s_param))
        else:
            # elementがある場合のみ、結果の配列を出力に入れる
            tmp_table = utility.path2dict(s_param, elements)
            utility.dict_list_marge(key_value_table, tmp_table)

    return key_value_table


def _apply_template(template, element):
    e = {}
    for k, v in element.items():
        e[k] = template.render({'VALUE': v})
    return e


def _apply_cast(v_type, element, trap_undefined_error):
    e = {}
    for k, v in element.items():
        e[k] = utility.cast(v, v_type, trap_undefined_error)
    return e


class ValidatedParam:
    def __init__(self, param_dict):
        regexp, element_names, ignore, template, value_type = self._parse(param_dict)
        self._validate(regexp, element_names)

        self.regexp = regexp
        self.element_names = element_names
        self.ignore = ignore
        self.template = template
        self.value_type = value_type

    @staticmethod
    def _parse(param):
        try:
            regexp = param['regexp']
            element_names = param['element']
        except KeyError:
            raise KeyError('"regexp" and "element" are required in param')
        regexp = re.compile(regexp)
        element_names = [unicode(en) for en in element_names]

        template = param.get('value')
        if template is not None:
            template = Template(template)

        value_type = param.get('value_type')

        ignore = param.get('ignore')

        return regexp, element_names, ignore, template, value_type

    @staticmethod
    def _validate(regexp, element_names):
        name_count = len(element_names)
        if name_count == 0:
            raise ValueError('At least one item is required in element.')
        group_count = re.compile(regexp).groups
        if group_count != name_count:
            raise ValueError('The number of element items ({}) '
                             'and number of regexp capture groups ({}) '
                             'should match.'.format(name_count, group_count))


class ListCollector:
    def __init__(self, file_path, encoding='utf-8'):
        self.file_path = file_path
        self.encoding = encoding

    def elements_many(self, params):
        """Generate (param_index, element) where element matches param conditions.

        args:
            params: iterable of ValidatedParameter
        """
        for line in self._lines():
            for i, p in enumerate(params):
                element = self._detect_element(line, p)
                if element:
                    yield i, element

    def elements(self, param):
        """Generate each element matching param conditions

        args:
            param ValidatedParameter
        """
        for _, element in self.elements_many([param]):
            yield element

    def _detect_element(self, line, param):
        if param.ignore is not None:
            if line.lstrip().startswith(param.ignore):
                return
        found = param.regexp.match(line)
        if found is None:
            return
        return OrderedDict(zip(param.element_names, found.groups()))

    def _lines(self):
        with io.open(self.file_path, encoding=self.encoding) as f:
            for line in f:
                line = line.rstrip('\n')
                yield line
