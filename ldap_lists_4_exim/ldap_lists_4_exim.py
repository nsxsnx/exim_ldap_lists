#!/usr/bin/env python3
"""Module synchronizes mail lists from LDAP to Exim

It gets groups from MAIL_GROUPS_DN, reads active users from
those groups and writes their emails to *.acl files
with the respective names.
"""

import sys
import logging as log
from os.path import join
import ldap  # pylint: disable=E0401

# Logging preferencies:
LOGFILE = '/var/log/ldap_lists_4_exim'
LOGLEVEL = log.WARNING
# Exim preferencies:
EXIM_CONFIG_PATH = '/tmp'
# LDAP configuration:
LDAP_SERVER = 'ldap://mures.global:389'
LDAP_USER = 'CN=mail_groups_sync,CN=Users,DC=mures,DC=global'
LDAP_PASSWORD = 'XXXXXXXX'
PERSONAL_DN = 'OU=АО МЭС - Персонал,DC=mures,DC=global'
MAIL_GROUPS_DN = 'OU=mail_groups,DC=mures,DC=global'
# LDAP queries:
SEARCH_SCOPE = ldap.SCOPE_SUBTREE
SEARCH_ATTRIBUTES = ['mail']
SEARCH_GROUPFILTER = '(objectClass=group)'
SEARCH_USERS_IN_GROUP = '(&(objectCategory=person)\
                        (objectClass=user)\
                        (!(userAccountControl:1.2.840.113556.1.4.803:=2))\
                        (memberOf:1.2.840.113556.1.4.1941:={GROUP}))'


def query_ldap(ldap_connection, basedn, filter_, attributes=None, scope=SEARCH_SCOPE):
    """ Actually makes search in LDAP based on given filter and attributes """
    try:
        query_result = ldap_connection.search_s(basedn, scope, filter_, attributes)
    except ldap.LDAPError as eror:
        print(eror)
        sys.exit(1)
    return query_result


def main():  # pylint: disable=C0116
    log.basicConfig(filename=LOGFILE,
                    level=LOGLEVEL,
                    format='%(asctime)s : %(levelname)s : %(message)s')
    ldap_connection = ldap.initialize(LDAP_SERVER)
    try:
        ldap_connection.protocol_version = ldap.VERSION3
        ldap_connection.simple_bind_s(LDAP_USER, LDAP_PASSWORD)
    except ldap.INVALID_CREDENTIALS:
        log.error('LDAP username or password is incorrect.')
        sys.exit(1)
    except ldap.LDAPError as error:
        if isinstance(error.message, dict) and 'desc' in error.message:
            log.error(error.message['desc'])
        else:
            log.error(error)
        sys.exit(1)
    # Get groups from LDAP:
    mail_groups = []
    query_result = query_ldap(ldap_connection, MAIL_GROUPS_DN, SEARCH_GROUPFILTER, [''])
    log.debug('Got groups: %s', query_result)
    for res in query_result:
        mail_groups.append(res[0])
    # Get members of the groups from LDAP:
    files = {}
    for group_dn in mail_groups:
        log.debug('Querying group: %s', group_dn)
        query_filter = SEARCH_USERS_IN_GROUP.format(GROUP=group_dn)
        query_result = query_ldap(ldap_connection, PERSONAL_DN, query_filter, SEARCH_ATTRIBUTES)
        log.debug('Got users: %s', query_result)
        user_mails_list = []
        for res in query_result:
            # Extract user's e-mail:
            userfields = res[1]
            if isinstance(userfields, dict) and "mail" in userfields:
                user_mail = userfields['mail'][0].decode('utf-8')
                log.debug('Extracted mail "%s" from user "%s"', user_mail, res[0])
                user_mails_list.append(user_mail)
        group_name = group_dn.split(',')[0].split('=')[1]
        log.debug('Extracted group name "%s" from "%s"', group_name, group_dn)
        files[group_name] = user_mails_list
        log.info('%s %s', group_name, files[group_name])
    # Write e-mails to files:
    for key, value in files.items():
        filename = join(EXIM_CONFIG_PATH, key) + '.acl'
        log.debug('Writing data to file: %s', filename)
        with open(filename, 'w') as file_:
            for mail in sorted(value):
                file_.write('{}\n'.format(mail))
        log.debug('Done')
    ldap_connection.unbind_s()
    return 0


if __name__ == '__main__':
    main()
