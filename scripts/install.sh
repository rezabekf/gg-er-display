#!/usr/bin/env bash
# Setup
sudo adduser --system ggc_user
sudo groupadd --system ggc_group

# Install pre-reqs
sudo apt-get update
sudo apt-get install -y vim git sqlite3 python2.7 binutils curl

# Improve security on the Pi device
vim /etc/sysctl.d/98-rpi.conf

# add the following two lines to the end of the file
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
sudo reboot

# Edit your command line boot file to enable and mount memory cgroups.
vim /boot/cmdline.txt

# Append the following to the end of the existing line, not as a new line.
cgroup_enable=memory cgroup_memory=1
sudo reboot

# Copy greengrass binaries
wget ~/downloads/ https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.8.1/greengrass-linux-armv7l-1.8.1.tar.gz

# Decompress the AWS IoT Greengrass core software
sudo tar -xzvf ~/downloads/greengrass-linux-armv7l-1.8.1.tar.gz -C /

# Download the appropriate ATS root CA certificate
sudo wget -O ~/downloads/root.ca.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem

# If the deployment is stuck then you may have to use legacy certificate
sudo wget -O ~/downloads/root.ca.pem https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Copy certificates and configurations to pi
rsync certs/* pi@RASPBERRY_PI_ADDR:/tmp/certs/
rsync config/* pi@RASPBERRY_PI_ADDR:/tmp/config/

# On raspberry pi
sudo cp ~/downloads/root.ca.pem /greengrass/certs/
sudo rsync --remove-source-files --chown=root:root /tmp/certs/* /greengrass/certs/
sudo rsync --remove-source-files --chown=root:root /tmp/config/* /greengrass/config/

# Start Greengrass Core
sudo /greengrass/ggc/core/greengrassd start

# Back up group.json - you'll thank me later
sudo cp /greengrass/ggc/deployment/group/group.json /greengrass/ggc/deployment/group/group.json.orig

# Start Greengrass on system boot
vim gg-deamon.service

```
[Unit]
Description=Greengrass Daemon

[Service]
Type=forking
PIDFile=/var/run/greengrassd.pid
Restart=on-failure
ExecStart=/greengrass/ggc/core/greengrassd start
ExecReload=/greengrass/ggc/core/greengrassd restart
ExecStop=/greengrass/ggc/core/greengrassd stop

[Install]
WantedBy=multi-user.target
```
sudo cp gg-deamon.service /etc/systemd/system/gg-deamon.service
sudo systemctl enable gg-deamon.service