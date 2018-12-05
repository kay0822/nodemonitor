#!/bin/bash

if [ $# != 2 ];then
    echo "Usage $0 host_id node_id"
    exit 1
fi

host_id=$1
node_id=$2

ssh z$host_id "systemctl restart secnode$node_id"

