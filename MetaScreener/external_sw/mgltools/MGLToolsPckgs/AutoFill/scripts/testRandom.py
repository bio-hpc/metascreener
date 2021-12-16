from random import uniform, seed
from math import abs

values = []
seed(10)

for i in range(10000):
    r1= uniform(-0.25,0.25)
    r2 = uniform(-0.25,0.25)
    r3 = uniform(-0.25,0.25)
    r4 = uniform(-0.25,0.25)
    values.append(abs(r1+r2+r3+r4))

