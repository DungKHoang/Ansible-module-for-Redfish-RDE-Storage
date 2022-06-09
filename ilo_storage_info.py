#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author: Dung.HoangKhac@hpe.com
# Objective: Get all storage ( SmartStorage - localStorage)
# Prerequisites:
#   - iLO fw > 2.65
#   - Storage fw > 5.0 

from __future__ import absolute_import, division, print_function

from itertools import count
from urllib import response
__metaclass__ = type

import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.general.plugins.module_utils.redfish_utils import RedfishUtils

CATEGORY_COMMANDS_ALL = {
    "Controller":           [   "GetStorageController"
                            ],
    "Disk":                 [   "GetPhysicalDisk",
                                "GetLogicalDisk"
                            ]
}

CATEGORY_COMMANDS_DEFAULT = {
    "Controller":           [   "GetStorageController"
                            ]
}


STORAGE_URL              = "/redfish/v1/Systems/1/Storage/"



def remove_odata(output):
    # Remove odata variables given in the list
    remove_list = ["@odata.context", "@odata.etag",  "@odata.type"] # "@odata.id",
    for key in remove_list:
        if key in output:
            output.pop(key)
    return output




def _get_data(rf_utils, entry):
    _uri        = rf_utils.root_uri + entry
    response    = rf_utils.get_request(_uri)
    data        = response['data']
    _data_out   = remove_odata(data)
    return _data_out

def get_controller(rf_utils, data):
    result              = {}
    controller_results  = []

    for _m in data[u'Members']:
        _storage    = _get_data(rf_utils, _m[u'@odata.id']) #//redfish/v1/systems/1/Storage/Dxxxxxxx
        _name       = _storage[u'Name']
        # Check if StorageControllers or Controllers only
        if 'StorageControllers' in _storage.keys():
            for _controller in _storage[u'StorageControllers']:
                _controller[u'Name'] = _name
                controller_results.append(_controller)
            
        else:
            # Controllers here
            _cont_uri    = _storage[u'Controllers'][u'@odata.id']
            _cont        = _get_data(rf_utils, _cont_uri)
            for _m in _cont[u'Members']:
                _controller = _get_data(rf_utils, _m[u'@odata.id'])
                controller_results.append(_controller)

    result[u'entries']   = controller_results
    result[u'count']    = len(controller_results)

    return result
    

def get_physical_disk(rf_utils, data):
    result              = {}
    phys_disk_results   = []

    
    for _m in data[u'Members']:
        _storage    = _get_data(rf_utils, _m[u'@odata.id'])  #//redfish/v1/systems/1/Storage/Dxxxxxxx
        for _d in _storage[u'Drives']:
            _drive  = _get_data(rf_utils, _d[u'@odata.id'])  #//redfish/v1/systems/1/Storage/Dxxxxxxx/Drives/x
            phys_disk_results.append(_drive)

    result[u'entries']  = phys_disk_results
    result[u'count']    = len(phys_disk_results)

    return result
    
def get_logical_disk(rf_utils, data):
    result              = {}
    log_disk_results    = []

    
    for _m in data[u'Members']:
        _storage    = _get_data(rf_utils, _m[u'@odata.id'])                         #//redfish/v1/systems/1/Storage/Dxxxxxxx
        if 'Volumes' in _storage.keys():
            _volumes    = _get_data(rf_utils, _storage[u'Volumes'][u'@odata.id'])       #//redfish/v1/systems/1/Storage/Dxxxxxxx/Volumes
            for _m in _volumes[u'Members']:                               
                _volume  = _get_data(rf_utils, _m[u'@odata.id'])                        #//redfish/v1/systems/1/Storage/Dxxxxxxx/Volumes/1
                log_disk_results.append(_volume)

    result[u'entries']  = log_disk_results
    result[u'count']    = len(log_disk_results)

    return result

def main():
    result = {}
    category_list = []
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(type='list', elements='str', default=['Storage']),
            command=dict(type='list', elements='str'),
            baseuri=dict(required=True),
            username=dict(),
            password=dict(no_log=True),
            auth_token=dict(no_log=True),
            timeout=dict(type='int', default=10)
        ),
        required_together=[
            ('username', 'password'),
        ],
        required_one_of=[
            ('username', 'auth_token'),
        ],
        mutually_exclusive=[
            ('username', 'auth_token'),
        ],
        supports_check_mode=True,
    )

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password'],
             'token': module.params['auth_token']}

    # timeout
    timeout = module.params['timeout']

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_utils = RedfishUtils(creds, root_uri, timeout, module)

        # Build Category list
    if "all" in module.params['category']:
        for entry in CATEGORY_COMMANDS_ALL:
            category_list.append(entry)
    else:
        # one or more categories specified
        category_list = module.params['category']

    for category in category_list:
        command_list = []
        # Build Command list for each Category
        if category in CATEGORY_COMMANDS_ALL:
            if not module.params['command']:
                # True if we don't specify a command --> use default
                command_list.append(CATEGORY_COMMANDS_DEFAULT[category])
            elif "all" in module.params['command']:
                for entry in range(len(CATEGORY_COMMANDS_ALL[category])):
                    command_list.append(CATEGORY_COMMANDS_ALL[category][entry])
            # one or more commands
            else:
                command_list = module.params['command']
                # Verify that all commands are valid
                for cmd in command_list:
                    # Fail if even one command given is invalid
                    if cmd not in CATEGORY_COMMANDS_ALL[category]:
                        module.fail_json(msg="Invalid Command: %s" % cmd)
        else:
            # Fail if even one category given is invalid
            module.fail_json(msg="Invalid Category: %s" % category)
    
        # Organize by Categories / Commands
        if category == "Controller":
            response    = rf_utils.get_request(root_uri + STORAGE_URL)
            for command in command_list:
                if command == "GetStorageController":
                    result["controller"] = get_controller(rf_utils,response['data']) 

        if category == "Disk":
            response    = rf_utils.get_request(root_uri + STORAGE_URL)
            for command in command_list:
                if command == "GetPhysicalDisk":
                    result["physical_disk"] = get_physical_disk(rf_utils,response['data']) 
                if command == "GetLogicalDisk":
                    result["logical_disk"] = get_logical_disk(rf_utils,response['data']) 


    # Return data back
    module.exit_json(redfish_facts=result)


if __name__ == '__main__':
    main()




