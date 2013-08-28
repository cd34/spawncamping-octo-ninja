#!/usr/bin/env python

import ConfigParser
import datetime
import os

import boto.ec2
from webhelpers.date import distance_of_time_in_words

def logger(log, event):
    log.append('{0} - {1}'.format(datetime.datetime.now().isoformat(),
        event))

def email_report(email_address, log, time_start):
    SENDMAIL = config.get('backups', 'sendmail')
    subject = config.get('backups', 'subject')

    message = """\
From: {0}
To: {1}
Subject: {2}

{3}

Elapsed time: {4}
""".format(email_address, email_address, subject, '\n'.join(log), 
   distance_of_time_in_words(time_start))

    p = os.popen('%s -t -i' % SENDMAIL, 'w')
    p.write(message)
    status = p.close()
    if status:
        print 'Sendmail error', status

def main():
    log = []
    time_start = datetime.datetime.now()
    email_address = config.get('backups', 'email_address')

    conn = boto.ec2.connect_to_region(config.get('backups', 'region'),
         aws_access_key_id=config.get('backups', 'aws_access_key_id'),
         aws_secret_access_key=config.get('backups', 'aws_secret_access_key'))
    logger(log, 'Connecting to AWS')

    reservations = conn.get_all_instances()
    instance_id = config.get('backups', 'instance_id')

    logger(log, 'Checking to see if {0} is running'.format(instance_id))

    public_dns_name = ''
    ip_address = ''
    instance_running = False
    for reservation in reservations:
        for instance in reservation.instances:
            if instance_id in instance.id:
                if 'running' in instance._state.name:
                    public_dns_name =  instance.public_dns_name
                    ip_address = instance.ip_address
                    instance_running = True
                    logger(log, 'Instance {0} is running\n{1} {2}'. \
                        format(instance_id, public_dns_name, ip_address))
                    break
                if 'stopped' in instance._state.name:
                    instance.start()
                    logger(log, 'Starting Instance {0}'.format(instance_id))
                    """
                    delay here waiting for instance to start running
                    """
                    public_dns_name =  instance.public_dns_name
                    ip_address = instance.ip_address
                    instance_running = True
                    break

    rsync_command='{0} -e "ssh -o StrictHostKeyChecking=no" -aplxo --delete ' \
                    '{1} {2}@{3}:{4}'.format( \
                config.get('backups', 'rsync_path'),
                config.get('backups', 'backup_source'),
                config.get('backups', 'remote_username'),
                public_dns_name, config.get('backups', 'backup_dest'))

    logger(log, 'Running rsync: {0}'.format(rsync_command))
    os.system(rsync_command)

    logger(log, 'Stopping Instance {0}'.format(instance_id))
    conn.stop_instances(instance_ids=[instance_id])

    if email_address:
        email_report(email_address, log, time_start)

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(open('backup.cfg'))

    try:
        main()
    except KeyboardInterrupt:
        sys.exit()