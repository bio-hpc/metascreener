#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import bisect
from threading import Thread, Lock
from collections import OrderedDict
from .Tools import *
from .debug import Debug
from .debug import BColors
import json
if sys.version_info[0] == 3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty


TAG = "Clustered.py: "
color = BColors.GREEN


class Clustered(object):

    def __init__(self, cfg):
        if cfg.opcion.startswith("BD") and cfg.clustered:
            self.clt_path = cfg.OUTPUT_GRAPHS['clusters'][
                                'outPut'] + ".txt"
            self.clt_json_path = cfg.OUTPUT_GRAPHS['clusters'][
                                'outPut'] + ".json"

            self.cfg = cfg
            self.debug = Debug(cfg.mode_debug)
            self.queue = Queue()
            self.mutex = Lock()
            self.create_clustered()

    @staticmethod
    def add_to_cluster(q, mutex, pbar, poses):
        while True:
            try:
                task = q.get(timeout=0.3)
            except Empty:
                continue
            if task is None:
                q.task_done()
                break
            else:
                cluster, pose = task

                if cluster[0].check_overlap(pose):
                    mutex.acquire()
                    poses.remove(pose)
                    bisect.insort(task[0], pose)
                    mutex.release()
                q.task_done()

    @staticmethod
    def read_pose_file(q, mutex, pbar, poses):
        while True:
            try:
                lig_pose = q.get(timeout=0.3)
            except Empty:
                continue
            if lig_pose is None:
                q.task_done()
                break
            else:
                mutex.acquire()
                bisect.insort(poses, lig_pose)
                mutex.release()
                q.task_done()

    #
    #    Create a pml file with the protein data the best ligands for pymol
    #
    def create_clustered(self):

        pbar = custom_pbar()
        try:
            poses = []
            threads = []
            for i in range(self.cfg.cores):
                thread = Thread(target=self.read_pose_file, args=(self.queue, self.mutex, pbar, poses))
                thread.setDaemon(True)
                thread.start()
                threads.append(thread)
            print('  Leyendo poses...')
            pbar.start()
            for lig in self.cfg.best_poses:
                self.queue.put(lig)
            self.queue.join()
            pbar.finish()
            print(' ')
        except KeyboardInterrupt:
            sys.stderr.write('\n\n\nCtrl+C: interrumpiendo\n\n\n')
            self.queue.queue.clear()
            for i in range(self.cfg.cores):
                self.queue.put(None)
            sys.exit()
        else:
            for i in range(self.cfg.cores):
                self.queue.put(None)
            for th in threads:
                th.join()
        clusters = self.make_clustered(poses)
        self.cfg.best_poses = [cl[0] for cl in clusters.values()]

    def clusterizar_poses(self, poses):
        poses = list(poses)
        clusters = []
        pbar = custom_pbar()

        try:
            threads = []
            for i in range(self.cfg.cores):
                thread = Thread(target=self.add_to_cluster, args=(self.queue, self.mutex, pbar, poses))
                thread.setDaemon(True)
                thread.start()
                threads.append(thread)

            print('  Haciendo clusterizado...')
            pbar.start()

            while len(poses):
                # The poses are ordered by energy, so the first pose in the list is the best one
                # that does not yet belong to any cluster, so we use it as the center of a new one.
                new_cluster = [poses.pop(0)]
                for pose in list(poses):
                    self.queue.put((new_cluster, pose))
                self.queue.join()
                clusters.append(new_cluster)

            pbar.finish()
            print(' ')

        except KeyboardInterrupt:
            sys.stderr.write('\n\n\nCtrl+C: interrumpiendo\n\n\n')
            self.queue.queue.clear()
            for i in range(self.cfg.cores):
                self.queue.put(None)
            sys.exit()
        else:
            for i in range(self.cfg.cores):
                self.queue.put(None)
            for th in threads:
                th.join()
        return clusters

    def make_clustered(self, poses):
        fclt = open(self.clt_path, "wt")
        clusters = OrderedDict()
        cls = {}
        for i, cluster in enumerate(self.clusterizar_poses(poses)):
            best_pose = cluster[0]
            cl_name = "Site_{}_E{:.1f}".format(i + 1, best_pose.get_score())
            clusters[cl_name] = cluster
            fclt.write('Cluster #{} ( {:.1f} kcal/mol): {} poses; best pose: {}; site: ({:.2f}, {:.2f}, {:.2f})\n'
                       .format(i + 1, best_pose.get_score(), len(cluster), best_pose.num_execution, *best_pose.coords))
            c ={
                'cluster':i+1,
                'score':best_pose.get_score(),
                'size': len(cluster),
                'best_pose': best_pose.num_execution,
                'coords':best_pose.coords,
                'option':self.cfg.opcion
            }
            cls['cl_'+str(i+1)]=c;
            best_pose.copy_files(self.cfg.OUTPUT_DIRS['bestScore'])
        fclt.close()
        with open(self.clt_json_path, 'w') as json_file:
            json.dump(cls, json_file)

        self.fusion_graficas_en_cl(clusters)

        return clusters

    def fusion_graficas_en_cl(self, clusters):

        clusters = [cl[0].get_score() for cl in clusters.values() for _ in cl]
        title = "Clustered Docking Results ({} on {}):\n Binding Energy Frequency"\
            .format(self.cfg.name_query, self.cfg.name_target)
        fname = os.path.join(self.cfg.file_input, self.cfg.name_input + "_Clustered")
        self.cfg.graphicsGenerator.generate_histogram_2(
            clusters, self.cfg.plot_data, 'Clusters', 'Unclustered poses', title,
            'Binding energy (kcal/mol)', 'Frequency', 'symlog', fname)
