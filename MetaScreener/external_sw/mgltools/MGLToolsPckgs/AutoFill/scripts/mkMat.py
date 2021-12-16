f = open('deg06.matrix')
data = f.readlines()
f.close()

f = open('deg06Rot.py', 'w')
f.write('import numpy\n')
f.write('allRtotations = numpy.array( [\n')
for line in data:
    f.write('[[%.6f,%.6f,%.6f,0.0],[%.6f,%.6f,%.6f,0.0],[%.6f,%.6f,%.6f,0.0],[0.0,0.0,0.0,1.0]],\n'%tuple(map(float, line.split())))
f.write("], 'f')\n")
f.close()
