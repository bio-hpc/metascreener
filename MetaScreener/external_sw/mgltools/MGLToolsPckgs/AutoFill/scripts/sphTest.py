from DejaVu import Viewer
vi = Viewer()

sphc = ([0,0,0], [0.,0,0], [0,0,0], [250,250,250], [-250,-250,-250])
sphr = [1.,125.,250., 50., 50,]
colors = [[1,0,0], [0,1,0], [0,0,1], [1,1,1], [1,1,1]]
from DejaVu.Spheres import Spheres
sphg = Spheres('sph', centers=sphc, radii=sphr, materials=colors,
               inheritMaterial=False)
vi.AddObject(sphg)

