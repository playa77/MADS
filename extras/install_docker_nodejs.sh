#!/bin/bash

# this installs docker and nodejs on ubuntu 24.04 you need to relog after running this.
sudo apt update
sudo apt install git -y #technically not needed, but every system should have this, like nano etc.
sudo apt install nodejs npm -y # optional, not needed for installing docker only
sudo apt install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo usermod -aG docker ${USER} # must relog for this to work
# the following is currently neccessaqry on ubuntu 24.04
sudo systemctl daemon-reload
sudo systemctl restart docker.socket
sudo systemctl restart docker.service
sudo systemctl status docker # check if docker is up and running now
echo "you need to log out and re-login for this to work for your user"
