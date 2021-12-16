#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from .Tools import *
from .debug import Debug
from .debug import BColors
from pylab import *
import json

TAG = "GenerateFilePymol.py: "
color = BColors.GREEN


class GenerateFilePymol(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.pml_path = self.cfg.OUTPUT_GRAPHS['pml']['outPut'] + ".pml"  # output file pml
        self.debug = Debug(cfg.mode_debug)
        self.create_pml_pymol()

    #
    #    Create a pml file with the protein data and the best ligands for pymol
    #
    def create_pml_pymol(self):
        funit = open(self.pml_path, 'wt')
        self.add_target_pml(funit)

        if self.cfg.opcion.startswith("BD") and self.cfg.best_poses is not None:
            for num_site in range(len(self.cfg.best_poses)):
                self.add_ligand_pml(funit, self.cfg.best_poses[num_site], num_site + 1)
            funit.write("cmd.hide('cgo')\n")

        elif self.cfg.opcion.startswith("VS"):

            if self.cfg.pymol_show_docking_box:
                size_grid_x = int(self.cfg.best_poses[0].size_grid.split(",")[0])
                cube = self.get_cube_pymol(self.cfg.best_poses[0].coords[0], self.cfg.best_poses[0].coords[1],
                                           self.cfg.best_poses[0].coords[2], size_grid_x)
                funit.write("Gr{1} = {0}\ncmd.load_cgo(Gr{1}, 'Gr{1}')\ncmd.hide('Gr{1}')\n".format(cube, 0))
            for lig in self.cfg.best_poses:
                self.add_ligand_pml(funit, lig, 0)
            funit.write("cmd.hide('cgo')\n")

        funit.write(
            "cmd.zoom()\n"
            "cmd.save('{}.pse')\n"
                .format(self.cfg.name_input)
        )

        funit.close()

    def add_target_pml(self, funit):
        if "results" in self.cfg.OUTPUT_DIRS['bestScore']:  # si se hace VS
            d_target = "."
        else:
            d_target = os.path.split(self.cfg.OUTPUT_DIRS['bestScore'][:-1])[1]
        if self.cfg.plip:
            self.cfg.ext_target = ".pdb"
        str_targets = ""
        if self.cfg.profile == "STANDARD_VSR":

            for lig in self.cfg.best_poses:
                str_targets += " {}".format(lig.file_ori_target)
        else:
            str_targets = '{}/{}{}'.format(d_target, self.cfg.name_target, self.cfg.ext_target)

        cmd = '{} {} -t {}'.format(self.cfg.python_exe, self.cfg.generate_headr_pml_pml, str_targets)
        funit.write(self.cfg.execute("Generate header session: ", cmd))

    def add_ligand_pml(self, funit, lig, num_site):
        cube = 1
        if "results" in self.cfg.OUTPUT_DIRS['bestScore']:  # si se hace VS
            n_lig = lig.file_name
            if num_site != 1:
                cube = 0
        else:
            n_lig = os.path.split(self.cfg.OUTPUT_DIRS['bestScore'][:-1])[1] + "/" + lig.file_name
        json_interactions = os.path.join(self.cfg.OUTPUT_DIRS['interacciones'],
                                         lig.file_name + "_interactions") + ".json"
        cmd = '{0} {1} {2} {3} {4} {5} {6} {7}'.format(
            self.cfg.python_exe,
            self.cfg.ligand_pml,
            "./" + n_lig + lig.ligand_ext,
            lig.file_json,
            json_interactions,
            num_site,
            cube,
            self.cfg.profile
        )
        out = self.cfg.execute("Generate File Pymol: ", cmd)
        funit.write(out)

    def generate_pymol_session(self):
        import pymol
        stdout = sys.stdout
        stderr = sys.stderr

        pymol.pymol_argv = ['pymol', '-c', '-q', '-k', '-Q ']  # -Q

        pymol.finish_launching()
        current_path = os.getcwd()
        if self.cfg.opcion.startswith("VS"):
            os.chdir(self.cfg.file_input + '/results/best_scores')
        else:
            os.chdir(self.cfg.file_input)
        pymol.cmd.load('{}.pml'.format(self.cfg.OUTPUT_GRAPHS['pml']['outPut']))
        pymol.cmd.delete('all')
        os.chdir(current_path)
        pymol.cmd.quit()
        sys.stdout = stdout
        sys.stderr = stderr

    def get_cube_pymol(self, x, y, z, size_grid_x):
        """
            Generate a cube for pymol with the center where the ligand started docking
        """
        PYTHON_RUN = "python"
        if size_grid_x > 0:
            cmd = "{} {} {}::{}::{} {} ".format(
                PYTHON_RUN,
                self.cfg.generate_cube_pymol,
                float(x),
                float(y),
                float(z),
                float(size_grid_x))
            return subprocess.check_output(cmd, shell=True).decode("utf-8")
        return ""