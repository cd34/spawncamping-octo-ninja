spawncamping-octo-ninja
=======================

Backup machine to EC2/EBS

    virtualenv /usr/src/backup
    cd /usr/src/backup
    source bin/activate
    git clone git@github.com:cd34/spawncamping-octo-ninja.git tools
    cd tools
    python setup.py develop
    cp backup.cfg.sample backup.cfg
    edit backup.cfg and fill in appropriate values



You need to have an instance created (micro) with rsync and ssh allowed
with the key from your source machine.

Here's what the mail log reports after a successful run:

    2013-08-28T08:34:46.730101 - Connecting to AWS
    2013-08-28T08:34:47.174520 - Checking to see if i-xxxxxxxx is running
    2013-08-28T08:34:47.174584 - Instance i-xxxxxxxx is running
    ec2-1-2-3-4.us-west-2.compute.amazonaws.com 1.2.3.4
    2013-08-28T08:34:47.174657 - Running rsync: /usr/bin/rsync -e "ssh -o StrictHostKeyChecking=no" -aplxo --delete / root@ec2-1-2-3-4.us-west-2.compute.amazonaws.com:/backups/
    2013-08-28T10:41:38.507962 - Stopping Instance i-xxxxxxxx

    Elapsed time: 2 hours, 6 minutes and 53 seconds
