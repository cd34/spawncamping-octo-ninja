#!/usr/bin/env python3

import configparser
import datetime
import os
import subprocess
import sys
import time

import boto3
import humanize


def logger(log, event):
    log.append(f"{datetime.datetime.now().isoformat()} - {event}")


def email_report(config, email_address, log, time_start):
    sendmail = config.get("backups", "sendmail")
    subject = config.get("backups", "subject")

    message = (
        f"From: {email_address}\n"
        f"To: {email_address}\n"
        f"Subject: {subject}\n\n"
        f"{'\n'.join(log)}\n\n"
        f"Elapsed time: {humanize.naturaltime(datetime.datetime.now() - time_start)}\n"
    )

    result = subprocess.run(
        [sendmail, "-t", "-i"],
        input=message,
        text=True,
    )
    if result.returncode:
        print("Sendmail error", result.returncode)


def get_instance(conn, instance_id):
    instances = conn.describe_instances()
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            if instance_id in instance["InstanceId"]:
                return instance
    return None


def wait_for_instance(conn, instance_id, log):
    instance = get_instance(conn, instance_id)
    if instance is None:
        logger(log, f"Instance {instance_id} not found")
        return False
    if instance["State"]["Name"] == "stopped":
        conn.start_instances(InstanceIds=[instance_id])
    loop = 0
    while instance["State"]["Name"] != "running":
        time.sleep(10)
        loop += 1
        if loop > 10:
            logger(
                log,
                f"Waited and Instance {instance_id} won't "
                f"start: {instance['State']['Name']}",
            )
            return False
        instance = get_instance(conn, instance_id)
        if instance is None:
            logger(log, f"Instance {instance_id} not found")
            return False
    # even though status is running, machine isn't always accessible
    # immediately
    time.sleep(60)
    return True


def main(config):
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

    logger(log, f"Checking to see if {instance_id} is running")

    public_dns_name = ""
    ip_address = ""
    instance_running = False
    instance = get_instance(conn, instance_id)
    if instance is None:
        logger(log, f"Instance {instance_id} not found")
        return
    if instance["State"]["Name"] == "running":
        public_dns_name = instance["PublicDnsName"]
        ip_address = instance["PublicIpAddress"]
        instance_running = True
        logger(
            log,
            f"Instance {instance_id} is running\n{public_dns_name} {ip_address}",
        )
    elif instance["State"]["Name"] == "stopped":
        logger(log, f"Starting Instance {instance_id}")
        instance_running = wait_for_instance(conn, instance_id, log)
        if instance_running:
            logger(log, f"Spawned and Started Instance {instance_id}")
            instance = get_instance(conn, instance_id)
            public_dns_name = instance["PublicDnsName"]
            ip_address = instance["PublicIpAddress"]
    else:
        logger(log, f"Waiting for Instance {instance_id}")
        instance_running = wait_for_instance(conn, instance_id, log)
        if instance_running:
            logger(log, f"Spawned and Started Instance {instance_id}")
            public_dns_name = instance["PublicDnsName"]
            ip_address = instance["PublicIpAddress"]
        else:
            logger(log, f"Couldn't Start Instance {instance_id}")
            return
        logger(log, f"Waited and Started Instance {instance_id}")

    if instance_running:
        rsync_command = [
            config.get("backups", "rsync_path"),
            "-e", "ssh -o StrictHostKeyChecking=no",
            "-aplxo",
            "--delete",
            config.get("backups", "backup_source"),
            f"{config.get('backups', 'remote_username')}@{public_dns_name}:{config.get('backups', 'backup_dest')}",
        ]

        logger(log, f"Running rsync: {' '.join(rsync_command)}")
        subprocess.run(rsync_command)

    logger(log, f"Stopping Instance {instance_id}")
    conn.stop_instances(InstanceIds=[instance_id])

    if email_address:
        email_report(config, email_address, log, time_start)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "backup.cfg")
    with open(config_path) as f:
        config.read_file(f)

    try:
        main(config)
    except KeyboardInterrupt:
        sys.exit()
