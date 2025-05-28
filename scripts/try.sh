#!/bin/bash
strings=("B1" "B2" "B3" "B4")
for ns in "${strings[@]}"; do
    echo "[$ns]: link add bat0"
    sudo ip netns exec $ns ip link add name bat0 type batadv
    echo "[$ns]:batctl add wt0 and wt1 to bat0"
    sudo ip netns exec $ns batctl if add wt0
    sudo ip netns exec $ns batctl if add wt1
    sleep 2
done

for ns in "${strings[@]}"; do
    echo "[$ns]:ip link add sge0 to $ns"
    sudo ip netns exec $ns ip link set sge0 master $ns
    sleep 2
    echo "adding bat0 if "
    echo "[$ns]:ip link add bat0 to $ns"
    sudo ip netns exec $ns ip link set bat0 master $ns

    sleep 2
    echo "[$ns]:turn on loop avoidance batctl in $ns"
    batctl bl 1
    echo "[$ns]:bridge $ns up"
    sudo ip netns exec $ns ip link set up dev $ns
    sleep 2
done

