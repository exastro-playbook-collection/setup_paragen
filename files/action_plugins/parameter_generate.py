from os import path
import sys
from parametergenerate import ParameterGenerate

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = "skipped, this module does not support check_mode."
            return result

        # get parameter
        rolename = self._task.args.get('rolename', None)
        collect_root = self._task.args.get('collect_root', None)
        config = self._task.args.get('config', None)
        dest = self._task.args.get('dest', None)
        specific = self._task.args.get('specific', None)

        # parameter check
        if rolename is None or collect_root is None or dest is None:
            result['failed'] = True
            result['msg'] = "rolename, collect_root, and dest are required."
            return result
        if config is None and specific is None:
            result['failed'] = True
            result['msg'] = "config or specific are required."
            return result

        hostname = task_vars['inventory_hostname']

        # Trim the last path delimiter.
        if(collect_root[-1:] == "/"):
            collect_root = collect_root[:-1]
        if(dest[-1:] == "/"):
            dest = dest[:-1]

        # For verbose mode (debug log)
        display.vvv("rolename = %s" % rolename)
        display.vvv("collect_root = %s" % collect_root)
        display.vvv("dest = %s" % collect_root)
        display.vvv("specific = %s" % specific)
        display.vvv("config = %s" % config)

        param_gen = ParameterGenerate(collect_root)

        if (config is not None):
            for element in config:
                try:
                    # Search the parameter from target file.
                    param_gen.find_value_common(element)
                except Exception as e:
                    raise AnsibleError("failed to get parameters from target file: %s" % str(e))

        # Execute product specific logic.
        if (specific is not None):
            try:
                param_gen.find_value_specific(specific)
            except Exception as e:
                raise AnsibleError("failed to execute product specific logic: %s" % str(e))

        # Save the parameter definition table in the yaml.
        try:
            param_gen.save(dest + '/' + hostname + '/' + rolename + '.yml')
        except Exception as e:
            raise AnsibleError("failed to write yaml file: %s" % str(e))

        return result
