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

from time import time
import Tkinter

from MolKit.molecule import Atom

points = []
vi = self.GUI.VIEWER
#from DejaVu.Points import Points
from DejaVu.Spheres import Spheres
seeds = []
seedsCoords = []
seedSpheres = Spheres('seeds')
vi.AddObject(seedSpheres)

keptCenters = []
keptRadii = []

factor = 0.5
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

        nbc = len(clusters)
        sph = Spheres('clustercenters', centers=keptCenters+centers,
                      radii=[2.], inheritMaterial=0, materials=colors[:nbc])
        vi.AddObject(sph)
        print 'cluster with %d points rg:%.2f rM:%.2f ratio:%.2f %.2f'%(
            len(cluster.points), radg, radm, radg/radm, rad)
        sph = Spheres('spheres', centers=keptCenters+centers, pickable=0,
                      radii=keptRadii+radii, inheritFrontPolyMode=0,
                      frontPolyMode='line',
                      inheritMaterial=0, materials=colors[:nbc])
        vi.AddObject(sph)

##     def onPick(pick):
##         global clusters
##         g, tmp = pick.hits.items()[0]
##         vn = tmp[0][0] # vertex number
##         atomNum = allAtoms[vn].number
##         #print g.vertexSet.vertices.array[vn], allAtoms[vn].coords
##         seeds.append(points[vn])
##         seedsCoords.append(allAtoms[vn].coords)
##         seedSpheres.Set(centers=seedsCoords, radii=(1,))
##         t1 = time()
##         clusters = kmeans(points, len(seeds), 0.5, seeds)
##         print 'time to cluster points', time()-t1
##         displayClusters(clusters, factor=factor)


def clusterN(event=None):
        global clusters, seeds, seedsCoords, points
        howMany = int(event)
        from random import uniform
        seedsInd = []
        seeds = []
        seedsCoords = []
        
        allAtoms = self.getSelection().findType(Atom)
        points = []
        for c in allAtoms.coords:
            points.append(Point(c))
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
        
root = Tkinter.Toplevel()
master = Tkinter.Frame(root)
master.pack()


def scale_cb(event=None):
    global factor
    displayClusters(clusters, factor=event)


def keepSpheres(event=None):
    g = vi.FindObjectByName('root|spheres')
    currentNum = len(keptRadii)
    keptCenters.extend( g.getVertices()[currentNum:] )
    keptRadii.extend( [r[0] for r in g.vertexSet.radii.array[currentNum:]] )
    self.clearSelection()

def deleteSpheres(event=None):
    global keptCenters, keptRadii
    keptCenters = []
    keptRadii = []
    clusterN(1)

def saveSphereModel(filename, minR=-1, maxR=-1):
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
    for r,c in zip(keptRadii, keptCenters):
        x,y,z = c
        f.write("%6.2f %6.2f %6.2f %6.2f\n"%(x,y,z,r))
    f.write("\n")
    f.close()


import tkFileDialog

def save_cb(event=None):
    initialFile = self.Mols[0].name+'_%d.sph'%len(keptRadii)
    file = tkFileDialog.asksaveasfilename(
        parent = master,
        filetypes=[ ('AutoFill Sph files', '*.sph'),('All files', '*') ],
        initialdir='.',
        initialfile=initialFile,
        title='save sphere file')
    if file=='': file = None
    if file:
        saveSphereModel(file)
        

keepSph = Tkinter.Button(master, text='keep Spheres', command=keepSpheres)
keepSph.pack()

keepSph = Tkinter.Button(master, text='delete kept Spheres', command=deleteSpheres)
keepSph.pack()

saveSph = Tkinter.Button(master, text='write Sphere File...', command=save_cb)
saveSph.pack()


from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
scale = ThumbWheel(master, width=100, height=30, labCfg={'text':'scale:'},
                   callback=scale_cb, type='float', min=0., max=1.,
                   oneTurn=1.)
scale.set(factor)

nbsph = ThumbWheel(master, width=100, height=30, labCfg={'text':'#sph:'},
                   callback=clusterN, type='int', min=1, continuous=False)
    
    
#execfile('scripts/clusterGUIpmv.py')
