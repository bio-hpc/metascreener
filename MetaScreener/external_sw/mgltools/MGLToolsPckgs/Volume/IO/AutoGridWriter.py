import numpy
from Volume.Grid3D import Grid3D

class WriteAutoGrid:

    def write(self, grid, filename):
        """
        write a Grid3D as an AutoDockGrid
        """
        assert isinstance(grid, Grid3D)

        f = open(filename, 'w')

        ## write header
        ##
        name = grid.header.get('GRID_PARAMETER_FILE', '')
        f.write('GRID_PARAMETER_FILE %s\n'%name)
        name = grid.header.get('GRID_DATA_FILE', '')
        f.write('GRID_DATA_FILE %s\n'%name)
        name = grid.header.get('MACROMOLECULE', '')
        f.write('MACROMOLECULE %s\n'%name)
        spacing = grid.stepSize[0]
        f.write('SPACING %.3f\n'%spacing)
        nx, ny, nz = grid.dimensions
        f.write('NELEMENTS %d %d %d\n'%(nx-1, ny-1, nz-1))
        ox, oy, oz = grid.origin
        center = (ox+(nx/2)*spacing, oy+(ny/2)*spacing, oz+(nz/2)*spacing)
        f.write('CENTER %.3f %.3f %.3f\n'%center)

        ## write the data
        ##
        data = grid.data
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    f.write("%.3f\n"%data[i,j,k])

        f.close()
