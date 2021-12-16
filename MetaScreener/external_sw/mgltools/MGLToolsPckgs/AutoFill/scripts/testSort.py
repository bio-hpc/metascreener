def numeric_compare(x, y):
    c1 = x['completion']
    c2 = y['completion']
    if c1 > c2:
        return 1
    elif c1==c2:
       r1 = x['radius']
       r2 = y['radius']
       if r1 > r2:
          return 1
       elif r1 == r2:
          return 0
       else:
          return -1
    else:  #x < y
       return -1

a1 = {'completion':10, 'radius':15}
a2 = {'completion':10, 'radius':1}
a3 = {'completion':10, 'radius':8}
a4 = {'completion':3, 'radius':5}
a5 = {'completion':12, 'radius':100}
a = [a1,a2,a3,a4,a5]
a.sort(numeric_compare)
