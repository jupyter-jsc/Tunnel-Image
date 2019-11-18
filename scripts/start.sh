#!/bin/bash

service ssh restart
sed -i -e "s/log_hostname/$HOSTNAME/g" /etc/j4j/J4J_Tunnel/uwsgi.ini
if [ -f "/etc/j4j/J4J_Tunnel/watch_logs.pid" ];then
    kill -9 `cat /etc/j4j/J4J_Tunnel/watch_logs.pid`
    rm /etc/j4j/J4J_Tunnel/watch_logs.pid
fi
su -c "/etc/j4j/J4J_Tunnel/watch_logs.sh &" tunnel
su -c "echo $! > /etc/j4j/J4J_Tunnel/watch_logs.pid" tunnel
su -c "uwsgi --ini /etc/j4j/J4J_Tunnel/uwsgi.ini" tunnel
