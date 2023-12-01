#!/bin/bash

function stats() {
    
    #
    # ss dump sockets statistics
    # 
    # This script list all connections(sockets) from all states that are on the port 8000
    # Counting the total number of connections(sockets).
    #
    connections=$(sudo ss -n | grep 8000 | wc -l)

    #
    # /proc/sys/net/ipv4/tcp_abort_on_overflow
    #
    # A boolean flag controlling the behaviour under lots of 
    # incoming connections. When enabled, this causes the kernel to 
    # actively send RST packets when a service is overloaded.
    #
    # IF this is 0(false) packet will be ignored. 
    #
    tcp_abort_on_overflow=$(cat /proc/sys/net/ipv4/tcp_abort_on_overflow)

    #
    # /proc/sys/net/ipv4/tcp_synack_retries
    #
    # Number of times SYNACKs for a passive TCP connection attempt
	# will be retransmitted. Should not be higher than 255. Default
	# value is 5, which corresponds to 31 seconds till the last
	# retransmission with the current initial RTO of 1second. With
	# this the final timeout for a passive TCP connection will
	# happen after 63 seconds.
    # 
    tcp_synack_retries=$(cat /proc/sys/net/ipv4/tcp_synack_retries)

    #
    # /proc/sys/net/ipv4/tcp_max_syn_backlog
    #
    # Maximal number of remembered connection requests, which have not
    # received an acknowledgment from connecting client.
    # The minimal value is 128 for low memory machines, and it will
    # increase in proportion to the memory of machine.
    # If server suffers from overload, try increasing this number.
    #
    tcp_maxsyn_backlog=$(cat /proc/sys/net/ipv4/tcp_max_syn_backlog)

    #
    # TIME_WAIT 
    # 
    # Indicates that local endpoint (this side) has closed the connection.
    # TIME_WAIT represents waiting for enough time to be sure that remote TCP 
    # received the ACK of its FIN request.
    #
    timewaiting=$(netstat -n | grep 8000 | grep TIME_WAIT | wc -l)

    #
    # RECV-Q
    #
    # High Recv-Q means the data is put on TCP/IP receive buffer, 
    # but the application does not call recv() to copy it from TCP/IP buffer 
    # to the application buffer. Customer can check the application 
    # listening the port, and see if it is working as expected. 
    #
    recvq=$(sudo ss -lt -n | grep 8000 | awk '{print $2}')

    #
    # SEND-Q
    #
    # High Send-Q means the data is put on TCP/IP send buffer, 
    # but it is not sent or it is sent but not ACKed. So, high value in 
    # Send-Q can be related to server network congest, server 
    # performance issue or data packet flow control, and so on. 
    #
    sendq=$(ss -plnt sport = :8000 | cat | awk '{print $3}' | sed -n 2p)

    #
    # TcpExtListenDrops
    #
    # What happens if the application can't keep up with calling accept() fast enough?
    #
    # This is when the magic happens! When the Accept Queue gets full 
    # (is of a size of backlog+1) then:
    # 
    # Inbound SYN packets to the SYN Queue are dropped.
    # Inbound ACK packets to the SYN Queue are dropped.
    # The TcpExtListenOverflows / LINUX_MIB_LISTENOVERFLOWS counter is incremented.
    # The TcpExtListenDrops / LINUX_MIB_LISTENDROPS counter is incremented.
    #
    tcpdrops=$(nstat -az TcpExtListenDrops | awk '{print $2}' | xargs)

    echo "TCP.ABORT.ON.OVERFLOW : $tcp_abort_on_overflow"
    echo "TCP.SYNACK.RETRIES    : $tcp_synack_retries"
    echo "TCP.MAXSYN.BACKLOG    : $tcp_maxsyn_backlog"
    echo "SOCKET CONNECTIONS    : $connections"
    echo "TIME_WAITING          : $timewaiting"
    echo "RECV-Q                : $recvq"
    echo "SEND-Q                : $sendq"
    echo "TCP_DROPS             : $tcpdrops"
}

export -f stats
watch -n1 -x bash -c stats
