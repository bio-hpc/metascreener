#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# 
# water related code
# v.0.1 start  26.1.2012
# v.0.2 rewritten class  2012.4.11
# 
#
"""
        - is RECEPTOR available?

        - is EXP_WAT  available?

        - is WAT_MAP  available?

        -for each pose:
            - clean LIG/LIG overlaps ( DeltaS = map_point )
            - clean LIG/REC overlaps ( DeltaS = map_point )
            ####### - clean FREE WATERS      ( DeltaS = map_point  ) ???
            ####### - score BRIDGING WATERS  ( DeltaH - DeltaS )
            - score BRIDGING WATERS  ( DeltaH - DeltaS )
            

    FREE WATERS issue:
        - are more favorable for a ligand, hence they should be kept?
        - are less favorab

"""

import HelperFunctionsN3P as hf
from numpy import array
#CLASH = 2.03 # min. distance between W and real atoms (lig, rec) # XXX to remove spurious water in 2zye
#CLASH = 2.15 # min. distance between W and real atoms (lig, rec)

LONELINESS_DISTANCE = 3.5 # to be used to remove lone waters not interacting with anything..b

# TODO add a function to renumber the PDBQT after removing waters?
# XXX MAKE IT A CLASS!!!


class processHydroDocking:


    def __init__(self, pose=None,           # advanced pose to process [text, coords, water_bridge, ...]
                  gridmap=None,              # grid map (file/dictionary)

                  # distance parms
                  mapdistrange=1.0,     # distance around W coords to look for grid points
                  clust_tol = 2.0,      # cluster tolerance
                  interact_dist = 3.5,  # W-RecAtom interaction distance
                  clash= 2.03,          # min.distance allowed between W/atoms (lig, rec) # XX to remove spurious watre
                  loneliness_dist = 3.5, # max distance between W and interacting rec atoms

                  # energy parms
                  cutoff_weak = -0.35,  # weak water e.cutoff
                  cutoff_strong = -0.5, # strong water e.cutoff
                  desolvEntropy=-0.2,   # desolvation entropy
                  conservedwaterentropy=0,  # add an entropy penalty also for conserved waters

                  ignore_types = ['H', 'HD', 'W'], # atoms ignored for lig_overlap
                  debug = False):   # ignore atom types for contacts

        if gridmap == None:
            #raise "No water map provided"
            print "No water map provided"
            return False
        print "WARNING processHydroDocking:_init_> clash distance [%2.3f] is extremely low! Test with some case studies" % clash
        self.gridmap = gridmap
        self.pose = pose
        self.mapdistrange = mapdistrange
        self.clust_tol = clust_tol
        self.interact_dist = interact_dist
        self.clash = clash
        self.loneliness_dist = loneliness_dist

        self.cutoff_weak = cutoff_weak
        self.cutoff_strong = cutoff_strong
        self.desolvEntropy = desolvEntropy
        self.ignore_types = ignore_types
        self.conservedwaterentropy = conservedwaterentropy

        self.qs = hf.QuickStop()

        self.debug = debug

        if not (pose == None) and not (gridmap == None):
            self.process

    
    def process(self):

        # w-lig overlap -> ['water_lig_over']
        self.ligOverlapWaters() 
        # w-rec overlap -> ['water_rec_over']
        self.recOverlapWaters()

        # get energies for ['water_bridge_score'], ['water_lig_over_penalty'], ['water_rec_over_penalty']
        self.getWaterGridEnergy()

        # cluster ['water_bridge']
        self.clusterWaters()

        # clean-up extra_weak waters (increment ['water_rec_over_penalty'], if necessary
        self.weakWaterCleanup()

        # score waters and update PDBQT
        self.rankWaters()

        # normalize ligand energy poses['e'] ; poses['leff']
        self.normalizeWaterScore()

        return self.pose






    def getMapPoints(self, coords=None, distance=1.0): # mapdata, coords=None, distance=1.0):
        """ get points around (distance) of coordinates (coords)
        """
        # XXX TODO it should become interpolator!
        if coords == None:
            print "getMapPoints> ERROR: no coordinates!"
            return False
        data = self.gridmap['values']
        v_min = self.gridmap['min']
        v_max = self.gridmap['max']
        spacing = self.gridmap['spacing']
        pts = self.gridmap['pts']
        harvesting = []

        pt_scan = int( round(float(distance)/(spacing)) )
        if pt_scan == 0: pt_scan = 1 # at least one point around
        if self.debug: print "Grid range: %2.2f [ +/- %d points : %2.2f ]" % (distance,pt_scan, pt_scan*spacing), 
        best = 0
        warning_issued = False
        if (coords[0] < v_max[0]) and (coords[0] > v_min[0]):
            if (coords[1] < v_max[1]) and (coords[1] > v_min[1]):
                if (coords[2] < v_max[2]) and (coords[2] > v_min[2]):
                    z_pt = int(round((coords[2] - v_min[2])/spacing))
                    y_pt = int(round((coords[1] - v_min[1])/spacing))
                    x_pt = int(round((coords[0] - v_min[0])/spacing))
                    for x_ofs in range(-pt_scan, pt_scan+1): 
                        x = x_pt + x_ofs
                        if x < 0 :
                            harvesting.append(0)
                            break
                        for y_ofs in range(-pt_scan, pt_scan+1): 
                            y = y_pt + y_ofs
                            if y < 0 :
                                harvesting.append(0)
                                break
                            for z_ofs in range(-pt_scan, pt_scan+1): 
                                z = z_pt + z_ofs
                                if z < 0 :
                                    harvesting.append(0)
                                    break
                                try:
                                    harvesting.append( data[z,y,x] )
                                    if data[z,y,x] < best:
                                        best = data[z,y,x]
                                except:
                                    if not warning_issued:
                                        msg = ('*** WaterProcessing> Warning! '
                                               'Wat(%2.3f,%2.3f,%2.3f) '
                                               'close to gridbox edge ***' % (coords[0], coords[1], coords[2])
                                               )
                                        best = 0
                                        print msg
                                        warning_issued = True
                                    
                                    harvesting.append( 0 )
                if self.debug: print "genMapPoints> %d pts [ best: %2.2f ]" % (len(harvesting), best),
                return harvesting, best
        return False



    def ligOverlapWaters(self): 
        """
        remove ligand-overlapping w-atoms in a pose
        """
        #, cutoff = CLASH, 
        ignore_types = self.ignore_types
        #ignore_types = [ 'W' ] 
        # add a larger tolerance for HD?

        #cutoff = 2.4

        cutoff = self.clash ** 2
        log = []
        overlapping = []
        for w in self.pose['water_bridge']:
            try:
                for a in self.pose['text']:
                    if not w == a:
                        if isAtom(a) and  (not getAtype(a) in self.ignore_types):
                            d = dist(w, a, sq=0)
                            #if d < self.clash:
                            if d < cutoff:
                                overlapping.append(w)
                                self.pose['text'].remove(w)
                                raise self.qs
            except:
                pass
        if self.debug:
            print "Processed: %d | Lig-overlap %d" % (len(self.pose['water_bridge']), len(overlapping) )
        for w in overlapping:
            idx = self.pose['water_bridge'].index(w)
            self.pose['water_bridge'].remove(w)
            self.pose['water_bridge_contacts'].pop(idx)

        self.pose['water_over_lig'] = overlapping
                    
    def recOverlapWaters(self): # pose, cutoff = CLASH,
        #ignore_types = ['HD', 'H', 'W'] ):
        """ INPUT : pdb lig (multi)model and pdb target model
            OUTPUT: cleaned pdb lig model
         """
        #print "WARNING! missing interactions! Line B1"
        overlapping = []
        atom_pool = []
        cutoff = self.clash**2
        #cutoff += 0.5
        #cutoff = 0
        #for a in self.pose['vdw_contacts']: # PDBQT, no-HD   # XXX TODO BUG Line B1
        for aset in self.pose['water_bridge_contacts']: # PDBQT, no-HD   # XXX TODO BUG Line B1
            for a in aset:
                if not hf.getAtype(a) in self.ignore_types:
                    atom_pool.append(a)
        if self.debug:
            fp = open('DEBUG_rec_overlap.pdb','w')
            fp.write("REMARK  WATERS REMOVED BY RECEPTOR CLASHES")
        for w in self.pose['water_bridge']:
            try: # try/except is faster
                for a in atom_pool:
                    #if hf.dist(w, a, sq=False) < self.clash:
                    if hf.dist(w, a, sq=False) < cutoff:
                        overlapping.append(w)
                        self.pose['text'].remove(w)
                        #print "\n\n\n ####  REMOVED", w
                        if self.debug:
                            fp.write(w+"\n")
                            fp.write(a+"\n")
                        raise self.qs
            except:
                pass 
        if self.debug:
            fp.close()
            print "Processed: %d | Rec-overlap %d" % (len(self.pose['water_bridge']), len(overlapping) )
        for w in overlapping:
            idx = self.pose['water_bridge'].index(w)
            del self.pose['water_bridge_contacts'][idx]
            self.pose['water_bridge'].remove(w)
        self.pose['water_over_rec'] = overlapping

    def getWaterGridEnergy(self): 

        #                    cutoff_weak = -0.35,   # weak water e.cutoff
        #                    cutoff_strong = -0.5,  # strong water e.cutoff
        #                    desolvEntropy=-0.2,    # desolvation entropy
        #                    mapdistrange = 0.5):   

        # TODO  to be used to 'minimize' the water position too?
        #       looking for the best spot for a water
        #       and increase the energy accordingly?
        # calculate the score for bridging waters;
        self.pose['water_bridge_scores'] = []
        for w in self.pose['water_bridge']:
            points, best_point = self.getMapPoints( coords = hf.atomCoord(w),
                                         distance = self.mapdistrange)
            self.pose['water_bridge_scores'].append(best_point)
        # calculate ligand-overlapping penalties
        self.pose['water_over_lig_penalty'] = []
        for w in self.pose['water_over_lig']:
            points, best_point = self.getMapPoints( coords = atomCoord(w),
                                        distance = self.mapdistrange)
            self.pose['water_over_lig_penalty'].append( -best_point)
        # calculate rec-overlapping penalties
        self.pose['water_over_rec_penalty'] = []
        for w in self.pose['water_over_rec']:
            self.pose['water_over_rec_penalty'].append(-self.desolvEntropy)


    def clusterWaters(self): #pose, clust_tolerance=2.0, desolvEntropy=0):
        # cluster waters
        # XXX
        # energy from the cluster?
        # once 3 waters are reclustered (3->1)
        # two desolvEntropy penalties should be issued?
        # XXX
        unclustered_waters = self.pose['water_bridge'][:] # XXX NOT SURE IT"S NECESSARY

        # cluster waters
        water_clusters = hf.clusterAtoms(unclustered_waters, tol=self.clust_tol)

        # calculate clustering energy
        self.pose['water_cluster_penalty'] = []
        remove_from_text = []
        for pop in water_clusters:
            if len(pop)>1:
                this_cluster_centroid = hf.avgCoord(pop)
                this_cluster_penalty = -self.desolvEntropy * (len(pop)-1)
                this_cluster_energy = 0
                this_cluster_contacts = []
                closest_to_centroid = None
                closest_dist = 999999
                for w in pop:
                    # get the w_index + w_score
                    idx = self.pose['water_bridge'].index(w)
                    this_cluster_energy += self.pose['water_bridge_scores'][idx]
                    remove_from_text.append(w)
                    # find water closest to centroid (to be conserved)
                    # get the distance from the cluster average
                    centr_dist =  hf.quickdist( hf.atomCoord(w), this_cluster_centroid, sq = False)
                    a = [ hf.makePdb(coord=this_cluster_centroid) ]
                    #writeList('centroid.pdb', a)
                    if centr_dist <= closest_dist:
                        closest_dist = centr_dist
                        closest_to_centroid = w
                    del self.pose['water_bridge'][idx]
                    del self.pose['water_bridge_scores'][idx]
                    # update contacts
                    for a in self.pose['water_bridge_contacts'][idx]:
                        if not a in this_cluster_contacts:
                            this_cluster_contacts.append(a)
                    del self.pose['water_bridge_contacts'][idx]
                # update PDBQT text
                # XXX DEBUGGINGH
                #print type(remove_from_text), remove_from_text[0]
                #writeList('REMOVING_WATERS.pdb', remove_from_text)
                #writeList('current_ligand.pdbqt', pose['text'])

                for w in remove_from_text:
                    if not w == closest_to_centroid:
                        try:
                            text_idx = self.pose['text'].index(w)

                            del self.pose['text'][text_idx]
                        except:
                            pass
                # use the closest to be updated with clustering coords
                closest_index = self.pose['text'].index(closest_to_centroid)
                water = self.pose['text'][closest_index]
                coord_text = "%8.3f%8.3f%8.3f" % (this_cluster_centroid[0], 
                                                  this_cluster_centroid[1],
                                                  this_cluster_centroid[2])
                cluster_water = water[0:30]+coord_text+water[54:] # XXX ugly, but it works...
                self.pose['text'][closest_index] = cluster_water
                # update water_bridge list+score, water_cluster_penalty list
                self.pose['water_bridge'].append(cluster_water)
                self.pose['water_bridge_scores'].append(this_cluster_energy)
                self.pose['water_cluster_penalty'].append(this_cluster_penalty)
                self.pose['water_bridge_contacts'].append(this_cluster_contacts)
                if self.debug:
                    print "CLUSTER SIZE", len(pop)
                    print "CLUSTER ENRG", this_cluster_energy
                    print "CLUSTER PENL", this_cluster_penalty
                    #print "CLUSTER FINL", clust_energy+clust_penalty
                    print "=============="

    def normalizeWaterScore(self): #pose,entropyPenalty=False):

        # keep track of the original energy values
        if self.debug:
            old_e =  self.pose['energy']
            old_leff = self.pose['leff']

        # rec_displaced waters
        rec_displaced = 0
        for p in self.pose['water_over_rec_penalty']:
            rec_displaced += p
        #    print p # XXX
        #print "RECDISP", rec_displaced  # XXX 
        
        # lig_displaced waters
        lig_displaced = 0
        for p in self.pose['water_over_lig_penalty']:
            lig_displaced += p

        # clustering-displaced
        clust_displaced = 0
        for p in self.pose['water_cluster_penalty']:
            clust_displaced += p

        # count heavy at for lig.efficiency
        heavy_atoms = 0
        for a in self.pose['text']:
            if hf.isAtom(a) and ( not hf.getAtype(a) in ['HD', 'W'] ):
                heavy_atoms += 1

        # energy correction
        if self.conservedwaterentropy:
            # XXX read the penalty from a variable!
            entropy = (0.2)*len(self.pose['water_bridge'])
            #print " ENTROPY PENALTY = ", entropy
        else:
            entropy = 0
        self.pose['energy'] += lig_displaced + rec_displaced + clust_displaced + entropy

        # lig.efficiency correction
        self.pose['leff'] = self.pose['energy'] / float( heavy_atoms )


        if self.debug:
            #print "\n# PENALTY:\t +%2.3f [rec: %2.3f, lig: %2.3f, clust: %2.3f ]" % (rec_displaced+lig_displaced+clust_displaced,
            #        rec_displaced, lig_displaced, clust_displaced)
            print "  Penalties:"
            print "   - lig overlap     : %2.3f" % lig_displaced
            print "   - rec overlap     : %2.3f" % rec_displaced
            print "   - cluster penalty : %2.3f" % clust_displaced
            print "   - extra entropy   : %2.3f" % entropy

            print "   ENERGY:\t %2.3f [ old: %2.3f ]" %  (self.pose['energy'], old_e)
            print "   L.EFF.:\t %2.3f [ old: %2.3f ]\n" %  (self.pose['leff'], old_leff)
        #return pose



    def rankWaters(self): #pose, cutoff_weak, cutoff_strong):
        # keep track of the original energy values
        if self.debug:
            old_e =  pose['energy']
            old_leff = pose['leff']

        rank_line = "REMARK  %s water ( score: %2.2f )\n"
        self.pose['water_bridge_rank'] = []
        for idx in range(len(self.pose['water_bridge'])):
            water = self.pose['water_bridge'][idx]
            score = self.pose['water_bridge_scores'][idx]

            if score < self.cutoff_strong:
                # strongly bound
                rank = 'STRONG'
                score_comment = rank_line % (rank, score)
            elif score < self.cutoff_weak:
                # weakly bound
                rank = 'WEAK'
                score_comment = rank_line % (rank, score)
            else:
                # transient trapped/bulk water
                rank = 'TRAPPED/BULK'
                score_comment = rank_line % (rank, score)
            self.pose['water_bridge_rank'].append( [ rank, score ])
            # update the PDBQT text
            mark = self.pose['text'].index(water)
            txt = self.pose['text'][mark]
            self.pose['text'][mark] = score_comment + txt
        if self.debug:
            for w in self.pose['water_bridge_rank']:
                print "W:", w

    def weakWaterCleanup(self): #
        #pose, cutoff_weak = -0.35, cutoff_strong=-0.5, interact_dist=3.5 ):
        """ clean-up extra_weak waters (increment ['water_rec_over_penalty'], if necessary"""
        org_waters = len(self.pose['water_bridge'])
        #ignore_types = ['HD']

        lone_water = []
        interact_dist = self.interact_dist**2
        hb_types = ['OA', 'NA', 'SA', 'N', 'O', 'OA', 'NA', 'SA']
        hb_types += hf.METALS 
        for idx in range(len(self.pose['water_bridge'])):
            water = self.pose['water_bridge'][idx]
            score = self.pose['water_bridge_scores'][idx]
            # analyze only waters that are not ranked strong
            if score >= self.cutoff_strong: 
                atom_pool = [ a for a in self.pose['water_bridge_contacts'][idx] if hf.getAtype(a) in hb_types] 
                if self.debug:
                    hf.writeList('ATOM_POOL_%d_HB_%d.pdb' % (idx, sess), atom_pool, addNewLine=True)
                lone_water.append(water)
                try:
                    for a in atom_pool:
                        if (dist(water, a, sq=0)<= interact_dist):
                            #print "FOUND MATE",
                            #print dist(water, a, sq=True)
                            #print a.strip()
                            #print "------------------"
                            raise self.qs
                    #print "NO MATE FOR THIS", score
                    #print water.strip()
                except:
                    lone_water.remove(water)
                            
        for w in lone_water:
            idx = self.pose['water_bridge'].index(w)
            del self.pose['water_bridge'][idx]
            del self.pose['water_bridge_contacts'][idx]
        
            # EXPERIMENTAL
            #w_score = self.pose['water_bridge_scores'][idx]
            #if w_score > 
            # XXX THIS shouldn't happen:
            # a weakly bound water could be hanging in the bulk, but it should be accounted for
            # ...? 
            # how to describe the bulk solvent?
            # combine desolv map + discrete waters?
            # 

            self.pose['water_over_rec_penalty'].append( -self.pose['water_bridge_scores'].pop(idx) )
            # update PDBQT text
            #print pose['water_over_rec_penalty'] # XXX
            text_idx = self.pose['text'].index(w)
            del self.pose['text'][text_idx]


        if self.debug:
            print "LONE WATERS # REMOVED: ", (org_waters- len(self.pose['water_bridge']) )


            
        

