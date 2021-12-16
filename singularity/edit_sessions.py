#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
try:
    import pymol
except ImportError as e:
    print ("ERROR: pymol not found")
    print(e)
    exit()



def edit_sessions(file_pse):

    if os.path.isfile(file_pse):
        pymol.pymol_argv = ['pymol', '-c', '-q', '-k', '-Q']
        pymol.finish_launching()

        pymol.cmd.reinitialize()
        pymol.cmd.set('max_threads', CORES)

        pymol.cmd.load(file_pse)

        pymol.cmd.set('ray_trace_frames', 1)
        pymol.cmd.label("n. CA AND v.", 'resn+"-"+resi')
        pymol.cmd.set("label_position", (1.5, 1.5, 1.5))
        pymol.cmd.set("label_font_id", 10)
        pymol.cmd.set("label_size", 15)
        pymol.cmd.select("seleccion", "!v.")
        pymol.cmd.show("cartoon", "seleccion")
        pymol.cmd.delete("seleccion")

        pymol.cmd.set('transparency', 0.6)
        pymol.cmd.set('cartoon_transparency', 0.8)
        pymol.cmd.save(file_pse)
        pymol.cmd.delete('all')

parser = argparse.ArgumentParser()
parser.add_argument('session_pse', type=argparse.FileType('r'))
args = parser.parse_args()
edit_sessions(args.session_pse.name)