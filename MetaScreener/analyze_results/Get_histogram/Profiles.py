#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
PROFILES = {
        'RAW':
        {
        },
        'STANDARD_BD':
        {
            'opcion': 'BD',
            'distanceGraph': True,
            'clustered': True,

            'finger_print':            True,
            'heat_map_interactions':   True,
            'interactions_global':     True,
            'interactions_atoms':      True,
            'poseview':                True,
            'plip':                    True,
            'createFolders':           True,
            'compress':                True,
            'join_images':             True,
            'copy_summary':            True,
            'img_svg':                 True,
            'distanceGraph':           True,
            'clustered':               True,
            'resultados_ficheros':     0,
            'resultados_best_score':   0,
            'resume':                  True,
            'pymol_show_docking_box':  True


        },
        'STANDARD_VS':
        {
            'opcion': 'VS',
            'clustered': True,
            'finger_print':            True,
            'heat_map_interactions':   True,
            'interactions_global':     True,
            'interactions_atoms':      True,
            'poseview':                True,
            'plip':                    True,
            'createFolders':           True,
            'compress':                True,
            'join_images':             True,
            'copy_summary':            True,
            'img_svg':                 True,
            'distanceGraph':           False,
            'clustered':               False,
            'resultados_ficheros':     500,
            'resultados_best_score':   50,
            'resume':                  True,
            'pymol_show_docking_box':  True
        },
        'TESTING':
        {
            'opcion': 'BD',
            'programa': 'AD',
            'distanceGraph': False,
            'resume': True,
            'pymol_show_docking_box': 'n',
            'clustered': True,
            'plip': False

        },
        'STANDARD_VS_LS':
        {
            'opcion':                  'VS',
            'createFolders':           True,
            'compress':                True,
            'interactions_global':     False,
            'interactions_atoms':      False,
            'clustered':               False,
            'finger_print':            False,
            'heat_map_interactions':   False,
            'poseview':                False,
            'plip':                    False,
            'join_images':             True,
            'copy_summary':            False,
            'img_svg':                 False,
            'distanceGraph':           False,
            'resultados_ficheros':     500,
            'resultados_best_score':   0,
            'resume':                  True,
            'pymol_show_docking_box':  False
        },
        'UNCLUSTERED_BD':
        {
            # Experimental profile
            'opcion':                  'BD',
            'interactions_global':     True,
            'interactions_atoms':      True,
            'createFolders':           True,
            'compress':                True,

            'clustered':               False,
            'finger_print':            False,
            'heat_map_interactions':   False,
            'poseview':                False,
            'plip':                    False,
            'join_images':             False,
            'copy_summary':            False,
            'img_svg':                 False,
            'distanceGraph':           False,
            'resultados_ficheros':     500,
            'resultados_best_score':   0,
            'resume':                  True,
            'pymol_show_docking_box':  False
        }
    }


class Profiles(object):

    def __init__(self, cfg):
        self.cfg = cfg

    def print_opt(self, opt, choice):
        if choice == 1 and opt != "Cores":
            choice = "True"
        elif choice == 0:
            choice = "False"
        self.cfg.print_format(" ", opt, choice)

    def print_perfil_conf(self, profile):
        print("")
        print("Profile settings: " + profile)
        self.print_opt('Cores', self.cfg.cores)
        self.print_opt('Dpi', self.cfg.dpi)
        self.print_opt('Debug', self.cfg.mode_debug)
        self.print_opt('Create_folders', self.cfg.createFolders)
        self.print_opt('Interactions_global', self.cfg.interactions_global)
        self.print_opt('interactions_atoms', self.cfg.interactions_atoms)
        self.print_opt('Poseview', self.cfg.poseview)
        self.print_opt('Plip', self.cfg.plip)
        self.print_opt('Compress', self.cfg.compress)
        self.print_opt('Join_images', self.cfg.join_images)
        self.print_opt('Compy_sumary', self.cfg.copy_summary)
        self.print_opt('Img_svg', self.cfg.img_svg)
        self.print_opt('DistanceGraph', self.cfg.distanceGraph)
        self.print_opt('Clustered', self.cfg.clustered)
        self.print_opt('File_res', self.cfg.resultados_ficheros)
        self.print_opt('Best_score', self.cfg.resultados_best_score)
        self.print_opt('Resume', self.cfg.resume)
        self.print_opt('Prmol_show_docking_box', self.cfg.pymol_show_docking_box)
        print("")

    def set_profile_cfg(self, profile):

        format_paramp = '{0:>5}{1:<25} {2:<20}'
        if profile in PROFILES:
            self.cfg.setattr('profile',profile)
            a = PROFILES[profile]
            for k, v in a.items():
                self.cfg.setattr(k, v)
            self.print_perfil_conf(profile)
        else:
            print("ERROR: Wrong profile. The available profiles are : ")
            for profile, v in PROFILES.items():
                print ("Profile: ", profile)
                p = PROFILES[profile]
                for k, v in p.items():
                    if v == 'y':
                        print(format_paramp.format("", k.title(), "True"))
                    elif v == 'n':
                        print(format_paramp.format("", k.title(), "False"))
                    else:
                        print(format_paramp.format("", k.title(), v))
                print("")
            exit()

    @staticmethod
    def get_folders():
        return{
            'folderErrorJob':      'jobs_out',
            'folderOutJob':        'jobs_out',
            'folderTemplatesJobs': 'jobs',
            'folderJobsDone':      'jobs_done',
            'folderGrid':          'grids',
            'folderOutUcm':        'soft_out',
            'folderMolec':         'molecules',
            'folderEnergy':        'energies'
            }

    def get_out_folders(self):
        # Se crea un apartado especial para VS
        if self.cfg.opcion.startswith("VS"):
            wkd = self.cfg.file_input+'/results/'
            output_dirs = {
                'workdir':             wkd,
                'bestScore':           os.path.join(wkd, 'best_scores/'),
                'nextBestScore':       os.path.join(wkd, ''),
                'interacciones':       os.path.join(wkd, 'best_scores/'),
                'afinidades':          os.path.join(wkd, 'best_scores/'),
                }
        elif self.cfg.profile == "UNCLUSTERED_BD":
            output_dirs = {
                'workdir':           self.cfg.file_input,
                'bestScore':           'poses/',
                'nextBestScore':       'poses/',
                'interacciones':       'poses/',
                'afinidades':          'affinities/',
                }
        else:
            output_dirs = {
                'workdir':           self.cfg.file_input,
                'bestScore':           'clustered_poses/',
                'nextBestScore':       'clustered_poses/',
                'interacciones':       'clustered_interactions/',
                'afinidades':          'clustered_affinities/',
                }
        return output_dirs

    def get_files_out(self):
        if self.cfg.opcion.startswith("VS"):
            graph_names = {
                'histogram':
                {
                    'title': "VS Docking results ({} on {}):\n".format(self.cfg.name_query, self.cfg.name_target),
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['bestScore'], self.cfg.name_input + "_Histogram")
                },
                'pml':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['bestScore'], self.cfg.name_input + "")
                },
                'clusters':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['bestScore'], self.cfg.name_input + "_clusters.txt")
                },
                'grap10':
                {
                    'title': self.cfg.OUTPUT_DIRS['bestScore'],
                    'outPut': self.cfg.OUTPUT_DIRS['bestScore']
                }
            }
        elif self.cfg.profile == "UNCLUSTERED_BD":
            graph_names={
                'histogram':
                {
                    'title': "Unclustered Docking results ({} on {}):\n Binding Energy Frequency".format( self.cfg.name_query, self.cfg.name_target),
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'], self.cfg.name_input + "_Binding_energy")
                },
                'pml':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'],self.cfg.name_input + "_poses")
                },
                'grap10':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'], self.cfg.name_input+ "_Poses_Join")
                }
            }
        else:
            graph_names={
                'histogram':
                {
                    'title': "Unclustered Docking results ({} on {}):\n Binding Energy Frequency".format( self.cfg.name_query, self.cfg.name_target),
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'], self.cfg.name_input + "_unclustered")
                },
                'pml':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'],self.cfg.name_input + "_clusters")
                },
                'clusters':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'],self.cfg.name_input+ "_clusters")
                },
                'grap10':
                {
                    'title': "",
                    'outPut': os.path.join(self.cfg.OUTPUT_DIRS['workdir'], self.cfg.name_input+ "_Poses_Join")
                }
            }

        self.cfg.cpy_file_target = os.path.join(self.cfg.file_input, self.cfg.OUTPUT_DIRS['bestScore'],
                                                self.cfg.name_target + self.cfg.ext_target)
        return graph_names
