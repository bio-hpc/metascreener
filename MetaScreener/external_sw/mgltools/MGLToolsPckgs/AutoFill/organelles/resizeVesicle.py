import sys

if len(sys.argv)<4:
    print "Usage: python %s infile outfile scale"%sys.argv[0]
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
scale = float(sys.argv[3])

f = open(infile)
data = f.readlines()
f.close()

f = open(outfile, 'w')
for line in data:
    x,y,z,nx,ny,nz = map(float, line.split())
    f.write("%f %f %f %f %f %f\n"%(x*scale, y*scale, z*scale, nx,ny,nz))
f.close()
