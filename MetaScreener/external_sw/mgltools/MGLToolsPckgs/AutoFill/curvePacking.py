import upy
import math
import numpy
from numpy import linalg as LA
from random import random
helper=upy.getHelperClass()()

def angle(v1,v2):
    return numpy.arccos(numpy.dot(v1,v2)/(LA.norm(v1)*LA.norm(v2)))
    
def distance(a,b):
    d = numpy.array(a) - numpy.array(b)
    s = numpy.sum(d*d)
    return s

#def segmentCross(A,B,C,D):
#    #xrange ?
#    I1 = [min(A[0],B[0]), max(A[0],B[0])]
#    I2 = [min(C[0],D[0]), max(C[0],D[0])]
#    Ia = [max( min(A[0],B[0]), min(C[0],D[0]) ), min( max(A[0],B[0]), max(C[0],D[0])] )]
#    if (max(A[0],B[0]) < min(C[0],D[0]))
#        return False;
#    return numpy.dot(v1,v2)
def segmentCross(A,B,C,D):
    #are they parrallele
    AB=A-B
    CD=C-D
    a=angle(AB,CD)
#    print a,math.degrees(a)
    if a == math.pi or a == math.pi * 2 :
        #parrallele
        return False
    N_A = numpy.cross(A,B)
    N_C = numpy.cross(C,D)
    da=numpy.dot(A-C,N_C)
    db=numpy.dot(B-C,N_C)
    dc=numpy.dot(C-A,N_A)
    dd=numpy.dot(D-A,N_A)
    #print da,db,dc,db
    aa=False
    cc=False
    if da * db < 0.0 :
        aa=True
    elif da * db == 0.0 :
        #perpandicaular
        print "T"
    if dc * dd < 0.0 :
        cc=True
    elif dc * dd == 0.0 :
        #perpandicaular
        print "T"
    #print (aa and cc) 
    crossV=numpy.dot(A-C,B-D)
    if crossV < 0.0 :
        return True
    #print crossV #if negatif : cross
    return (aa and cc)  

def rmsd(A,B,C,D):
    da1=distance(A,C)
    da2=distance(A,D)
    db1=distance(B,C)
    db2=distance(B,D)
    d1=min(da1,db1)
    d2=min(da2,db2)
    return (d1+d2)/2.0

def norm(v):
    a,b,c=v
    return (math.sqrt( a*a + b*b + c*c))
    
def sphereInterpolate(A,B,C,D,radius,u):
    s=int(u/radius)
    directionS1=(B-A)#/norm(B-A)#normalized A-B = BA / B-A = AB
    directionS2=(D-C)#/norm(D-C)
    #generate the sphere along direction
    sp1=[]
    sp2=[]
    for i in range(1,s+1):
        sp1.append(A*(directionS1*i/s))
        sp2.append(C*(directionS2*i/s))
    r=[]
    for p in sp1:
        delta = numpy.array(sp2)-numpy.array(p)
        delta *= delta
        distA = numpy.sqrt( delta.sum(1) )
        #test = distA < 15.0#*2.0
        test = numpy.less_equal(distA, 7.0)
        #print distA
        if True in test:
            return True
    return False
    
def checkIntersect(listePtCurve,point,radius=5.0,u=20):
    #need a radius .... need distance between segement as well
    if len(listePtCurve) < 4:
        return False    
    #should do it only on closest one will be faster but not itsef...
    #indiceClose,coord = getClosest(point,listePtCurve[:-2],cutoff=u*4.)
    delta = numpy.array(listePtCurve[:-2])-numpy.array(point)
    delta *= delta
    distA = numpy.sqrt( delta.sum(1) )
    mini = min(distA)#force the distance
    if mini <= 7.0 :
        return True
    #ranges = [100.,150.0]
    indiceCloseId = numpy.nonzero( numpy.equal(distA, mini))[0][0]
    #indiceCloseId = numpy.nonzero( numpy.logical_and(numpy.greater_equal(distA, ranges[0]) ,numpy.less_equal(distA, ranges[1])) )
    indiceClose = numpy.nonzero( numpy.less_equal(distA, u*4))[0]
    #print indiceClose
    #indiceClose = indiceClose[0][0]#or random one ?
    #indiceClose = indiceCloseId[0][0]

    A=listePtCurve[-1]
    B=point
    r=[]
    for i in indiceClose:#listePtCurve[:-1]):
        if (i > len(listePtCurve)-2):
            continue
        C=listePtCurve[i-1]
        D=listePtCurve[i]
#        d=rmsd(A,B,C,D)
#        if d < cutoff :
        dr=sphereInterpolate(A,B,C,D,radius,u)
        r.append(dr)
#        if dr :
#            c=segmentCross(A,B,C,D)
#            r.append(c)
    if True in r:
        return True
    else:
        return False
    
def checkCollide(listePtCurve,point):
    #print (len(listePtCurve),len(point),point)
    if not len(listePtCurve):
        return False
    cutoff=0.5
    delta = numpy.array(listePtCurve)-numpy.array(point)
    delta *= delta
    distA = numpy.sqrt( delta.sum(1) )
    test = distA < cutoff
    if True in test:
        return True
    return False

def getClosest(point,v,cutoff=15.0):
    #reorder by distance from first point.
    delta = numpy.array(v)-numpy.array(point)
    delta *= delta
    distA = numpy.sqrt( delta.sum(1) )
    if cutoff < min(distA) :
        cutoff = distA+1.0 
    indiceClose = numpy.nonzero( numpy.less_equal(distA, cutoff))
    return indiceClose[0],numpy.take(v,indiceClose[0],0).tolist()

def getClosestOne(point,v):#,cutoff=15.0):
    #reorder by distance from first point.
    #print "get ",len(v),len(point),point
    delta = numpy.array(v)-numpy.array(point)
    delta *= delta
    distA = numpy.sqrt( delta.sum(1) )
    mini = min(distA)#force the distance
    #ranges = [100.,150.0]
    indiceCloseId = numpy.nonzero( numpy.equal(distA, mini))
    #indiceCloseId = numpy.nonzero( numpy.logical_and(numpy.greater_equal(distA, ranges[0]) ,numpy.less_equal(distA, ranges[1])) )

    #print indiceClose
    #indiceClose = indiceClose[0][0]#or random one ?
    indiceClose = indiceCloseId[0][0]
    #if len(indiceCloseId[0]) > 1 :
    #     indiceClose = int(random()*len(indiceCloseId[0]))
    #else :
    #     indiceClose = indiceCloseId[0][0]
    return indiceClose,mini#,v[indiceClose[0]]

def distance(a,b):
    d= numpy.array(a)-numpy.array(b)
    s=numpy.sum(d*d)
    return math.sqrt(s)
    
#when on a grid gave a similar hamiltonian path
def growAtsurface(faces,v,n,limit=0,nb=0):
    #limit is the size limit of the spline
    #n is the number of desired spline            
    #progress bar
    totalLength=0
    nbCurve=0
    data = numpy.array(v)
    mask_visisted = numpy.ones(len(v))
    mask_indice = numpy.array(range(len(v)))
    listePtCurveId=[]
    listePtCurve=[]
    curves=[]
    newPtId = 0
    mask_visisted[0]=0
    done = False
    counter=0
    counterCut=len(v)
    early = False
    helper.resetProgressBar()
    while not done :
        #get closest point in remaining point
        remaining_point = numpy.nonzero(mask_visisted)[0]
        if len(remaining_point) == 0 :
            done = True
            break
        #print remaining_point
        #indiceClose,closest = getClosest(data[newPtId],numpy.take(v,remaining_point,0))
        #take one of the indiceclose
        #newPtId = indiceClose[int(random()*len(closest))]
        #print ("pass ",data[newPtId],len(numpy.take(v,remaining_point,0)))
        closeId,distance = getClosestOne(data[newPtId],numpy.take(v,remaining_point,0))
        newPtId = remaining_point[closeId]
        #print ("return ",newPtId)
        if newPtId not in listePtCurveId :#and not checkCollide(listePtCurve,v[newPtId]):
            #check collision with previous
            #angle,axis = helper.getAngleAxis(v[newPtId],lastPoint)
            #if angle < math.radians(20.0):#check collision with previous
            listePtCurve.append(v[newPtId].tolist())
            listePtCurveId.append(newPtId)
            mask_visisted[newPtId]=0
            totalLength+=distance
            #
        helper.progressBar(progress=len(listePtCurve)/len(v),label=str(len(listePtCurve))+" "+str(totalLength))        
        if len(listePtCurve) == len(v) or len(remaining_point) == 0:
            done = True
        if limit!=0 and totalLength >= limit:
            done = True
        counter+=1
        #print vi,len(listId),len(listePtCurve),counter
        if counter >= counterCut:
            #start a new curve ?
            done = True
            early = True 
    remaining_point = numpy.nonzero(mask_visisted)[0]                         
    return listePtCurve,early,numpy.take(v,remaining_point,0)   

def walkSphere(ref,faces,v,n,limit=0,nb=0,radius=5.0,u=20.0):
    #limit is the size limit of the spline
    #n is the number of desired spline            
    #progress bar
    totalLength=0
    nbCurve=0
    data = numpy.array(v)
    mask_visisted = numpy.ones(len(v))
    mask_indice = numpy.array(range(len(v)))
    listePtCurveId=[]
    listePtCurve=[]
    curves=[]
    newPtId = 0
    uL=u
    mask_visisted[0]=0
    done = False
    counter=0
    counterCut=1000
    early = False
    helper.resetProgressBar()
    center = helper.getCenter(v)
    prev = center[:]#v[newPtId]
    marge = 90.0
    while not done :
        #get closest point in remaining point
        remaining_point = numpy.nonzero(mask_visisted)[0]
        if len(remaining_point) == 0 :
            done = True
            break
        #pick next point ?
        ps=helper.randpoint_onsphere(uL)
        pt = [0,0,0]
        for i in range(3):
            pt[i]=prev[i]+ps[i]
        #print (pt)
        intersect,count = helper.raycast(ref,pt,center,10000,count=True)
        #print (pt)
        r = ((count%2) == 1)
        if r :
            doit=True
            if len(listePtCurve) >= 2 :
                angle = helper.angle_between_vectors(numpy.array(listePtCurve[-1])-numpy.array(listePtCurve[-2]),ps)
                doit = abs(math.degrees(angle)) <= marge
            #if not checkCollide(listePtCurve,pt):
            if not checkIntersect(numpy.array(listePtCurve),numpy.array(pt),radius=radius,u=uL) and doit :
                listePtCurve.append(pt)
                totalLength+=uL
                prev = pt
                counter = 0
        helper.progressBar(progress=totalLength/limit,label=str(len(listePtCurve))+" "+str(totalLength))        
        if limit!=0 and totalLength >= limit:
            done = True
        counter+=1
        #print vi,len(listId),len(listePtCurve),counter
        if counter >= counterCut:
            #start a new curve ?
            done = True
            early = True 
    print totalLength
    return listePtCurve,early   
    
    
#def main():
if __name__=="__main__":
    #mode = "cv" # mode in ["v","f","rv","rf","cv",""cf]
    #dicfunc = {"v":getv,"f":getf,"rv":getrv,"rf":getrf,"cv":getcv}
    o=helper.getCurrentSelection()[0]#getObject("Sphere")
    #currentSlection
    faces,v,n = helper.DecomposeMesh(o,
            edit=False,copy=False,tri=True,transform=True)
    #mask = numpy.ones(len(v),int)
    snake = helper.getObject("test")
    print snake 
    #c4d.v=v
    if snake is None :
        c=walkSphere(o,faces,v,n,limit=32170*2,nb=2,radius=5.0,u=15.0)#32170*2
        snake=helper.spline("test0", c[0],close=0,type=1,
                           scene=None)#,parent="snake1")[0]
        #listePtCurve,early=getcv(faces,v,n,range(len(v)))
        #c,early,rv=growAtsurface(faces,v,n,limit=32170,nb=2)
        #snake=helper.spline("test1", c,close=0,type=1,
        #                   scene=None,parent="snake1")[0]#,parent="snake")[0]
        #c,early,rv=growAtsurface(faces,rv,n,limit=32170,nb=2)
        #snake=helper.spline("test2", c,close=0,type=1,
        #                   scene=None,parent="snake2")[0]#,parent="snake")[0]
                           
#execfile("/Users/ludo/DEV/autofill_svn/trunk/AutoFillClean/curvePacking.py")