#!/bin/bash

function stats() {
    waiting=$(sudo ss -n | grep 8000 | wc -l)
    tcp_synack_retries=$(cat /proc/sys/net/ipv4/tcp_synack_retries)
    tcp_maxsyn_backlog=$(cat /proc/sys/net/ipv4/tcp_max_syn_backlog)

    echo "TCP.SYNACK.RETRIES : $tcp_synack_retries"
    echo "TCP.MAXSYN.BACKLOG : $tcp_maxsyn_backlog"
    echo "WAITING            : $waiting"
}

export -f stats
watch -n1 -x bash -c stats
