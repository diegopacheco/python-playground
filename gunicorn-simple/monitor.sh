#!/bin/bash

function stats() {
    waiting=$(sudo ss -n | grep 8000 | wc -l)
    tcp_abort_on_overflow=$(cat /proc/sys/net/ipv4/tcp_abort_on_overflow)
    tcp_synack_retries=$(cat /proc/sys/net/ipv4/tcp_synack_retries)
    tcp_maxsyn_backlog=$(cat /proc/sys/net/ipv4/tcp_max_syn_backlog)
    timewaiting=$(netstat -n | grep 8000 | grep TIME_WAIT | wc -l)
    recvq=$(sudo ss -lt -n | grep 8000 | awk '{print $2}')

    echo "TCP.ABORT.ON.OVERFLOW : $tcp_abort_on_overflow"
    echo "TCP.SYNACK.RETRIES    : $tcp_synack_retries"
    echo "TCP.MAXSYN.BACKLOG    : $tcp_maxsyn_backlog"
    echo "WAITING               : $waiting"
    echo "TIME_WAITING          : $timewaiting"
    echo "RECV-Q                : $recvq"
}

export -f stats
watch -n1 -x bash -c stats
