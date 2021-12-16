# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   Author: Jorge de la Peña García
   Email:  jorge.dlpg@gmail.com
   Description: Adds the protein to the pml, the indicated queries and returns the default parameters that are used
                in the pymol sessions.
"""
import argparse
import sys
from os.path import splitext, basename

DEFAULT_SESSION_HEAD = '#\n# Default Head Params \n#\n' \
                     + 'cmd.select("tal", "Site*")\n' \
                     + 'cmd.spectrum("b","rainbow_rev", "tal")\n' \
                     + 'from pymol.cgo import *\n' \
                     + 'cmd.set("valence")\n' \
                     + 'cmd.bg_color("grey30")\n' \
                     + 'cmd.set("label_size", 15)\n'


DEFAULT_SESSION_TAIL = '#\n# Default Tail Params \n#\n' \
                     + 'cmd.clip("far", 1000)\n' \
                     + 'cmd.clip("near", 1000)\n' \
                     + 'cmd.zoom("all")\n'

DEFAULT_SESSION_TARGET = '#\n# Target {0} \n#\n' \
                       + 'cmd.load("{1}","{2}")\n' \
                       + 'cmd.hide("(all and hydro and (elem C extend 1))")\n' \
                       + 'cmd.set("transparency", 0.7)\n' \
                       + 'cmd.hide("everything", "{2}")\n' \
                       + 'cmd.show_as("surface", "{2}")\n' \
                       + 'cmd.color("green", "{2}")\n'

DEFAULT_SESSION_QUERY = '#\n# Query {0} \n#\n' \
                      + 'cmd.load("{1}","{2}")\n' \
                      + 'cmd.show("lines", "{2}") \n'


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Adds the protein to the pml, the indicated queries and returns the'
                                                 ' default parameters that are used in the pymol sessions', epilog="")
    parser.add_argument('-t', '--targets', action='append', nargs='+',
                        help='extra file queries',
                        required=False, type=str) # are str because they may not exist on the same path from where you are told

    parser.add_argument('-q', '--queries', action='append', nargs='+',
                        help='extra file queries',
                        required=False, type=str)

    parser.add_argument('-head',   help='Add head', default=True, type=str2bool)
    parser.add_argument('-tail', help='Add tail', default=True, type=str2bool)

    if len(sys.argv) == 1:
        parser.print_help()
        print ('')
        sys.exit(1)
    args = parser.parse_args()
    txt_show = ""
    if args.head:
        txt_show += DEFAULT_SESSION_HEAD
    if args.targets:
        cnt = 1
        for target in args.targets[0]:
            name_receptor = splitext(basename(target))[0]
            txt_show += DEFAULT_SESSION_TARGET.format(cnt, target, name_receptor)
            cnt += 1
    if args.queries:
        cnt = 1
        for query in args.queries[0]:
            name_q = splitext(basename(query))[0]
            txt_show += DEFAULT_SESSION_QUERY.format(cnt, query, name_q)
    if args.tail:
        txt_show += DEFAULT_SESSION_TAIL
    print (txt_show)
