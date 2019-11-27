# Ansible Role: setup_paragen

## Trademarks

* Linuxは、Linus Torvalds氏の米国およびその他の国における登録商標または商標です。
* RedHat、RHEL、CentOSは、Red Hat, Inc.の米国およびその他の国における登録商標または商標です。
* Windows、PowerShellは、Microsoft Corporation の米国およびその他の国における登録商標または商標です。
* Ansibleは、Red Hat, Inc.の米国およびその他の国における登録商標または商標です。
* pythonは、Python Software Foundationの登録商標または商標です。
* NECは、日本電気株式会社の登録商標または商標です。
* その他、本ロールのコード、ファイルに記載されている会社名および製品名は、各社の登録商標または商標です。

## Description

本ロールではパラメータ生成共通部品を指定したAnsibleサーバーにインストールします。

パラメータ生成共通部品とは、収集ロールを利用するために必要となるモジュールで以下機能を有します。
1. 構築済みサーバーから収集した設定情報から必要な値を抽出する
2. 抽出した値をパラメータ変数とマッピング（Key/Value）する
3. マッピングしたパラメータをYAML形式で出力する

## Supports

パラメータ生成共通部品は以下環境での動作をサポートします。

- Ansibleサーバー（本ロールのインストール先）
  - OS：RHEL7.5（CentOS7.5）
  - Ansible：Version 2.7
  - Python：2.7 or 3.6
- 対象ホスト側（パラメータ生成共通部品の解析対象）
  - 利用する収集ロールに準拠します

## Requirements

* 本ロールではインストール先にあらかじめAnsibleがインストールされている必要があります。
* 本ロールはインストール先のsudo実行権限を持つユーザーで実行する必要があります。

## Role Variables

無し

## Dependencies

無し

## Example Playbook

    - hosts: local
      become: yes
      roles:
        - setup_paragen

## License

Apache License 2.0

## Author Information

None

