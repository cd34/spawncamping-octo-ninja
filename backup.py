#!/usr/bin/env python

import configparser
import datetime
import humanize
import os
import sys
import time

import boto3.ec2


def logger(log, event):
    log.append("{0} - {1}".format(datetime.datetime.now().isoformat(), event))


def email_report(email_address, log, time_start):
    SENDMAIL = config.get("backups", "sendmail")
    subject = config.get("backups", "subject")

    message = """\
From: {0}
To: {1}
Subject: {2}

{3}

Elapsed time: {4}
""".format(
        email_address,
        email_address,
        subject,
        "\n".join(log),
        humanize.naturaldelta(datetime.datetime.now() - time_start),
    )

    p = os.popen("%s -t -i" % SENDMAIL, "w")
    p.write(message)
    status = p.close()
    if status:
        print("Sendmail error", status)


def get_instance(conn, instance_id):
    instances = conn.describe_instances()
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            if instance_id in instance["InstanceId"]:
                return instance
    return "unknown"


def wait_for_instance(conn, instance_id, log):
    instance = get_instance(conn, instance_id)
    if instance["State"]["Name"] == "stopped":
        aaa = conn.start_instances(InstanceIds=[instance_id])
    loop = 0
    while not instance["State"]["Name"] == "running":
        time.sleep(10)
        loop += 1
        if loop > 10:
            logger(
                log,
                "Waited and Instance {0} won't "
                "start: {1}".format(instance_id, instance["State"]["Name"]),
            )
            return False
        instance = get_instance(conn, instance_id)
    # even though status is running, machine isn't always accessible
    # immediately
    time.sleep(60)
    return True


def main():
    log = []
    time_start = datetime.datetime.now()
    email_address = config.get("backups", "email_address")

    conn = boto3.client(
        "ec2",
        region_name=config.get("backups", "region"),
        aws_access_key_id=config.get("backups", "aws_access_key_id"),
        aws_secret_access_key=config.get("backups", "aws_secret_access_key"),
    )
    logger(log, "Connecting to AWS")

    instance_id = config.get("backups", "instance_id")

    logger(log, "Checking to see if {0} is running".format(instance_id))

    public_dns_name = ""
    ip_address = ""
    instance_running = False
    instance = get_instance(conn, instance_id)
    if instance["State"]["Name"] == "running":
        public_dns_name = instance["PublicDnsName"]
        ip_address = instance["PublicIpAddress"]
        instance_running = True
        logger(
            log,
            "Instance {0} is running\n{1} {2}".format(
                instance_id, public_dns_name, ip_address
            ),
        )
    elif instance["State"]["Name"] == "stopped":
        logger(log, "Starting Instance {0}".format(instance_id))
        instance_running = wait_for_instance(conn, instance_id, log)
        if instance_running:
            logger(log, "Spawned and Started Instance {0}".format(instance_id))
            instance = get_instance(conn, instance_id)
            public_dns_name = instance["PublicDnsName"]
            ip_address = instance["PublicIpAddress"]
    else:
        logger(log, "Waiting for Instance {0}".format(instance_id))
        instance_running = wait_for_instance(conn, instance_id, log)
        if instance_running:
            logger(log, "Spawned and Started Instance {0}".format(instance_id))
            public_dns_name = instance["PublicDnsName"]
            ip_address = instance["PublicIpAddress"]
        else:
            logger(log, "Couldn't Start Instance {0}".format(instance_id))
            return
        logger(log, "Waited and Started Instance {0}".format(instance_id))

    if instance_running:
        rsync_command = (
            '{0} -e "ssh -o StrictHostKeyChecking=no" -aplxo '
            "--delete {1} {2}@{3}:{4}".format(
                config.get("backups", "rsync_path"),
                config.get("backups", "backup_source"),
                config.get("backups", "remote_username"),
                public_dns_name,
                config.get("backups", "backup_dest"),
            )
        )

        logger(log, "Running rsync: {0}".format(rsync_command))
        os.system(rsync_command)

    logger(log, "Stopping Instance {0}".format(instance_id))
    conn.stop_instances(InstanceIds=[instance_id])

    if email_address:
        email_report(email_address, log, time_start)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read_file(
        open(os.path.join("/".join(sys.argv[0].split("/")[:-1]), "backup.cfg"))
    )

    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
