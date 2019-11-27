#!/usr/bin/python
# -*- coding: UTF-8 -*-
import chardet
from collections import MutableSequence, MutableMapping
import io
import re


def dict_list_marge(src1, src2):
    for key in src2:
        if key in src1:
            if (isinstance(src2[key], list)):
                for index, item in enumerate(src2[key]):
                    if (isinstance(item, dict)):
                        if (len(src1[key]) < index + 1):
                            src1[key].append(src2[key][index])
                        else:
                            src1[key][index] = dict_list_marge(src1[key][index], src2[key][index])
                    else:
                        if (item is not None):
                            src1[key].append(item)
            elif (isinstance(src2[key], dict)):
                src1[key] = dict_list_marge(src1[key], src2[key])
            else:
                src1[key] = src2[key]
        else:
            src1[key] = src2[key]
    return src1


def __str2str(value):
    return value


def __str2int(value):
    # Return None for None
    if value is None:
        return None
    # Return None for empty string
    try:
        if value.strip() == '':
            return None
    except AttributeError:
        pass
    # Allow errors for other non-integer values
    return int(value)


def __str2bool(value):
    if value in {True, False}:
        return value
    temp = value.lower()
    if temp not in {"true", "false"}:
        raise ValueError("bool must be true or false")
    if temp == "false":
        return(False)
    else:
        return(True)


def __str2float(value):
    # Return None for None
    if value is None:
        return None
    # Return None for empty string
    try:
        if value.strip() == '':
            return None
    except AttributeError:
        pass
    return float(value)


def split_path(python_path, separator):
    return python_path.lstrip(separator).split(separator)


def path_types(obj, path_list):
    result = []
    current = obj
    for index, element in enumerate(path_list[:-1]):
        # print(element)
        re_result = re.match(r'^\[([0-9]+)\]$', element)
        if re_result:
            element = re_result.group(1)
            path_list[index] = element
        if ((issubclass(current.__class__, MutableMapping) and element in current)):
            # print("-path_types(MutableMapping):", element, current)
            result.append([element, current[element].__class__])
            current = current[element]
        elif (issubclass(current.__class__, MutableSequence) and int(element) < len(current)):
            # print("-path_types(MutableSequence):", element, current)
            element = int(element)
            result.append([element, current[element].__class__])
            current = current[element]
        else:
            # print("-path_types(else):", element)
            re_result = re.match(r'^\[([0-9]+)\]$', path_list[index + 1])
            if re_result:
                result.append([element, list])
                path_list[index + 1] = re_result.group(1)
            else:
                result.append([element, dict])

    try:
        try:
            result.append([path_list[-1], current[path_list[-1]].__class__])
        except TypeError:
            result.append([path_list[-1], current[int(path_list[-1])].__class__])
    except (KeyError, IndexError, ValueError):
        result.append([path_list[-1], path_list[-1].__class__])
    return result


def set_obj(obj, path_obj, value, create_parent=True, afilter=None):
    traversed = []

    def _is_exist_dict(obj, element):
        return (element[0] in obj)

    def _create_parent_dict(obj, element):
        obj[element[0]] = element[1]()

    def _get_dict(obj, element):
        return obj[element[0]]

    def _set_value_dict(obj, element, value):
        obj[element[0]] = value

    def _is_exist_list(obj, element):
        return (int(str(element[0])) < len(obj))

    def _create_parent_list(obj, element):
        index = int(str(element[0]))
        for i in range(len(obj), index + 1):
            if (i == index):
                obj.append(element[1]())
            else:
                obj.append(None)

    def _get_list(obj, element):
        return obj[int(str(element[0]))]

    def _set_value_list(obj, element, value):
        obj[int(str(element[0]))] = value

    element = None
    for element in path_obj:
        element_value = element[0]

        tester = None
        creator = None
        accessor = None
        assigner = None
        if issubclass(obj.__class__, MutableMapping):
            # print("-issubclass MutableMapping:", element_value)
            tester = _is_exist_dict
            creator = _create_parent_dict
            accessor = _get_dict
            assigner = _set_value_dict
        elif issubclass(obj.__class__, MutableSequence):
            # print("-issubclass MutableSequence:", element_value)
            if not str(element_value).isdigit():
                raise TypeError("Can only create integer indexes in lists, "
                                "not {}, in {}".format(type(obj),
                                                       traversed
                                                       )
                                )
            tester = _is_exist_list
            creator = _create_parent_list
            accessor = _get_list
            assigner = _set_value_list
        else:
            raise TypeError("Invalid elements of type {} "
                            "at {}".format(obj, traversed))

        if (not tester(obj, element)) and (create_parent):
            creator(obj, element)
        elif (not tester(obj, element)):
            raise Exception(
                "{} does not exist in {}".format(
                    element,
                    traversed
                    )
                )
        traversed.append(element_value)
        if len(traversed) < len(path_obj):
            obj = accessor(obj, element)

    if element is None:
        return
    if (afilter and afilter(accessor(obj, element))) or (not afilter):
        assigner(obj, element, value)


def cast(v, v_type, trap_undefined_error):
    casters = {
        None: __str2str,
        'str': __str2str,
        'int': __str2int,
        'bool': __str2bool,
        'float': __str2float
    }
    try:
        caster = casters[v_type]
    except KeyError:
        caster_list = ', '.join(str(c) for c in casters)
        raise KeyError('Unknown value_type ({}). Expected one of ({})'
                        ''.format(v_type, caster_list))
    cast_v = caster(v)

    # any cast can return None for "missing" value
    if trap_undefined_error and (cast_v is None) and (v_type is not None):
        raise ValueError('Could not cast value ({}) to requested type ({})'
                        ''.format(v, v_type))
    return cast_v


def path2dict(param, value):
    yaml_path = param.get('variable', None)
    table = {}
    path_list = split_path(yaml_path, "/")
    path_obj = path_types(table, path_list)
    set_obj(table, path_obj, value, create_parent=True)
    # print("DEBUG:",table)
    return table


def check_encode(target_file):
    with io.open(target_file, 'rb') as f:
        char_code = chardet.detect(f.read())
        file_encode = char_code['encoding']
    return file_encode
