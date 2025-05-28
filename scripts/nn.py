#!/usr/bin/env python

import subprocess
import os
import sys

ns_db = ["B1", "B2", "B3", "B4", "B5", "B6"]

def run_netns_command(netns_name, command):
    cmd = ["ip", "netns", "exec", netns_name] + command
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout, result.stderr

def batctl_config():
    link_set = ["ip", "link", "set", "up"]
    for node in ns_db:
        o, e = run_netns_command(node, "ip link add name", "bat0 type batadv")
        o, e = run_netns_command(node, "batctl", "add", "if", "wt0")
        o, e = run_netns_command(node, "batctl", "add", "if", "wt1")

        bridge_name = node
        o, e = run_netns_command(node, link_set, "sge0 master", bridge_name)
        o, e = run_netns_command(node, link_set, "bat0 master", bridge_name)
        o, e = run_netns_command(node, "batctl bl 1")

    for node in ns_db:
        o, e = run_netns_command(node, link_set, "up dev" , bridge_name)


if __name__ == "__main__":
    print("Script name:", sys.argv[0])
    if len(sys.argv) > 1:
        netns_name = sys.argv[1]
        command = sys.argv[2:]
        if netns_name == 'all' or netns_name == 'a':
            for name in ns_db:
                print("---", name, "---")
                output = run_netns_command(name, command)
                for line in output:
                    print(line)
        elif netns_name == "batcfg" or "bc":
            if command == "batrun":
               batctl_config()

        else:
            print("Run command on ", netns_name)
            output, error = run_netns_command(netns_name, command)
            print(output)
            print(error)

    else:
        print("No arguments provided. call nn <ns-name> <command-to-run>")

