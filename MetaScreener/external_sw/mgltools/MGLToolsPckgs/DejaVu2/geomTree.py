import Tkinter
from mglutil.gui.BasicWidgets.Tk.trees.tree import IconsManager
from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
     ColumnDescriptor ,TreeWithButtons, NodeWithButtons

from DejaVu2.Geom import Geom
from DejaVu2.IndexedPolygons import IndexedPolygons
from DejaVu2.IndexedPolylines import IndexedPolylines
from DejaVu2.Polylines import Polylines
from DejaVu2.Spheres import Spheres
from DejaVu2.Cylinders import Cylinders
from DejaVu2.glfLabels import GlfLabels

class DejaVu2GeomTreeWithButtons(TreeWithButtons):
    """
    Class to display a tree for DejaVu2 geoemtry.
    """

    def __init__(self, master, root, iconsManager=None,
                 idleRedraw=True, nodeHeight=18, headerHeight=30,
                 treeWidth=150, **kw):
        # add a compound selector entry
        kw['iconsManager'] = iconsManager
        kw['idleRedraw'] = idleRedraw
        kw['nodeHeight'] = nodeHeight
        kw['headerHeight'] = headerHeight
        kw['treeWidth'] = treeWidth
        TreeWithButtons.__init__( *(self, master, root), **kw )

        canvas = self.canvas


class DejaVu2GeomNode(NodeWithButtons):
    """
    The first level of this tree is either a molecule or a container.
    The second level are geoemtry object. Columns are used to modify geoms
    """

    def getChildren(self):
        """
        return children for object associated with this node.
        By default we return object.children. Override this method to
        selectively show children
        """
        return self.children

    
    def getIcon(self):
        """
        return node's icons for DejaVu2 geometry objects 
        """
        iconsManager = self.tree().iconsManager
        object = self.object

        if isinstance(object, IndexedPolygons):
            icon = iconsManager.get("mesh16.png", self.tree().master)
        elif isinstance(object, IndexedPolylines) or \
                 isinstance(object, Polylines):
            icon = iconsManager.get("lines16.png", self.tree().master)
        elif isinstance(object, Spheres):
            icon = iconsManager.get("spheres16.png", self.tree().master)
        elif isinstance(object, Cylinders):
            icon = iconsManager.get("cyl16.png", self.tree().master)
        elif isinstance(object, GlfLabels):
            icon = iconsManager.get("labels16.png", self.tree().master)
        else: # isinstance(object, Geom):
            icon = iconsManager.get("geom16.png", self.tree().master)

        if icon:
            self.iconWidth = icon.width()
        else:
            self.iconWidth = 0
        return icon

if __name__ == '__main__':
    root = Tkinter.Toplevel()
    vi = self.GUI.VIEWER

    iconsManager = IconsManager(['Icons'], 'DejaVu2')

    rootnode = DejaVu2GeomNode(vi.rootObject, None)

    tree = DejaVu2GeomTreeWithButtons(root, rootnode, self, nodeHeight=18,
                                     iconsManager=iconsManager, headerHeight=0,
                                     treeWidth=180, selectionMode='multiple')
    tree.pack(side='bottom', expand=1, fill='both')
    rootnode.expand()
