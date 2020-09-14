#!/usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import codecs
import io
import os.path
import yaml


def save_yaml(target_file, save_data):
    if save_data == {}:
        # チケット503の解決
        yaml_bytes = b'---'
    else:
        yaml_bytes = yaml.safe_dump(
            save_data,
            allow_unicode=True,  # ユニコードをエスケープしない
            encoding='utf-8',  # バイトとして出力して、そのままファイルに書き込めるように
            default_flow_style=False,
            explicit_start=True,
            width=10000
        )

    # the save directory exist?
    save_dir = os.path.dirname(target_file)
    if (not os.path.exists(save_dir)):
        # create the save directory. (Recursively)
        os.makedirs(save_dir)

    # save yaml file.
    with io.open(target_file, 'wb') as fp:
        fp.write(yaml_bytes)
