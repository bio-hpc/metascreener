import random
import numpy
from math import sqrt
# -- The Point class represents points in n-dimensional space

class Point:
    # Instance variables
    # self.coords is a list of coordinates for this Point
    # self.n is the number of dimensions this Point lives in (ie, its space)
    # self.reference is an object bound to this Point
    # Initialize new Points

    def __init__(self, coords, reference=None):
        self.coords = coords
        self.n = len(coords)
        self.reference = reference
    # Return a string representation of this Point

    def __repr__(self):
        return str(self.coords)
# -- The Cluster class represents clusters of points in n-dimensional space


class Cluster:
    # Instance variables
    # self.points is a list of Points associated with this Cluster
    # self.n is the number of dimensions this Cluster's Points live in
    # self.centroid is the sample mean Point of this Cluster

    def __init__(self, points):
        # We forbid empty Clusters (they don't make mathematical sense!)
        if len(points) == 0: raise Exception("ILLEGAL: EMPTY CLUSTER")
        self.points = points
        self.n = points[0].n
        # We also forbid Clusters containing Points in different spaces
        # Ie, no Clusters with 2D Points and 3D Points
        for p in points:
            if p.n != self.n: raise Exception("ILLEGAL: MULTISPACE CLUSTER")
        # Figure out what the centroid of this Cluster should be
        self.centroid = self.calculateCentroid()
    # Return a string representation of this Cluster

    def __repr__(self):
        return str(self.points)
    # Update function for the K-means algorithm
    # Assigns a new list of Points to this Cluster, returns centroid difference

    def update(self, points):
        old_centroid = self.centroid
        self.points = points
        self.centroid = self.calculateCentroid()
        x1,y1,z1 = old_centroid.coords
        x2,y2,z2 = self.centroid.coords
        return sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) + (z1-z2)*(z1-z2) )

    # Calculates the centroid Point - the centroid is the sample mean Point
    # (in plain English, the average of all the Points in the Cluster)
    def calculateCentroid(self):
        centroid_coords = []
        # For each coordinate:
        for i in range(self.n):
            # Take the average across all Points
            centroid_coords.append(0.0)
            for p in self.points:
                centroid_coords[i] = centroid_coords[i]+p.coords[i]
            centroid_coords[i] = centroid_coords[i]/len(self.points)
        # Return a Point object using the average coordinates
        return Point(centroid_coords)

    def radiusOfGyration(self):
        ptCoords = [x.coords for x in self.points]
        delta = numpy.array(ptCoords)-self.centroid.coords
        rg = sqrt( sum( numpy.sum( delta*delta, 1))/float(len(ptCoords)) )
        return rg

    def encapsualtingRadius(self):
        ptCoords = [x.coords for x in self.points]
        delta = numpy.array(ptCoords)-self.centroid.coords
        rM = sqrt( max( numpy.sum( delta*delta, 1)) )
        return rM


# -- Return Clusters of Points formed by K-means clustering
def kmeans(points, k, cutoff, initial=None):
    # Randomly sample k Points from the points list, build Clusters around them
    if initial is None:
        # Randomly sample k Points from the points list, build Clusters around them
        initial = random.sample(points, k)
    else:
        assert len(initial)==k

    clusters = []
    for p in initial: clusters.append(Cluster([p]))
    # Enter the program loop
    while True:
        # Make a list for each Cluster
        lists = []
        for c in clusters: lists.append([])
        # For each Point:
        for p in points:
            # Figure out which Cluster's centroid is the nearest
            x1,y1,z1 = p.coords
            x2,y2,z2 = clusters[0].centroid.coords
            smallest_distance = sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) +
                                      (z1-z2)*(z1-z2) )
            index = 0
            for i in range(len(clusters[1:])):
                x2,y2,z2 = clusters[i+1].centroid.coords
                distance = sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) +
                                 (z1-z2)*(z1-z2) )
                if distance < smallest_distance:
                    smallest_distance = distance
                    index = i+1
            # Add this Point to that Cluster's corresponding list
            lists[index].append(p)
        # Update each Cluster with the corresponding list
        # Record the biggest centroid shift for any Cluster
        biggest_shift = 0.0
        for i in range(len(clusters)):
            if len(lists[i]):
                shift = clusters[i].update(lists[i])
                biggest_shift = max(biggest_shift, shift)
        # If the biggest centroid shift is less than the cutoff, stop
        if biggest_shift < cutoff: break
    # Return the list of Clusters
    return clusters

def saveSphereModel(filename):
    g = vi.FindObjectByName('root|spheres')
    centers = g.getVertices()
    radii = g.vertexSet.radii.array
    f = open(filename, 'w')
    f.write("# rmin rmax\n")
    f.write("%6.2f  %6.2f\n"%(minR, maxR))
    f.write("\n")
    f.write("# number of levels\n")
    f.write("1\n")
    f.write("\n")
    f.write("# number of spheres in level 1\n")
    f.write("%d\n"%len(centers))
    f.write("\n")
    f.write("# x y z r of spheres in level 1\n")
    for r,c in zip(radii,centers):
        x,y,z = c
        f.write("%6.2f %6.2f %6.2f %6.2f\n"%(x,y,z,r[0]))
    f.write("\n")
    f.close()

## def computeMinRadius(mol):
##     # get all atoms with X coordinate within [-8, 8] and compute enclosing
##     # sphere radius. This assumes X aligned membrane proteins with center
##     # of membrane at (0,0,0)
##     from MolKit.molecule import AtomSet
##     membAtoms = AtomSet(filter( lambda a: a.coords[0]>=-8. and a.coords[0]<8.,
##                         mol.allAtoms))
##     membCoords = membAtoms.coords
##     # compute center
##     cx, cy, cz = center = numpy.sum(membCoords, 0)/len(membCoords)

##     # find max distance to center
##     minR = 0.
##     for a in membAtoms:
##         x,y,z = a.coords
##         d2 = (x-cx)*(x-cx) + (y-cy)*(y-cy) + (z-cz)*(z-cz)
##         if d2 > minR:
##             minR = d2
##     print 'center of membrane', center, 'min Radius:', sqrt(minR)
##     return sqrt(minR)


# -- Main function
if __name__=='__main__':
    from time import time
    import sys
    import Tkinter

    molname = sys.argv[1]

    # Create num_points random Points in n-dimensional space
    points = []
    from MolKit import Read
    mols = Read(sys.argv[1])

    # get minR from remark in last line of the file
    line = mols.parser[0].allLines[-1]
    if line[:11]!='REMARK Rmin':
        print 'pdb file does not provide REMARK Rmin on last line, using 10.0'
        minR = 10.0
    else:
        minR = float(line.split()[2])

    allAtoms = mols.allAtoms
    coords = allAtoms.coords

    # compute maxR
    maxR = 0
    for x,y,z in coords:
        d2 = (x*x) + (y*y) + (z*z)
        if d2 > maxR:
            maxR = d2
    maxR = sqrt(maxR)
    print 'max Radius:', maxR

    print 'make points'
    t1 = time()
    for c in coords:
        points.append(Point(c))
    print 'time to make points', time()-t1

    from DejaVu import Viewer
    vi = Viewer()
    from DejaVu.Points import Points
    atomsPts = Points('atoms', vertices=coords)
    vi.AddObject(atomsPts)

    from DejaVu.Spheres import Spheres
    seeds = []
    seedsCoords = []
    seedSpheres = Spheres('seeds')
    vi.AddObject(seedSpheres)

    minRSph = Spheres('minMax', centers=((0,0,0),(0,0,0),), radii=(minR,maxR),
                      inheritMaterial=False, materials=((0,1,0), (1,0,0),),
                      inheritFrontPolyMode=False, frontPolyMode='line',
                      visible=0)
    vi.AddObject(minRSph)
    
    factor = 0.7
    clusters = None
    
    def displayClusters(clusters, factor=0.7):

        from DejaVu.colors import red, green, blue, cyan, magenta, yellow, \
             pink, brown, orange, burlywood, darkcyan, gainsboro
        from DejaVu import colors
        colors = [ getattr(colors, name) for name in  colors.cnames ]
        #colors = [ red, green, blue, cyan, magenta, yellow, pink,
        #           brown, orange, burlywood, darkcyan, gainsboro]

        centers = []
        radiiG = []
        radiiM = []
        radii = []
        if clusters is None:
            return
        for i,cluster in enumerate(clusters):
            centers.append(cluster.centroid.coords)
            radg = cluster.radiusOfGyration()
            radm = cluster.encapsualtingRadius()
            #rad = radg/0.7
            rad = radg + factor*(radm-radg)
            radiiG.append(radg)
            radiiM.append(radm)
            radii.append(rad)
            
            ptCoords = [x.coords for x in cluster.points]
            pts = Points('cluster%d'%i, vertices=ptCoords, pickable=0,
                         inheritMaterial=0, materials=[colors[i%len(colors)]])
            vi.AddObject(pts)

        nbc = len(clusters)
        sph = Spheres('clustercenters', centers=centers,
                      radii=[2.], inheritMaterial=0, materials=colors[:nbc])
        vi.AddObject(sph)
        ## sph = Spheres('gyration_sph', centers=centers,
##                       radii=radiiG, pickable=0,
##                       inheritFrontPolyMode=0, frontPolyMode='line',
##                       inheritMaterial=0, materials=colors[:nbc],  visible=0)
##         vi.AddObject(sph)
##         sph = Spheres('encapsualting_sph', pickable=0,
##                       centers=centers, radii=radiiM,
##                       inheritFrontPolyMode=0, frontPolyMode='line',
##                       inheritMaterial=0, materials=[colors[i]], visible=0)
##         vi.AddObject(sph)
        print 'cluster with %d points rg:%.2f rM:%.2f ratio:%.2f %.2f'%(
            len(cluster.points), radg, radm, radg/radm, rad)
        sph = Spheres('spheres', centers=centers, pickable=0,
                      radii=radii, inheritFrontPolyMode=0,
                      frontPolyMode='line',
                      inheritMaterial=0, materials=colors[:nbc])
        vi.AddObject(sph)

    def onPick(pick):
        global clusters
        g, tmp = pick.hits.items()[0]
        vn = tmp[0][0] # vertex number
        atomNum = allAtoms[vn].number
        #print g.vertexSet.vertices.array[vn], allAtoms[vn].coords
        seeds.append(points[vn])
        seedsCoords.append(allAtoms[vn].coords)
        seedSpheres.Set(centers=seedsCoords, radii=(1,))
        t1 = time()
        clusters = kmeans(points, len(seeds), 0.5, seeds)
        print 'time to cluster points', time()-t1
        displayClusters(clusters, factor=factor)


    def clusterN(event=None):
        global clusters, seeds, seedsCoords
        howMany = int(event)
        from random import uniform
        seedsInd = []
        seeds = []
        seedsCoords = []
        for i in range(howMany):
            ind = int(uniform(0, len(allAtoms)))
            seeds.append(points[ind])
            seedsCoords.append(allAtoms[ind].coords)
            seedsInd.append( ind)
        t1 = time()
        clusters = kmeans(points, len(seeds), 0.5, seeds)
        print 'time to cluster points', time()-t1
        displayClusters(clusters, factor=factor)
        print 'seeds', seedsInd
        
        
    vi.processPicking = onPick

    root = Tkinter.Toplevel()
    master = Tkinter.Frame(root)
    master.pack()

    def undo_cb(event=None):
        global clusters
        seeds.remove(seeds[-1])
        seedsCoords.remove(seedsCoords[-1])
        seedSpheres.Set(centers=seedsCoords, radii=(1,))
        t1 = time()
        clusters = kmeans(points, len(seeds), 0.5, seeds)
        print 'time to cluster points', time()-t1
        displayClusters(clusters, factor=factor)
        
    def clear_cb(event=None):
        centers = []
        radiiG = []
        radiiM = []
        radii = []
        seeds.append(points[vn])
        seedsCoords.append(allAtoms[vn].coords)
        seedSpheres.Set(centers=seedsCoords, radii=(1,))
        t1 = time()
        for child in vi.rootObject.children:
            vi.RemoveObject(child)

    def scale_cb(event=None):
        global factor
        factor = int(event)/100.
        displayClusters(clusters, factor=factor)
        
    def save_cb(event=None):
        from os.path import splitext
        a,b = splitext(sys.argv[1])
        print 'saving',a+'.sph'
        saveSphereModel(a+'.sph')
        
    clear = Tkinter.Button(master, text='Clear', command=clear_cb)
    clear.pack()

    undo = Tkinter.Button(master, text='Undo', command=undo_cb)
    undo.pack()

    saveSph = Tkinter.Button(master, text='saveSph', command=save_cb)
    saveSph.pack()

    scale = Tkinter.Scale(master, label='scale radius', command=scale_cb)
    scale.pack()

    from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
    nbsph = ThumbWheel(master, width=100, height=40, labCfg={'text':'#sph:'},
                       callback=clusterN, type='int', min=1, continuous=False)
    
    
    vi.Normalize_cb()
    vi.Center_cb()
    
##     from MolKit.stringSelector import CompoundStringSelector
##     selector = CompoundStringSelector()
##     sel = selector.select
##     init = []
##     init.append(points[sel(mols,'2a79:A:TYR262:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:E:TYR262:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:I:TYR262:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:M:TYR262:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:N:ARG82:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:N:PHE242:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:F:PHE242:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:J:PHE242:CA')[0][0].number-1])
##     init.append(points[sel(mols,'2a79:B:PHE242:CA')[0][0].number-1])

    # Cluster the points using the K-means algorithm
##     t1 = time()
##     clusters = kmeans(points, len(init), 0.5, init)
##     print 'time to cluster points', time()-t1

##     from DejaVu.colors import red, green, blue, cyan, magenta, yellow, pink, \
##          brown, orange, burlywood, darkcyan, gainsboro
##     colors = [ red, green, blue, cyan, magenta, yellow, pink,
##                brown, orange, burlywood, darkcyan, gainsboro]

##     for i,cluster in enumerate(clusters):
##         ptCoords = [x.coords for x in cluster.points]
##         pts = Points('cluster%d'%i, vertices=ptCoords,
##                      inheritMaterial=0, materials=[colors[i]])
##         vi.AddObject(pts)
##         sph = Spheres('cluster_center%d'%i, centers=[cluster.centroid.coords],
##                       radii=[5.],
##                      inheritMaterial=0, materials=[colors[i]])
##         vi.AddObject(sph)
##         radg = cluster.radiusOfGyration()
##         sph = Spheres('gyration_sph%d'%i, centers=[cluster.centroid.coords],
##                       radii=[radg], inheritFrontPolyMode=0, frontPolyMode='line',
##                      inheritMaterial=0, materials=[colors[i]], visible=0)
##         vi.AddObject(sph)
##         radm = cluster.encapsualtingRadius()
##         sph = Spheres('encapsualting_sph%d'%i, centers=[cluster.centroid.coords],
##                       radii=[radm], inheritFrontPolyMode=0, frontPolyMode='line',
##                      inheritMaterial=0, materials=[colors[i]], visible=0)
##         vi.AddObject(sph)
##         # scale radM so taht ratio is 0.7
##         rad = radg/0.7
##         print 'cluster with %d points rg:%.2f rM:%.2f ratio:%.2f %.2f'%(
##             len(cluster.points), radg, radm, radg/radm, rad)
##         sph = Spheres('sph%d'%i, centers=[cluster.centroid.coords],
##                       radii=[rad], inheritFrontPolyMode=0, frontPolyMode='line',
##                      inheritMaterial=0, materials=[colors[i]])
##         vi.AddObject(sph)


    
    # Print the results
    #print "\nPOINTS:"
    #for p in points: print "P:", p
    #print "\nCLUSTERS:"
    #for c in clusters: print "C:", c

## from cluster import KMeansClustering
## cl = KMeansClustering(coords)
## clusters = cl.getclusters(8)
