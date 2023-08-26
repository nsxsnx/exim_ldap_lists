=================
LDAP lists to Exim Readme
=================
-------------------------
Synchronization of mail lists from LDAP to Exim4 *.acl config
-------------------------

Introduction
============

This package gets groups from MAIL_GROUPS_DN, reads active users from
those groups and writes their emails to *.acl files
with the respective names.

Dependencies
============

Some libraries are required to build python-ldap module during installatuion with Poetry.
For Debian they are as follows:

sudo apt install python3-dev libsasl2-dev libldap2-dev libssl-dev

Installation
============

git clone https://github.com/nsxsnx/exim_ldap_lists.git

cd exim_ldap_lists/

poetry install

Configuration
============

Just change your preferencies at the very beginning of the script to connect to your LDAP server.

Run script with cron as root:

sudo crontab -e

Add line:

07 01 * * * cd /root/exim-ldap_lists && /usr/local/bin/poetry run python3 ./exim_ldap_lists/ldap_lists_4_exim.py

