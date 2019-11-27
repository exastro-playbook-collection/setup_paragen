#!/usr/bin/python
# -*- coding: UTF-8 -*-
import subprocess
import json


def find_specific_value(script, collect_root):
    # Create argument.
    args = script.split(" ")
    args.append(collect_root)
    # Execute the specific script.
    try:
        res = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        raise Exception('Error: return=' + e.returncode + 'cmd=' + e.cmd)

    # Convert JSON of standard output to dictionary.
    return json.loads(res)
