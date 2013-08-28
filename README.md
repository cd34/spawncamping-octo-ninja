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
    edit backup.cfg and fill in approproiate values



You need to have an instance created (micro) with rsync and ssh allowed
with the key from your source machine.
