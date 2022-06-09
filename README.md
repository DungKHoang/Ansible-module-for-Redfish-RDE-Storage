# Ansible-module-for-Redfish-RDE-Storage

Ansible module to manage RDE storage with iLO RedFish

## Pre-requisites
 - RHEL OS - current release
 - Python3 - current release
 - Ansible - current release
 - Redfish python library installed: pip3 install redfish==3.0.2
 - Refish collection from RedHat community: ansible-galaxy collection install community.general
 - HPE iLO collection from RedHat: ansible-galaxy collection install hpe.ilo

 - Target servers: 
   - iLO firmware > 2.65
   - [PLDM RDE](https://developer.hpe.com/blog/overview-of-the-platform-level-data-model-for-redfish%C2%AE-device-enablement-standard/) Storage controllers(SR, MR, NS controllers) firmware: 5.00  
