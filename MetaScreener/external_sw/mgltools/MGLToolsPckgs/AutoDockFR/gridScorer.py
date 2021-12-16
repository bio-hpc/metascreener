########################################################################
#
# Date: 2013 Authors: Michel Sanner, Pradeep Ravindranath
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2013
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/gridScorer.py,v 1.22 2014/08/18 21:36:04 pradeep Exp $
#
# $Id: gridScorer.py,v 1.22 2014/08/18 21:36:04 pradeep Exp $
#

from AutoDockFR.trilinterp import trilinterp
import os.path
from time import time
from bhtree import bhtreelib
from math import sqrt
from MolKit.molecule import AtomSet
import numpy

class GridScorer:
    """
    Scorer using affinity grids
    """

    def __init__(self, mapFileList):
        self.atypes = {}
        self.charge = {}
        self.abscharge = {}
        
        # read autogrid maps we assume the maps exist and are name 1abf_rec.C.map
        from Volume.IO.AutoGridReader import ReadAutoGrid
        reader = ReadAutoGrid()
        maps = {}
        self.mapFileList = mapFileList
        self.maxValues = {} # atomType: maxValue in grid
        for mapName in mapFileList:
            atype = os.path.splitext(os.path.splitext(mapName)[0])[1][1:]
            print atype, mapName
            maps[atype] = reader.read(mapName, 0)
            self.maxValues[atype] = max(maps[atype].data.flatten())

        self.maxGridVal = max(self.maxValues.values())
        
        self.maps = maps
        self.gridOrigin = ox, oy, oz = maps['e'].origin
	self.spacing = sx, sy, sz =  maps['e'].stepSize
	nbptx, nbpty, nbptz = maps['e'].data.shape
	sizeX, sizeY, sizeZ = self.boxDim = ((nbptx-1)*sx, (nbpty-1)*sy, (nbptz-1)*sz)
        self.gridEnd = (ox+sizeX, oy+sizeY, oz+sizeZ)
        self.inv_spacing = [1./x for x in maps['e'].stepSize]
        self.nbPoints = nbptx*nbpty*nbptz


    def addAtomSet(self, atoms, setName):
        # find all atom types in ligand and
        # build list of atom indices for each type
        atypes = {}.fromkeys(atoms.autodock_element)
        for k in atypes.keys():
            atypes[k] = []

        # put atom indices into atom type list i.e. 'c': [0, 2,5,7,8]
        for i, a in enumerate(atoms):
            atypes[a.autodock_element].append(i)
        self.atypes[setName] = atypes
        self.charge[setName] = atoms.charge
        self.abscharge[setName] = [abs(x) for x in self.charge[setName]]

        
    def getSurface(self, dockingObject):
        """
        identify MSMS surface components that is surrounding the ligand
        """
        import mslib
        ats = dockingObject.rigidRecAtoms
        radii = ats[0].top.defaultRadii()
        coords = ats.coords
        srf = mslib.MSMS(coords=coords, radii=radii)
        # compute reduced surface for all components
        srf.compute_rs(probe_radius=1.5, allComponents=1)

        # find the component closest to the ligand
        # 1 - get vertices for each component
        comp = srf.rsr.fst
        compVerts = []
        allRSv = {}
        while comp:
            print comp.nbf
            face = comp.ffa
            vd = {}
            while face:
                a, b, c = face._s()
                vd[a] = coords[a]
                vd[b] = coords[b]
                vd[c] = coords[c]
                face = face.nxt
            allRSv.update(vd)
            comp = comp.nxt
            compVerts.append(vd)

        # find smallest distance from ligand atom to RSVertex
        lig = dockingObject.ligand
        ligAtomsCoords = lig.allAtoms.coords

        vertInd = allRSv.keys()
        vertInd.sort()
        rsvCoords = []
        for ind in vertInd:
            rsvCoords.append(allRSv[ind])

        bht = bhtreelib.BHtree( rsvCoords, None, 10)
        results = numpy.zeros(5000, 'i')
        dist2 = numpy.zeros(5000, 'f')

        mini = 10000
        minInd = None
        for ligAtCoord in ligAtomsCoords:
            nb = bht.closePointsDist2(tuple(ligAtCoord), 4.0, results, dist2)
            for ind, d2 in zip(results[:nb], dist2[:nb]):
                if d2 < mini:
                    mini = d2
                    minInd = ind

        minInd = vertInd[minInd]
        # find the components that contain minInd
        comps = []
        for i in range(len(compVerts)):
            if minInd in compVerts[i].keys():
                comps.append(i)

        print 'closest receptor atom', minInd, allRSv[minInd], ats[minInd], ats[minInd].coords, comps

        if len(comps)>1:
            # use the largest one ! . this might not always be right !
            maxi = 0
            for c in comps:
                if len(compVerts[c])> maxi:
                    comp = c
                    maxi = len(compVerts[c])
            print "WARNING %d components found %s using largest one %d"%(
                len(comps), comps, comp)
        else:
            comp = comps[0]

        print 'Using component %d of the molecular surface'%comp
        srf.compute_ses(component=comp)
        srf.triangulate(component=comp, density=6.0)
        vf, vi, f = srf.getTriangles()
        verts = vf[:, :3]
        normals = vf[:, 3:6]

        # exclude vertices on edges of analytical surface to avoid
        # singular vertices with bad normals
        bhverts = []
        bhnormals = []
        for i in xrange(len(vf)):
            if vi[i][0] >= 0:
                bhverts.append(verts[i])
                bhnormals.append(normals[i])

        # verify that moving receptor atoms are in the cavity
        if dockingObject.setting['rmsdRecRef']:
            bhts = bhtreelib.BHtree( bhverts, None, 10)
            Aresults = numpy.zeros(len(bhverts), 'i')
            Adist2 = numpy.zeros(len(bhverts), 'f')
            movingRecAtoms = dockingObject.sortedRecRefAts
            #outsideAtoms = []
            for atom in movingRecAtoms:
                if atom.element=='H':
                    atom.outside = None
                    continue
                pt = atom.coords
                cut = 2.0
                nb = 0
                while nb==0:
                    nb = bhts.closePointsDist2(tuple(pt), cut, Aresults, Adist2)
                    if nb == 0:
                        cut += 1.0

                closestSurfInd = Aresults[numpy.argmin(Adist2[:nb])]
                clSP = bhverts[closestSurfInd]
                clN = bhnormals[closestSurfInd]

                # vector for surface to atom
                v = [ pt[0]-clSP[0], pt[1]-clSP[1], pt[2]-clSP[2]]

                # dot product of surface normal with v
                dot = clN[0]*v[0] + clN[1]*v[1] + clN[2]*v[2]
                if dot < 0:
                    # implments that only atoms more the 1.0 outside surface
                    # make the side chain be rejected
                    #n = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
                    #print 'ATOM outside cavity ', atom.full_name(), 'by', n
                    #if n>1.0:
                    #    outsideAtoms.append(atom)

                    # tag atom as outside
                    atom.outside = True
                else:
                    atom.outside= False
            #import pdb
            #pdb.set_trace()
            from MolKit.protein import ResidueSet
            notInPocket = ResidueSet([])
            for res in movingRecAtoms.parent.uniq():
                nba = 0
                nbaout = 0
                for a in movingRecAtoms:
                    if a.parent != res: continue
                    if a.element != 'H':
                        nba +=1 # one more atom in this residue
                    #print a.name
                    if a.outside:
                        #print "OUT",a.name
                        nbaout +=1
                    del a.outside
                #print 'AAAA', res.name, nba, nbaout
                if nbaout==nba: # all are out
                    notInPocket.append(res)

            if len(notInPocket):
                print 'Side chain atoms for residue are not in pocket', notInPocket.full_name()
                raise ValueError

            #if len(outsideAtoms):
            #    print 'Residue(s) are not in pocket, please remove from flexRec'
            #    for res in AtomSet(outsideAtoms).parent.uniq():
            #        #if len(res.atoms) == len(outsideAtoms):
            #        print "    ", res.name
            #    raise ValueError
        return verts, normals
    

    def fixTranslation(self, dockingObject, fixMaps=False):
	##
	## limit translations to favorable grid points
	##
        
        name = dockingObject.setting['Receptor']
        name = os.path.splitext(os.path.basename(name))[0]

        ## FIXME .. we can;t be sure ligandTree.root.motion.motionList[1]
        ## is the boxtranslation
        
        # get handle to translation and boxTranslation motion objects
        boxTrans = dockingObject.gnm.ligandTree.root.motion.motionList[1]
        # we configure the size of the boxTrans box to match the AutoDockGrid so that
        # good genes that percents of the box size will be correct
        boxTrans.configure(boxDim=self.boxDim)
        
        # get affinity map for root atom
        rootAtom = dockingObject.ligand.ROOT
        rootMap = self.maps[rootAtom.autodock_element].data

        mapECutOff = dockingObject.setting['mapECutOff']
        if fixMaps:
            maps = self.maps
            ox, oy, oz = self.gridOrigin
            sx, sy, sz =  maps['e'].stepSize
            nbptx, nbpty, nbptz = maps['e'].data.shape
            sizeX, sizeY, sizeZ = self.boxDim
            goodPtsGene = []
            goodc = []
            coords = []
            cut = 0.0
            print 'reducing box'

            ###import numpy
            result = numpy.zeros( (500,), 'i' )
            dist2 = numpy.zeros( (500,), 'f' )
            bht = dockingObject.receptorBht

            # get parameters of search box to select points in AD grids that
            # fall into search box adn are not too close to the protein
            # search box edge lengths

            # AutoGrid map parameter
            sbdimx, sbdimy, sbdimz = self.boxDim
            sbox, sboy, sboz = ox, oy, oz
            sbex, sbey, sbez = ox+sbdimx, oy+sbdimy, oz+sbdimz

            if dockingObject.setting['useXmlBox']: # only take grid points that fall inside the ligand's
                # search box size
                sbdimx, sbdimy, sbdimz = boxTrans.boxDim # translation box
                # search box center
                sbcenterx, sbcentery, sbcenterz = trans.point2
                # search box origin
                sbox, sboy, sboz = sbcenterx-(sbdimx*.5), sbcentery-(sbdimy*.5), sbcenterz-(sbdimz*.5)
                # search box end
                sbex, sbey, sbez = sbcenterx+(sbdimx*.5), sbcentery+(sbdimy*.5), sbcenterz+(sbdimz*.5)

            t0 = time()
            inBoxPtsCounter = 0
            #import pdb
            #pdb.set_trace()

            mini = 0.0
            maxi = 1.0
            removedPtsInd = []
            keptijk = []
            for i in range(nbptx+1):
                x = ox+i*sx
                if x<sbox or x>sbex: continue
                for j in range(nbpty+1):
                    y = oy+j*sy
                    if y<sboy or y>sbey: continue
                    for k in range(nbptz+1):
                        z = oz+k*sz
                        if z<sboz or z>sbez: continue
                        inBoxPtsCounter += 1

                        # check if grid point is far enough from closest receptor atom
                        nb = bht.closePointsDist2((x,y,z), 1.0, result, dist2)
                        if nb>500:
                            raise 
                        keep = True
                        for aind, anum in enumerate(result[:nb]):
                        #	#if dist2[aind] < 12.0: # grid point is too close to receptor atom
                            keep = False
                            break

                        if keep:
                            goodc.append( (x, y, z) )
                            keptijk.append((i,j,k))
                            # compute percentage for this point in AutoGrip Map
                            gx, gy, gz = (x-sbox)/sbdimx, (y-sboy)/sbdimy, (z-sboz)/sbdimz
                            assert mini-gx<0.00001 and gx-maxi<0.00001 and \
                                   mini-gy<0.00001 and gy-maxi<0.00001 and \
                                   mini-gz<0.00001 and gz-maxi<0.00001 
                            goodPtsGene.append( (gx, gy, gz)  )
                        else:
                            removedPtsInd.append((i,j,k))
                            coords.append( (x, y, z) )

            verts, normals = self.getSurface(dockingObject)
            srfVerticesBHT = bhtreelib.BHtree(verts, None, 10)

            reallyGood = []
            reallyGoodGenes = []
            anchorGood = []
            anchorGoodGenes = []
            removed = []
            keptijk2 = []
            t0 = time()

            for pt, gene, ijk in zip(goodc, goodPtsGene, keptijk):
                cut = 2.0
                nb = 0
                while nb==0:
                    nb = srfVerticesBHT.closePointsDist2(tuple(pt), cut, result, dist2)
                    cut += 2.
                vertInd = result[numpy.argmin(dist2[:nb])]
                vx, vy, vz = verts[vertInd]
                n1x = pt[0]-vx
                n1y = pt[1]-vy
                n1z = pt[2]-vz
                nx, ny, nz = normals[vertInd]
                dot = nx*n1x + ny*n1y + nz*n1z
                if dot > 0.0: # point is outside the surface
                    reallyGood.append(pt)
                    reallyGoodGenes.append(gene)
                    keptijk2.append(ijk)
                    i,j,k, = (ijk)
                    if rootMap[i,j,k,] < mapECutOff:
                        anchorGood.append(pt)
                        anchorGoodGenes.append(gene)
                else:
                    # compute distance to closest surface point
                    d2 = n1x*n1x + n1y*n1y + n1z*n1z
                    if d2<0.5625: # if less than 0.75**2 keep it
                        reallyGood.append(pt)
                        reallyGoodGenes.append(gene)
                        keptijk2.append(ijk)
                    else:
                        removed.append(pt)
                        removedPtsInd.append(ijk)

            print time()-t0
            #numpy.save('anchorPoints.npy', anchorGood)
            if len(reallyGood)==0:
                print "NO GOOD POINTS FOR ",name
                raise
            numpy.save('%s_goodPoints%3.2f.npy'%(name, mapECutOff), reallyGood)
            numpy.save('%s_anchorPoints%3.2f.npy'%(name, mapECutOff), anchorGood)
            f = open(dockingObject.setting['transPointsFile'], 'w')
            f.write("# anchor points for %s\n"%name)
            f.write("anchorAtomName = '%s'\n"%rootAtom.name)
            f.write("mapType='%s'\n"%rootAtom.autodock_element)
            f.write("boxDim = (%.3f,%.3f,%.3f)\n"%self.boxDim)
            f.write("origin = (%.3f,%.3f,%.3f)\n"%self.gridOrigin)
            f.write("spacing = (%.3f,%.3f,%.3f)\n"%self.spacing)
            f.write("mapECutOff = %.3f\n"%mapECutOff)
            f.write("genes = (%s)\n"%str(anchorGoodGenes))
            f.close()
            #numpy.save('%removed1.npy', coords)
            #numpy.save('removed2.npy', removed)
            goodc = reallyGood
            goodPtsGene = reallyGoodGenes
            
            self.goodPointsBHT = bhtreelib.BHtree(goodc, None, 10)
            self.result = numpy.zeros( (5000,), 'i' )
            self.dist2 = numpy.zeros( (5000,), 'f' )

            origin = self.gridOrigin
            inv_spacing = self.inv_spacing
            # only use surface points from surface that fall inside the box
            ## vInBox = []
            ## for i in xrange(len(verts)):
            ##     x,y,z = verts[i]
            ##     if x<ox: continue
            ##     if x>sbex: continue
            ##     if y<oy: continue
            ##     if y>sbey: continue
            ##     if z<oz: continue
            ##     if z>sbez: continue
            ##     vInBox.append((x,y,z))

            ## srfVertInBoxBHT = bhtreelib.BHtree(vInBox, None, 10)

            print 'fixing maps'
            newData = {}
            #values = {}
            for atype, amap in self.maps.items():
                newData[atype] = amap.data.copy()
            #    values[atype] = trilinterp(vInBox, amap.data, inv_spacing, origin)

            mini = 999999
            maxi = 0.0
            for i, j, k in removedPtsInd:
                x = ox+i*sx
                y = oy+j*sy
                z = oz+k*sz
                cut = 2.0
                nb = 0
                while nb==0:
                    nb = self.goodPointsBHT.closePointsDist2((x,y,z), cut, result, dist2)
                    cut += 2.

                indexOfMinDistVert = result[numpy.argmin(dist2[:nb])]
                vx, vy, vz = goodc[indexOfMinDistVert]
                d2 = (x-vx)*(x-vx) + (y-vy)*(y-vy) +(z-vz)*(z-vz)
                im = 0
                for atype, amap in self.maps.items():
                    #value = values[atype][indexOfMinDistVert]
                    value = amap.data[keptijk2[indexOfMinDistVert]]
                    if d2 < 1.0:
                        newData[atype][i][j][k] = value + sqrt(d2)*100
                    else:
                        newData[atype][i][j][k] = value + 100 + d2*1000

            print 'maps fixed in', time()-t0, mini, maxi

            im = 0
            for atype, amap in self.maps.items():
                amap.data = newData[atype]
                im += 1
                
            from Volume.IO.AutoGridWriter import WriteAutoGrid
            writer = WriteAutoGrid()
            for atype, amap in self.maps.items():
                name = dockingObject.setting['Receptor']
                name = os.path.splitext(os.path.basename(name))[0]
                writer.write(amap, '%s_fixedWith%3.2f.%s.map'%(name , mapECutOff, atype))

            print 'Search space reduced by %5.2f percent (%d/%d) %5.2f percent (%d/%d) in box and %5.2f (%d/%d) total in %f'%(
                100.-100*len(goodPtsGene)/float(inBoxPtsCounter), len(goodc), inBoxPtsCounter,
		100.-100*len(anchorGoodGenes)/float(inBoxPtsCounter), len(anchorGoodGenes), inBoxPtsCounter,
		100.-100*len(goodPtsGene)/float(self.nbPoints), len(goodc), self.nbPoints, time()-t0)

        else:
            d = {}
            mapPath = os.path.split(self.mapFileList[0])[0]
            name2 = dockingObject.setting['transPointsFile']
            execfile(os.path.join(mapPath,name2), d)
            #print d['anchorAtomName'], rootAtom.name
            #assert d['anchorAtomName'] == rootAtom.name
            #assert d["mapType"] == rootAtom.autodock_element
            #for i in range(3):
            #    assert abs(d["boxDim"][i] - self.boxDim[i]) < 0.001
            #    assert abs(d["origin"][i] - self.gridOrigin[i]) < 0.001
            #    assert abs(d["spacing"][i] - self.spacing[i]) < 0.001
            anchorGoodGenes = d['genes']
            print 'Search space reduced by %5.2f percent (%d/%d)'%(
		100.-100*len(anchorGoodGenes)/float(self.nbPoints), len(anchorGoodGenes), self.nbPoints)
            #newDim = d['boxDim']

        boxTrans.configure(boxDim= dockingObject.setting['box_dimensions'])     
        # constrain the trabslation of anchor atom
        boxTrans.setGoodGenes(anchorGoodGenes)

        ## fix cut points. BoxTranslation allows cuts between x and y and y
        ## also between y and z. If good genes are given we do not want to cut
        ## inside the (x,y,z) anymore so we have to remove these cut points
        cutPoints = dockingObject.gnm.cutPoints
        print 'cutPoints before fixTranslation', cutPoints
        flg = dockingObject.gnm.firstLigandGeneIndex # this points to Qx
        dockingObject.gnm.cutPoints.remove( flg+5 )
        dockingObject.gnm.cutPoints.remove( flg+6 )
        print 'cutPoints after fixTranslation', cutPoints
        assert cutPoints[-1] < len(dockingObject.gnm)
    
    def score(self, coords, setName):
        score = 0.0
        origin = self.gridOrigin
        inv_spacing = self.inv_spacing
        charge = self.charge[setName]
        abscharge = self.abscharge[setName]
        maps = self.maps
        outsideBox = False

        # loop over atom types
        for atype, atinds in self.atypes[setName].items():
            pts = [coords[i] for i in atinds]
            values = trilinterp(pts, maps[atype].data, inv_spacing, origin)
## <<<<<<< gridScorer.py
##             if values==outsidePenalty:
##                 outsideBox = True
##                 score += values
##                 break
##             else:
##                 for v in values:
##                     score += v
##             #for v in values:
##             #    score += v
## =======
            if values is None:
                #print 'outsideHHHHHHHHHHHH', atype, self.maxValues[atype]
                outsideBox = True
                score += self.maxValues[atype]*len(coords)
                break
            else:
                for v in values:
                    score += v
##>>>>>>> 1.4
        
        if not outsideBox:
            evalues = trilinterp(coords, maps['e'].data, inv_spacing, origin)
            for i,v in enumerate(evalues):
                score += v*charge[i]
                #evalxChg.append(v*charge[i])
                
            
            dvalues = trilinterp(coords, maps['d'].data, inv_spacing, origin)
            for i,v in enumerate(dvalues):
                score += v * abscharge[i]
                #dvalxChg.append(v*charge[i])

        return score


    def scoreBreakDown(self, coords, setName):
        vdwTerm = None
        elecTerm = None
        desolvTerm = None
        score = 0.0
        origin = self.gridOrigin
        inv_spacing = self.inv_spacing
        charge = self.charge[setName]
        abscharge = self.abscharge[setName]
        maps = self.maps
        outsideBox = False
        vDWval =[9999]*len(coords)
        evalxChg = []
        dvalxChg = []
        from AutoDockFR.trilinterp import outsidePenalty
        # loop over atom types
        for atype, atinds in self.atypes[setName].items():
            pts = [coords[i] for i in atinds]
            values = trilinterp(pts, maps[atype].data, inv_spacing, origin)
            if values==outsidePenalty:
                outsideBox = True
                score += values
                break
            else:
                for ati, v in zip(atinds,values):
                    vDWval[ati] = v
                    score += v
        vdwTerm = score
        score = 0.0
        
        if not outsideBox:
            evalues = trilinterp(coords, maps['e'].data, inv_spacing, origin)
            for i,v in enumerate(evalues):
                score += v*charge[i]
                evalxChg.append(v*charge[i])
            elecTerm = score
            score = 0.0
            
            dvalues = trilinterp(coords, maps['d'].data, inv_spacing, origin)
            for i,v in enumerate(dvalues):
                score += v * abscharge[i]
                dvalxChg.append(v*abscharge[i])
            desolvTerm = score

        return {'vdw':vdwTerm, 'elec':elecTerm, 'desolvTerm':desolvTerm,
                'total':vdwTerm+elecTerm+desolvTerm},vDWval,evalxChg, dvalxChg

    #def initReallyGoodPop(self,dockingObject):

