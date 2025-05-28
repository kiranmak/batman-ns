#!/bin/python3
ns_db = ["B1", "B2", "B3", "B4", "B5", "B6"]

batctl -m bat0 loglevel routes tt

def set_bat_loop_avoidance(ns, flag):
    cmd = "batctl bat0 bl"
    set_flag = 1 if flag else 0
    exec_subprocess(f"ip netns exec {ns}  {cmd} {set_flag}")

def set_bat_log_level(ns, flag):
    cmd = "batctl bat0 ll"
    exec_subprocess(f"ip netns exec {ns}  {cmd} {flag}")



