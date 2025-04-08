#!/usr/bin/env bash

cd /app

if [ -e /dev/nsm ] ; then
    echo In Enclave

    ip addr add 127.0.0.1/32 dev lo
    ip link set dev lo up

    host_to_vsock --port 11434 --vsock-addr 3 --vsock-port 11434 &
    host_to_vsock --port 443 --vsock-addr 3 --vsock-port 443 &

    echo "127.0.0.1	api.openai.com" >> /etc/hosts
    echo "127.0.0.1	api.anthropic.com" >> /etc/hosts
    echo "127.0.0.1	api.together.xyz" >> /etc/hosts
    cat /etc/hosts

    FLAGS="--vsock"

elif [ "$DOCKER" == 1 ] ; then
    echo In Docker

    host_ip=`/sbin/ip route|awk '/default/ { print $3 }'`
    echo "${host_ip}	api.openai.com" >> /etc/hosts
    echo "${host_ip}	api.anthropic.com" >> /etc/hosts
    echo "${host_ip}	api.together.xyz" >> /etc/hosts
    cat /etc/hosts

    echo Forwarding ...
    host_to_remote --dest-addr ${host_ip} &

fi

echo APP STARTING ...
enclave $FLAGS
