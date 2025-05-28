#! /bin/bash
#: ${EXE:=eval}
# ring management API
: ${bdev:=bat0}

a0=${0##*/}
_usage()
{
echo "Usage: [bdev=<bat_dev>] $a0 addif|delif <netdev> ..." >&2
#echo "       [bdev=<bat_dev>] $a0 ifup|ifdown <netdev> ..." >&2
echo "       [bdev=<bat_dev>] $a0 net|show|neighbor|if|nodes" >&2
echo "       [bdev=<bat_dev>] $a0 mac|fdb [-a]" >&2
echo "       [bdev=<bat_dev>] $a0 arp|dat_cache|dc" >&2
# debug
echo " ***   utilities + debug" >&2
echo "       [bdev=<bat_dev>] $a0 tr|p ... <orig_mac>|all " >&2
echo "       [bdev=<bat_dev>] $a0 tp ... <nexthop_mac>|wt?|0|1 " >&2
echo "       [bdev=<bat_dev>] $a0 hops|next [wt?|0|1] # show mac of ifs" >&2
echo "       [bdev=<bat_dev>] $a0 path <wt?>" >&2
echo "       [bdev=<bat_dev>] $a0 debug|dbg ..." >&2
# setup
echo " ***   internal - reserved" >&2
echo "Usage: [bdev=<bat_dev>] $a0 create [<mtu>]" >&2
echo "       [bdev=<bat_dev>] $a0 destroy <bat_dev>" >&2
[[ $# > 0 ]] || return $1
}
kdbg=/sys/kernel/debug/batman_adv
dbgfs=${kdbg}/${bdev}

ifcmd=
bat="batctl meshif ${bdev}"

_main()
{
 case "$1" in
 addif*) shift
  _add_del_ifs add $*
 ;;
 delif*) shift
  _add_del_ifs del $*
 ;;
# ifup)
#  ifcmd=${1} ; shift
#  _add_del_ifs add "$@"
# ;;
# ifdown)
#  ifcmd=${1} ; shift
#  _add_del_ifs del "$@"
# ;;
 fdb|mac) shift
  _ring_fdb $*
 ;;
 dc|dat_*|arp) shift
  _ring_dat $*
 ;;
 if) shift # list interface
 _ring_if
 ;;
 n|nei*)  # neighbors
 _ring_neigh
 ;;
 node*)
 _ring_nodes | cut -d' ' -f1
 ;;
 hop*)
# _ring_nodes "$@"
 __ring_hops "$@"
 ;;
 next) shift
 _ring_next_hop "$@"
 ;;
 ""|net|show)
 _ring_net | _skip_sort 3
 ;;
 stats) shift
 _ring_stats
 ;;
 create) shift
 _ring_create "$@"
 ;;
 destroy) shift
 _ring_destroy "$@"
 ;;
 path)  shift ;
 _path "$@"
 ;;
 tr*) shift #L2 traceroute
 (( $# > 0 )) || { _usage ; return 1 ; }
 if [[ $1 == all ]] ; then
 _orig | tee | _tr2
 else
 _btr "$@"
 fi
 ;;
 #p|ping)    #L2 ping
 #(( $# > 1 )) || { _usage ; return 1 ; }
 #${bat} "$@"
 #;;
 tp|p|ping)
 (( $# > 1 )) || { _usage ; return 1 ; }
 _tp_p "$@"
 ;;
 debug|dbg*) shift
  echo kdbg=${kdbg}
 _ring_dbg "$@"
 ;;
 *|-h|--help|help)
  _usage ; return 1
 ;;
 esac

 return $?
}
###############################################
_del_port()
{
bdev=$1 ; i=$2 ; shift 2
 ${EXE} ${bat} if -M del ${i}
 [[ "${ifcmd}" == "" ]]  || { ${EXE} ${ifcmd} ${i} ; return $? ;
 }
# handle link up/down outside of this
# ${EXE} ip link set dev ${i} down
}

_batif_customize()
{
# dev ::= {ring0,wt0,wt1}
dev=$1 ; shift
#
_ring_set=/etc/init.d/bsp/ring_if_settings
[[ -x ${_ring_set} ]] || return
# pass mtu to ring_set
eval ${_ring_set} ${dev} "$@"
}

_add_port()
{
bdev=$1 ; i=$2 ; shift 2
# ${EXE} ip -4 addr flush dev ${i}
# ${EXE} ip link set dev ${i} down
 ${EXE} ${bat} if add ${i}
 [[ "${ifcmd}" == "" ]]  || { ${EXE} ${ifcmd} ${i} ; return $?;
}
 ${EXE} _batif_customize ${i}       # customize hardif
# handle link up/down outside of this
# ${EXE} ip link set dev ${i} up
# set ${bdev} up in case it was down
 ${EXE} ip link set dev ${bdev} up
 ${EXE} if.vlan ${bdev} default
}

_add_del_ifs()
{
# add one or more ports to bat_dev
# only add port if it is not already on the bat_dev
 cmd=$1 ; shift
 if [ $# -lt 1 ] ; then
  _usage
  return 1
 fi
 for i in $* ; do
  # todo: check to see if port is already attached to bat_dev
  eval _${cmd}_port ${bdev} ${i}
 done
}

###############################################
_ring_if()
{
${EXE} ${bat} if
}

_ring_net()
{
${EXE} ${bat} o | _skip_sort 3
}

_ring_neigh()
{
${EXE} ${bat} n
}

_ring_stats()
{
 ${EXE} ${bat} s
 return $?
}

_ring_fdb()
{
${EXE} ${bat} tg
[[ "$1" == "-a" ]] && ${EXE} ${bat} tl
#cat ${dbgfs}/transtable_*
}

_ring_dat()
{   # dc|dat_cache
${EXE} ${bat} dc
}


_ring_create()
{
# need to set protocol before creating ring0
batctl ra BATMAN_V
# create batman interface ring0
${bat} if create
# customize if settings
_batif_customize ${bdev} "$@"
}

_ring_destroy()
{
[[ ${bdev} == "$1" ]] || { _usage ; return 1 ; }
${bat} if destroy
}

###############################################
# utilities
_orig()
{
${bat} o | tail +3
# | cut -c3-
}

_btr()
{
timeout 10 ${bat} tr -n $1
}
_tr2()
{
while read a m l2 ; do
[[ $a == "*" ]] || continue
_btr  $m
done
}

# sort after the nth column
_skip_sort() {
 skip=
 (( $# == 0 )) || { skip="skip=$1" ; shift ; }
 awk 'NR<3 { print $0 ; next ; } { print $0 | "sort -k6,7" }' ${
skip}
}

# hack version to hide own node as originator
_path()
{
if (( $# > 0 ))  ; then
_ring_net |
    awk '
        NR == 1 { split($5, m, "/") ; mac = m[2] ; }
        NR > 2 {
            if ( $2 == mac ) { next ; }
            print $2, $7, $6;
        }' | grep ${1}  |
    awk '{print $1, $2 ; }'
else
_ring_net |
         awk '
        NR == 1 { split($5, m, "/") ; mac = m[2] ; }
        NR > 2 {
            if ( $2 == mac ) { next ; }
            print $1, $2, $3, $5, $6, $7;
        }'
fi
}

_path_0()
{
if (( $# > 0 ))  ; then
_ring_net | sed '1,2d;s/^..//'|  grep ${1}  |
         awk '{print $1, $6 ; }'
#        awk '{print $1, $7 ; }' | tr -d ')'
else
#_ring_net | sed -e '/^ \*/!d;s/]//g;s/\[//g;s/[()]//g' |
_ring_net |
    awk 'NR > 2 {print $1, $2, $3, $5, $6, $7; }'
fi
}

__ring_hops()
{
_ring_net |
    awk '$1 == "*" { printf "%s %s %s\n", $2, $6, $7; }'
}

_ring_nodes()
{   # mask out last 4 bit of mac
__ring_hops |
    awk '{ n=$1 ; printf "%s0 %s %s\n", substr(n, 1, length(n)-1
), $2, $3; }'
}
 return the next hop neighbor and interface
_ring_next_hop()
{
#_ring_neigh |  awk '\
#    function cut_n(a) { return substr(a, 1, length(a)-1) ; }
#    NR > 2 { printf "%s %s\n", $1,  cut_n($NF) ; } '
# no args ==> wt=""
__ring_hops |  awk ' $3 == 1 \
    { if ( wt == "" ||  wt == $2 ) { printf "%s %s\n", $1, $2; }
 }' wt=$1
}

###############################################
# link throughput or ping
_tp_p()
{
cmd="$1" ; shift
(( $# > 0 )) || return 1
case "$1" in
wt?)  dstif=$1 ; shift ;;
0|1) dstif=wt${1} ; shift ;;
*) dmac="$1" ; shift ;;
esac

if [ "$dstif" != "" ] ; then
read dmac dif <<< $(_ring_next_hop ${dstif}) || return 2
fi
[[ "$dmac" != "" ]] || return 3

echo "+ ${cmd}: ${dmac} ${dif}"
${bat} ${cmd} ${dmac} "$@"
return $?
}
###############################################
_ring_dbg()
{
case "$1" in
"") ls ${dbgfs} ;;
vlan) shift ; cat ${dbgfs}/bla_vlan_list ;;
bbt) shift ; cat ${dbgfs}/bla_backbone_table ;;
log) shift ; cat ${dbgfs}/log ;;
cl|dc|gwl|mf|n|nn|o|tg|tl) ${bat} $1 ;;
ptype) shift ;
 if (( $# > 0 )) ; then
  d=$1 ; shift ;
 else
  d="wt?"
 fi
 eval  cat ${kdbg}/${d}/ptype
;;
#cl) shift ; cat ${dbgfs}/bla_claim_table ;;
*) cat ${dbgfs}/$1 ;;
esac
}
# bla_backbone_table
# bla_vlan_list
# bla_claim_table
# dat_cache
# gateways
# log
# mcast_flags
# neighbors
# originators
# transtable_global
# transtable_local
# socket

###############################################
_main $*
