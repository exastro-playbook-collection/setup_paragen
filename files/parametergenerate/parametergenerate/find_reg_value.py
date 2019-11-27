# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import io

from jinja2 import Template

from parametergenerate import utility


def find_value(target_file, search_params, encoding=None, trap_undefined_error=False):
    # auto encoding
    if encoding is None:
        encoding = utility.check_encode(target_file)
    reg = Registry(target_file, encoding=encoding)

    v_params = [ValidatedParam(p) for p in search_params]
    regpaths = [p.regpath for p in v_params]
    not_found_indexes = set(range(len(search_params)))
    key_value_table = {}
    for i, entry in reg.find_many(regpaths):
        not_found_indexes.remove(i)
        p = v_params[i]
        value = {
            # レジストリ値の変化は普通より難しいと思いますので、
            # 先に、レジストリで対応したほうがいいかと思います
            # 'int': entry.value.as_int
            # 'bool': entry.value.as_bool
            # ...
        }.get(p.value_type, entry.value.as_default)()

        if p.template:
            value = p.template.render({'VALUE': value})
        value = utility.cast(value, p.value_type, trap_undefined_error)

        tmp_table = utility.path2dict(search_params[i], value)
        utility.dict_list_marge(key_value_table, tmp_table)

    if not_found_indexes:
        if trap_undefined_error:
            not_found = [v_params[i].regpath for i in not_found_indexes]
            raise KeyError('No matches for: {}'.format(', '.join(not_found)))

    return key_value_table


class ValidatedParam:
    def __init__(self, param_dict):
        keys, valuename, template, value_type = self._parse(param_dict)
        self.keys = Keys(keys)
        self.valuename = valuename
        self.template = template
        self.value_type = value_type
        self.regpath = '{}{}{}'.format(keys, Entry.KEY_VALUE_DELIMITER, valuename)

    @staticmethod
    def _parse(param):
        try:
            keys = param['keys']
        except KeyError:
            raise KeyError('"keys" is required in params')

        try:
            valuename = param['value_name']
        except KeyError:
            raise KeyError('"value_name" is required in params')

        template = param.get('value')
        if template is not None:
            template = Template(template)

        value_type = param.get('value_type')

        return keys, valuename, template, value_type


class Registry:
    file_path = None
    encoding = None

    def __init__(self, file_path, encoding='utf-16'):
        self.file_path = file_path
        self.encoding = encoding

    def find_many(self, regpaths):
        """Generate (regpath_index, entry) where entry matches regpath.

        args:
            params: iterable of ValidatedParameter
        """
        for entry in self.entries():
            for i, regpath in enumerate(regpaths):
                if entry.path() == regpath:
                    yield i, entry

    def find(self, regpath):
        """Return entry matching vparam or None if not found."""
        for _, entry in self.find_many([regpath]):
            return entry
        return None

    def entries(self):
        """Generate all entries in this registry."""
        with io.open(self.file_path, encoding=self.encoding) as f:
            while True:
                key = self._next_key(f)
                if key is None:
                    break  # end of file
                # generate the key alone as an entry
                yield Entry(key, None)

                # generate every key + value pair as entries
                for v in self._next_values(f):
                    yield Entry(key, v)

    def _next_key(self, iter_lines):
        """Iterate through the lines and stop when one key or end of file found."""
        while True:
            line = next(iter_lines, None)
            if line is None:
                return None  # end of file

            if line.startswith('[HKEY'):
                key_without_brackets = line.strip()[1:-1]
                return Keys(key_without_brackets)

    def _next_values(self, iter_lines):
        """Iterate through the lines and stop when no more values or end of file found."""
        while True:
            value = self._next_value(iter_lines)
            if value is None:
                break
            yield value

    def _next_value(self, iter_lines):
        """Iterate through the lines and stop when one value or end of file found."""
        lines = []
        while True:
            line = next(iter_lines, None)
            if line is None:
                break  # end of file
            line = line.strip()
            lines.append(line)
            has_more_lines = line.endswith('\\')

            if has_more_lines:
                continue
            else:
                break

        # combine all the lines
        value_str = '\n'.join(lines)

        # no value
        if not value_str:
            return None

        # parse the value string
        return value_from_string(value_str)


class Entry:
    """A single key [+ value] entry in the windows registry."""
    key = None
    value = None
    KEY_VALUE_DELIMITER = '\\\\'

    def __init__(self, key, value):
        self.key, self.value = key, value

    def path(self):
        p = self.key.path()
        if self.value:
            p = '{}{}{}'.format(
                p, self.KEY_VALUE_DELIMITER, self.value.name
            )
        return p

class Keys:
    _KEY_DELIMITER = '\\'
    _ROOT_KEYS = {
        'HKEY_CLASSES_ROOT',
        'HKEY_CURRENT_CONFIG',
        'HKEY_CURRENT_USER',
        'HKEY_LOCAL_MACHINE',
        'HKEY_PERFORMANCE_DATA',
        'HKEY_USERS',
    }
    _key_string = None

    def __init__(self, key_string):
        self._key_string = self._validate_key_string(key_string)

    def path(self):
        return self._key_string

    def _validate_key_string(self, key_string):
        """Passes through key string.

        Raises ValueError if keys are not within specification.
        """
        key_strings = key_string.split(self._KEY_DELIMITER)
        root_key = key_strings[0]
        if root_key.upper() not in self._ROOT_KEYS:
            raise ValueError('root key is "{}" but it must be one of ({})'
            ''.format(root_key, ', '.join(sorted(self._ROOT_KEYS))))

        return key_string


class _Value(object):
    # set on each class
    TYPE_PREFIX = None

    # set values @init
    reg_string = None
    name = None
    data_string = None

    def __init__(self, reg_string, name, data_string):
        self.reg_string = reg_string
        self.name = name
        self.data_string = data_string


class ValueNone(_Value):
    TYPE_PREFIX = 'hex(0):'
    def as_default(self):
        return None

    @classmethod
    def from_typedata_string(cls, reg_string, name, _):
        return cls(reg_string, name, None)


class ValueString(_Value):
    TYPE_PREFIX = '"'
    def as_default(self):
        return self.as_string()

    def as_string(self):
        return self.data_string

    @classmethod
    def from_typedata_string(cls, reg_string, name, typedata_string):
        data = typedata_string.split(cls.TYPE_PREFIX, 1)[1]
        # Remove the last quote because the first quote is removed as the prefix
        data = data[:-1]
        # must unescape \ and " for non-hex strings
        data = data.replace('\\\\', '\\')
        data = data.replace('\\"', '"')
        return cls(reg_string, name, data)

class ValueMultiString(_Value):
    TYPE_PREFIX = 'hex(7):'
    def as_default(self):
        return '{}{}'.format(self.TYPE_PREFIX, self.data_string)

    @classmethod
    def from_typedata_string(cls, reg_string, name, typedata_string):
        data = typedata_string.split(cls.TYPE_PREFIX, 1)[1]
        return cls(reg_string, name, data)


class ValueExpandString(ValueMultiString):
    # this will need more implementation for anything except hex output
    TYPE_PREFIX = 'hex(2):'


class ValueBinary(ValueMultiString):
    # this will need more implementation for anything except hex output
    TYPE_PREFIX = 'hex:'


class ValueQWord(ValueMultiString):
    TYPE_PREFIX = 'hex(b):'
    def as_default(self):
        return self.as_int()

    def as_int(self):
        hex_pairs = self.data_string.split(',')
        hexlike = ''.join(reversed(hex_pairs))
        return int(hexlike, 16)


class ValueDWordHex(ValueQWord):
    TYPE_PREFIX = 'hex(4):'


class ValueDWordNum(_Value):
    TYPE_PREFIX = 'dword:'
    def as_default(self):
        return self.as_int()

    def as_int(self):
        return int(self.data_string, 16)

    @classmethod
    def from_typedata_string(cls, reg_string, name, typedata_string):
        data = typedata_string.split(cls.TYPE_PREFIX, 1)[1]
        return cls(reg_string, name, data)


def value_from_string(s):
    one_line = _normalize_value_string(s)

    if one_line.startswith('@='):
        # default values for keys have a special format: @=...
        name, type_and_data = one_line.split('=', 1)
    else:
        # <  =  > is the name-data delimiter.
        # However, the name also might have "=" so we use <  "=  >.
        # This fails in the case that value name also has <  "=  >.
        name, type_and_data = one_line.split('"=', 1)
        name = name[1:]  # remove open quote

    value_classes = [
        ValueNone,
        ValueString,
        ValueMultiString,
        ValueExpandString,
        ValueBinary,
        ValueDWordHex,
        ValueDWordNum,
        ValueQWord
    ]

    VClass = None
    for C in value_classes:
        if type_and_data.startswith(C.TYPE_PREFIX):
            VClass = C
            # collect any data after the prefix (but not if it is empty)
    if VClass is None:
        raise ValueError('unknown value type in: {}. Expected one of ({})'
        ''.format(s, ','.join(c.TYPE_PREFIX for c in value_classes)))
    return VClass.from_typedata_string(s, name, type_and_data)


def _normalize_value_string(s):
    """Flatten value into a single line."""
    final_lines = []
    for line in s.splitlines():
        line = line.strip()
        # remove line continuation \
        if line.endswith('\\'):
            line = line[:-1]
        final_lines.append(line)
    return ''.join(final_lines)
