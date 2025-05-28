# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""IP link commands"""
import logging
from nest.engine.exec import exec_subprocess

logger = logging.getLogger(__name__)

"""
Batman has 3 things to buld upon:
    - a vertual meshif ??
    - a bat0 vertual if of type batadv
    - add lower leverl (physical/hard ifs)
"""
with_ns_cmd = "ip netns exec "
if_add_cmd = "ip link add name "
if_set_cmd = "ip link set dev "

def create_meshif(ns_name, s_name):
    exec_subprocess(
            f"{with_ns_cmd} {ns_name} ip link add name {s_name} type batadv"
    )


def batctl_add_interface(ns_name, ifname):
    exec_subprocess(
      f"ip netns exec {ns_name} batctl meshif {"bat0"} interface add {ifname}"
    )
    set_switch_mode("bat0", "up")
    exec_subprocess(f"ip netns exec {ns_name} ip -4 addr flush dev {dev_name}")
    exec_subprocess(f"ip netns exec {ns_name} ip -6 addr flush dev {dev_name}")


def configure_interface(nsname, ifname):
    # up interface
    mtu = 1532
    exec_subprocess(f"ip netns exec {ns_name} ip addr set dev {ifname} up {mtu}")

    # Configure mesh interface for layer 2 use.
    # probably not needed
    exec_subprocess(f'ip netns exec "{ns_name}" ip link set dev "{ifname}" arp off') 
    exec_subprocess(f'ip netns exec "{ns_name}" ip link set dev "{ifname}" multicast off') 
    #exec_subprocess(f'ip netns exec "{ns_name}" sysctl -q -w net.ipv6.conf.{ifname}.disable_ipv6=1')

def create_forwarder(ns_name, wt1, wt2, hosts):

    """
        --wt1--bat0--wt2--
          |     |     |
          +---(br0)---+
                |
                host
    """
    #ip link add name br0 type bridge
    create_switch(ns_name "br0")
    add_int_to_switch("br0", "bat0")
    add_int_to_switch("br0", "wt1")
    add_int_to_switch("br0", "wt2")
    for host in hosts:
        add_int_to_switch("br0", host)


def launch_batman(ns_name, wt1, wt2):
    # create bat0 type batadv
    create_meshif(ns_name, "bat0")
    batctl_add_interface(ns_name, wt1)
    batctl_add_interface(ns_name, wt2)

    configure_interface(nsname, wt1)
    configure_interface(nsname, wt2)
    #to do host config 


def destroy_batman(ns_name, wt1, wt2, hosts):
    exec_subprocess(
      "ip netns exec {nsname} batctl meshif {"bat0"} interface destroy 2> /dev/null"
    )

def delete_meshif(ns_name, s_name):
    delete_switch(ns_name, s_name)
