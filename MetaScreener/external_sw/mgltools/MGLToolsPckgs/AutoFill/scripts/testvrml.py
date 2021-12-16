from DejaVu.IndexedPolygons import IndexedPolygons

def importMesh_IndexedFaceSet(geom, gipname, bpyima, ancestry):
    # print geom.lineno, geom.id, vrmlNode.DEF_NAMESPACE.keys()

    ccw = geom.getFieldAsBool('ccw', True, ancestry)
    ifs_colorPerVertex = geom.getFieldAsBool('colorPerVertex', True, ancestry) # per vertex or per face
    ifs_normalPerVertex = geom.getFieldAsBool('normalPerVertex', True, ancestry)

    # This is odd how point is inside Coordinate

    # VRML not x3d
    #coord = geom.getChildByName('coord') # 'Coordinate'

    coord = geom.getChildBySpec('Coordinate') # works for x3d and vrml

    #if coord:
    #    ifs_points = coord.getFieldAsArray('point', 3, ancestry)
    #else:
    #    coord = []

    if not coord:
        print '\tWarnint: IndexedFaceSet has no points'
        return None, ccw

    ifs_faces = geom.getFieldAsArray('coordIndex', 0, ancestry)

    faces = []
    face = [0]
    for fi in ifs_faces[1:]:
        if fi==-1:
            if len(face)==3:
                face.reverse()
                faces.append(face)
            elif len(face)>3:
                for j in range(1, len(face)-1):
                    faces.append( [face[0], face[j+1], face[j]] )
            face = []
        else:
            face.append(fi)

    ipgeom = IndexedPolygons(gipname, vertices=coord.getFieldAsArray('point', 3, ancestry),
                          faces=faces)

##     coords_tex = None
##     if ifs_faces: # In rare cases this causes problems - no faces but UVs???

##         # WORKS - VRML ONLY
##         # coords_tex = geom.getChildByName('texCoord')
##         coords_tex = geom.getChildBySpec('TextureCoordinate')

##         if coords_tex:
##             ifs_texpoints = coords_tex.getFieldAsArray('point', 2, ancestry)
##             ifs_texfaces = geom.getFieldAsArray('texCoordIndex', 0, ancestry)

##             if not ifs_texpoints:
##                 # IF we have no coords, then dont bother
##                 coords_tex = None


    # WORKS - VRML ONLY
    # vcolor = geom.getChildByName('color')
    vcolor = geom.getChildBySpec('Color')
    vcolor_spot = None # spot color when we dont have an array of colors
    if vcolor:
        # float to char
        ifs_vcol = [(0,0,0)] # EEKADOODLE - vertex start at 1
        ifs_vcol.extend([[int(c*256) for c in col] for col in vcolor.getFieldAsArray('color', 3, ancestry)])
        ifs_color_index = geom.getFieldAsArray('colorIndex', 0, ancestry)

        if not ifs_vcol:
            vcolor_spot = [int(c*256) for c in vcolor.getFieldAsFloatTuple('color', [], ancestry)]

    # Convert faces into somthing blender can use
    edges = []

    # All lists are aligned!
    faces = []
    faces_uv = [] # if ifs_texfaces is empty then the faces_uv will match faces exactly.
    faces_orig_index = [] # for ngons, we need to know our original index

## ##     if coords_tex and ifs_texfaces:
## ##         do_uvmap = True
## ##     else:
## ##         do_uvmap = False

    # current_face = [0] # pointer anyone

##     def add_face(face, fuvs, orig_index):
##         l = len(face)
##         if l==3 or l==4:
##             faces.append(face)
##             # faces_orig_index.append(current_face[0])
##             if do_uvmap:
##                 faces_uv.append(fuvs)

##             faces_orig_index.append(orig_index)
##         elif l==2:
##             edges.append(face)
##         elif l>4:
##             for i in xrange(2, len(face)):
##                 faces.append([face[0], face[i-1], face[i]])
##                 if do_uvmap:
##                     faces_uv.append([fuvs[0], fuvs[i-1], fuvs[i]])
##                 faces_orig_index.append(orig_index)
##         else:
##             # faces with 1 verts? pfft!
##             # still will affect index ordering
##             pass

##     face = []
##     fuvs = []
##     orig_index = 0
##     for i, fi in enumerate(ifs_faces):
##         # ifs_texfaces and ifs_faces should be aligned
##         if fi != -1:
##             # face.append(int(fi)) # in rare cases this is a float
##             # EEKADOODLE!!!
##             # Annoyance where faces that have a zero index vert get rotated. This will then mess up UVs and VColors
##             face.append(int(fi)+1) # in rare cases this is a float, +1 because of stupid EEKADOODLE :/

##             if do_uvmap:
##                 if i >= len(ifs_texfaces):
##                     print '\tWarning: UV Texface index out of range'
##                     fuvs.append(ifs_texfaces[0])
##                 else:
##                     fuvs.append(ifs_texfaces[i])
##         else:
##             add_face(face, fuvs, orig_index)
##             face = []
##             if do_uvmap:
##                 fuvs = []
##             orig_index += 1

##     add_face(face, fuvs, orig_index)
##     del add_face # dont need this func anymore

##     bpymesh = bpy.data.meshes.new()

##     bpymesh.verts.extend([(0,0,0)]) # EEKADOODLE
##     bpymesh.verts.extend(ifs_points)

##     # print len(ifs_points), faces, edges, ngons

##     try:
##             bpymesh.faces.extend(faces, smooth=True, ignoreDups=True)
##     except KeyError:
##             print "one or more vert indicies out of range. corrupt file?"
##             #for f in faces:
##             #	bpymesh.faces.extend(faces, smooth=True)

##     bpymesh.calcNormals()

##     if len(bpymesh.faces) != len(faces):
##         print '\tWarning: adding faces did not work! file is invalid, not adding UVs or vcolors'
##         return bpymesh, ccw

##     # Apply UVs if we have them
##     if not do_uvmap:
##         faces_uv = faces # fallback, we didnt need a uvmap in the first place, fallback to the face/vert mapping.
##     if coords_tex:
##         #print ifs_texpoints
##         # print geom
##         bpymesh.faceUV = True
##         for i,f in enumerate(bpymesh.faces):
##             f.image = bpyima
##             fuv = faces_uv[i] # uv indicies
##             for j,uv in enumerate(f.uv):
##                 # print fuv, j, len(ifs_texpoints)
##                 try:
##                     uv[:] = ifs_texpoints[fuv[j]]
##                 except:
##                     print '\tWarning: UV Index out of range'
##                     uv[:] = ifs_texpoints[0]

##     elif bpyima and len(bpymesh.faces):
##             # Oh Bugger! - we cant really use blenders ORCO for for texture space since texspace dosnt rotate.
##             # we have to create VRML's coords as UVs instead.

##             # VRML docs
##             '''
##             If the texCoord field is NULL, a default texture coordinate mapping is calculated using the local
##             coordinate system bounding box of the shape. The longest dimension of the bounding box defines the S coordinates,
##             and the next longest defines the T coordinates. If two or all three dimensions of the bounding box are equal,
##             ties shall be broken by choosing the X, Y, or Z dimension in that order of preference.
##             The value of the S coordinate ranges from 0 to 1, from one end of the bounding box to the other.
##             The T coordinate ranges between 0 and the ratio of the second greatest dimension of the bounding box to the greatest dimension.
##             '''

##             # Note, S,T == U,V
##             # U gets longest, V gets second longest
##             xmin, ymin, zmin = ifs_points[0]
##             xmax, ymax, zmax = ifs_points[0]
##             for co in ifs_points:
##                     x,y,z = co
##                     if x < xmin: xmin = x
##                     if y < ymin: ymin = y
##                     if z < zmin: zmin = z

##                     if x > xmax: xmax = x
##                     if y > ymax: ymax = y
##                     if z > zmax: zmax = z

##             xlen = xmax - xmin
##             ylen = ymax - ymin
##             zlen = zmax - zmin

##             depth_min = xmin, ymin, zmin
##             depth_list = [xlen, ylen, zlen]
##             depth_sort = depth_list[:]
##             depth_sort.sort()

##             depth_idx = [depth_list.index(val) for val in depth_sort]

##             axis_u = depth_idx[-1]
##             axis_v = depth_idx[-2] # second longest

##             # Hack, swap these !!! TODO - Why swap??? - it seems to work correctly but should not.
##             # axis_u,axis_v = axis_v,axis_u

##             min_u = depth_min[axis_u]
##             min_v = depth_min[axis_v]
##             depth_u = depth_list[axis_u]
##             depth_v = depth_list[axis_v]

##             depth_list[axis_u]

##             if axis_u == axis_v:
##                     # This should be safe because when 2 axies have the same length, the lower index will be used.
##                     axis_v += 1

##             bpymesh.faceUV = True

##             # HACK !!! - seems to be compatible with Cosmo though.
##             depth_v = depth_u = max(depth_v, depth_u)

##             for f in bpymesh.faces:
##                     f.image = bpyima
##                     fuv = f.uv

##                     for i,v in enumerate(f):
##                             co = v.co
##                             fuv[i][:] = (co[axis_u]-min_u) / depth_u, (co[axis_v]-min_v) / depth_v

    # Add vcote 
    if vcolor:
        # print ifs_vcol
        bpymesh.vertexColors = True

        for f in bpymesh.faces:
            fcol = f.col
            if ifs_colorPerVertex:
                fv = f.verts
                for i,c in enumerate(fcol):
                    color_index = fv[i].index # color index is vert index
                    if ifs_color_index:
                        try:
                            color_index = ifs_color_index[color_index]
                        except:
                            print '\tWarning: per vertex color index out of range'
                            continue

                    if color_index < len(ifs_vcol):
                        c.r, c.g, c.b = ifs_vcol[color_index]
                    else:
                        #print '\tWarning: per face color index out of range'
                        pass
            else:
                if vcolor_spot: # use 1 color, when ifs_vcol is []
                    for c in fcol:
                        c.r, c.g, c.b = vcolor_spot
                else:
                    color_index = faces_orig_index[f.index] # color index is face index
                    #print color_index, ifs_color_index
                    if ifs_color_index:
                        if color_index <= len(ifs_color_index):
                            print '\tWarning: per face color index out of range'
                            color_index = 0
                        else:
                            color_index = ifs_color_index[color_index]


                    col = ifs_vcol[color_index]
                    for i,c in enumerate(fcol):
                        try:
                            c.r, c.g, c.b = col
                        except:
                            pass # incase its not between 0 and 255

##     bpymesh.verts.delete([0,]) # EEKADOODLE

    return ipgeom, ccw


def importShape(node, ancestry, num):
    vrmlname = node.getDefName()
    if not vrmlname: vrmlname = 'Shape'+str(num)

    # works 100% in vrml, but not x3d
    #appr = node.getChildByName('appearance') # , 'Appearance'
    #geom = node.getChildByName('geometry') # , 'IndexedFaceSet'

    # Works in vrml and x3d
    appr = node.getChildBySpec('Appearance')
    geom = node.getChildBySpec(['IndexedFaceSet', 'IndexedLineSet', 'PointSet', 'Sphere', 'Box', 'Cylinder', 'Cone'])

    # For now only import IndexedFaceSet's
    if geom:
        bpymat = None
        bpyima = None
        texmtx = None

        depth = 0 # so we can set alpha face flag later

        if appr:

            #mat = appr.getChildByName('material') # 'Material'
            #ima = appr.getChildByName('texture') # , 'ImageTexture'
            #if ima and ima.getSpec() != 'ImageTexture':
            #	print '\tWarning: texture type "%s" is not supported' % ima.getSpec() 
            #	ima = None
            # textx = appr.getChildByName('textureTransform')

            mat = appr.getChildBySpec('Material')
            ima = appr.getChildBySpec('ImageTexture')

            textx = appr.getChildBySpec('TextureTransform')

            if textx:
                texmtx = translateTexTransform(textx, ancestry)



            # print mat, ima
            if mat or ima:

                if not mat:
                    mat = ima # This is a bit dumb, but just means we use default values for all

##                 # all values between 0.0 and 1.0, defaults from VRML docs
##                 bpymat = bpy.data.materials.new()
##                 bpymat.amb =		mat.getFieldAsFloat('ambientIntensity', 0.2, ancestry)
##                 bpymat.rgbCol =		mat.getFieldAsFloatTuple('diffuseColor', [0.8, 0.8, 0.8], ancestry)

##                 # NOTE - blender dosnt support emmisive color
##                 # Store in mirror color and approximate with emit.
##                 emit =				mat.getFieldAsFloatTuple('emissiveColor', [0.0, 0.0, 0.0], ancestry)
##                 bpymat.mirCol =		emit
##                 bpymat.emit = 		(emit[0]+emit[1]+emit[2])/3.0

##                 bpymat.hard =		int(1+(510*mat.getFieldAsFloat('shininess', 0.2, ancestry))) # 0-1 -> 1-511
##                 bpymat.specCol =	mat.getFieldAsFloatTuple('specularColor', [0.0, 0.0, 0.0], ancestry)
##                 bpymat.alpha =		1.0 - mat.getFieldAsFloat('transparency', 0.0, ancestry)
##                 if bpymat.alpha < 0.999:
##                     bpymat.mode |= Material.Modes.ZTRANSP

##             if ima:

##                 ima_url = ima.getFieldAsString('url', None, ancestry)

##                 if ima_url==None:
##                     try:
##                         ima_url = ima.getFieldAsStringArray('url', ancestry)[0] # in some cases we get a list of images.
##                     except:
##                         ima_url = None

##                 if ima_url==None:
##                     print "\twarning, image with no URL, this is odd"
##                 else:
##                     bpyima= BPyImage.comprehensiveImageLoad(ima_url, dirName(node.getFilename()), PLACE_HOLDER= False, RECURSIVE= False, CONVERT_CALLBACK= imageConvertCompat)
##                     if bpyima:
##                         texture= bpy.data.textures.new()
##                         texture.setType('Image')
##                         texture.image = bpyima

##                         # Adds textures for materials (rendering)
##                         try:	depth = bpyima.depth
##                         except:	depth = -1

##                         if depth == 32:
##                             # Image has alpha
##                             bpymat.setTexture(0, texture, Texture.TexCo.UV, Texture.MapTo.COL | Texture.MapTo.ALPHA)
##                             texture.setImageFlags('MipMap', 'InterPol', 'UseAlpha')
##                             bpymat.mode |= Material.Modes.ZTRANSP
##                             bpymat.alpha = 0.0
##                         else:
##                             bpymat.setTexture(0, texture, Texture.TexCo.UV, Texture.MapTo.COL)

##                         ima_repS = ima.getFieldAsBool('repeatS', True, ancestry)
##                         ima_repT = ima.getFieldAsBool('repeatT', True, ancestry)

##                         # To make this work properly we'd need to scale the UV's too, better to ignore th
##                         # texture.repeat =	max(1, ima_repS * 512), max(1, ima_repT * 512)

##                         if not ima_repS: bpyima.clampX = True
##                         if not ima_repT: bpyima.clampY = True

        bpydata = None
        geom_spec = geom.getSpec()
        ccw = True
        if geom_spec == 'IndexedFaceSet':
            ipgeom, ccw = importMesh_IndexedFaceSet(geom, vrmlname, bpyima, ancestry)
##         elif geom_spec == 'IndexedLineSet':
##             bpydata = importMesh_IndexedLineSet(geom, ancestry)
##         elif geom_spec == 'PointSet':
##             bpydata = importMesh_PointSet(geom, ancestry)
##         elif geom_spec == 'Sphere':
##             bpydata = importMesh_Sphere(geom, ancestry)
##         elif geom_spec == 'Box':
##             bpydata = importMesh_Box(geom, ancestry)
##         elif geom_spec == 'Cylinder':
##             bpydata = importMesh_Cylinder(geom, ancestry)
##         elif geom_spec == 'Cone':
##             bpydata = importMesh_Cone(geom, ancestry)
        else:
            print '\tWarning: unsupported type "%s"' % geom_spec
            return

##         if bpydata:
##                 vrmlname = vrmlname + geom_spec

##                 bpydata.name = vrmlname

##                 bpyob  = node.blendObject = bpy.data.scenes.active.objects.new(bpydata)

##                 if type(bpydata) == Types.MeshType:
##                         is_solid =			geom.getFieldAsBool('solid', True, ancestry)
##                         creaseAngle =		geom.getFieldAsFloat('creaseAngle', None, ancestry)

##                         if creaseAngle != None:
##                                 bpydata.maxSmoothAngle = 1+int(min(79, creaseAngle * RAD_TO_DEG))
##                                 bpydata.mode |= Mesh.Modes.AUTOSMOOTH

##                         # Only ever 1 material per shape
##                         if bpymat:	bpydata.materials = [bpymat]

##                         if bpydata.faceUV:

##                                 if depth==32: # set the faces alpha flag?
##                                         transp = Mesh.FaceTranspModes.ALPHA
##                                         for f in bpydata.faces:
##                                                 f.transp = transp

##                                 if texmtx:
##                                         # Apply texture transform?
##                                         uv_copy = Vector()
##                                         for f in bpydata.faces:
##                                                 for uv in f.uv:
##                                                         uv_copy.x = uv.x
##                                                         uv_copy.y = uv.y

##                                                         uv.x, uv.y = (uv_copy * texmtx)[0:2]
##                         # Done transforming the texture


##                         # Must be here and not in IndexedFaceSet because it needs an object for the flip func. Messy :/
##                         if not ccw: bpydata.flipNormals()


##                 # else could be a curve for example



##                 # Can transform data or object, better the object so we can instance the data
##                 #bpymesh.transform(getFinalMatrix(node))
##                     bpyob.setMatrix( getFinalMatrix(node, None, ancestry) )

        return ipgeom

    
def translateRotation(rot):
    '''	axis, angle	'''
    return RotationMatrix(rot[3]*RAD_TO_DEG, 4, 'r', Vector(rot[:3]))

def translateScale(sca):
	mat = Matrix() # 4x4 default
	mat[0][0] = sca[0]
	mat[1][1] = sca[1]
	mat[2][2] = sca[2]
	return mat

def translateTexTransform(node, ancestry):
    cent = node.getFieldAsFloatTuple('center', None, ancestry) # (0.0, 0.0)
    rot = node.getFieldAsFloat('rotation', None, ancestry) # 0.0
    sca = node.getFieldAsFloatTuple('scale', None, ancestry) # (1.0, 1.0)
    tx =  node.getFieldAsFloatTuple('translation', None, ancestry) # (0.0, 0.0)
	
	
    if cent:
        # cent is at a corner by default
        cent_mat = TranslationMatrix(Vector(cent).resize3D()).resize4x4()
        cent_imat = cent_mat.copy().invert()
    else:
        cent_mat = cent_imat = None
	
    if rot:
        rot_mat = RotationMatrix(rot*RAD_TO_DEG, 4, 'z') # translateRotation(rot)
    else:
        rot_mat = None
	
    if sca:
        sca_mat = translateScale((sca[0], sca[1], 0.0))
    else:
        sca_mat = None
	
    if tx:
        tx_mat = TranslationMatrix(Vector(tx).resize3D()).resize4x4()
    else:
        tx_mat = None
	
    new_mat = Matrix()
	
    # as specified in VRML97 docs
    mats = [cent_imat, sca_mat, rot_mat, cent_mat, tx_mat]

    for mtx in mats:
        if mtx:
            new_mat = mtx * new_mat
	
    return new_mat


def getFinalMatrix(node, mtx, ancestry):
	
    transform_nodes = [node_tx for node_tx in ancestry if node_tx.getSpec() == 'Transform']
    if node.getSpec()=='Transform':
        transform_nodes.append(node)
    transform_nodes.reverse()
	
    if mtx==None:
        mtx = Matrix()
	
    for node_tx in transform_nodes:
        mat = translateTransform(node_tx, ancestry)
        mtx = mtx * mat
	
    return mtx


def importTransform(node, ancestry):
    return
    name = node.getDefName()
    if not name:
        name = 'Transform'
	
    #bpyob = node.blendObject = bpy.data.scenes.active.objects.new('Empty', name) # , name)
    #bpyob.setMatrix( getFinalMatrix(node, None, ancestry) )
    getFinalMatrix(node, None, ancestry)

    # so they are not too annoying
    #bpyob.emptyShape= Blender.Object.EmptyShapes.AXES
    #bpyob.drawSize= 0.2


PREF_FLAT=False
PREF_CIRCLE_DIV=16
HELPER_FUNC = None

from import_web3d import vrml_parse #load_web3d

print 'parsing'
#root_node, msg = vrml_parse('./NoskeCell3simple1.wrl')
#root_node, msg = vrml_parse('MockOrganelles/TwoMockOrganellesCut1.wrl')
root_node, msg = vrml_parse('MockOrganelles/TwoMockOrganellesUnCut1.wrl')
#root_node, msg = vrml_parse('MockOrganelles/MultipleMockOrganelles1.wrl')
print 'done'

print msg

all_nodes = root_node.getSerialized([], [])
geoms = []

for node, ancestry in all_nodes:
    spec = node.getSpec()
    #'''
    #prefix = node.getPrefix()
    #if prefix=='PROTO':
    #    pass
    #else
    #'''
    #if HELPER_FUNC and HELPER_FUNC(node, ancestry):
    #    # Note, include this function so the VRML/X3D importer can be extended
    #    # by an external script. - gets first pick 
    #                pass
    if spec=='Shape':
        geom = importShape(node, ancestry, len(geoms))
        geoms.append(geom)
        
    elif spec in ('PointLight', 'DirectionalLight', 'SpotLight'):
        importLamp(node, spec, ancestry)

    elif spec=='Viewpoint':
        importViewpoint(node, ancestry)

    elif spec=='Transform':
            # Only use transform nodes when we are not importing a flat object hierarchy
            if PREF_FLAT==False:
                    importTransform(node, ancestry)
            '''
    # These are delt with later within importRoute
    elif spec=='PositionInterpolator':
            ipo = bpy.data.ipos.new('web3d_ipo', 'Object')
            translatePositionInterpolator(node, ipo)
            '''
    else:
        print spec
        


##     # After we import all nodes, route events - anim paths
##     for node, ancestry in all_nodes:
##             importRoute(node, ancestry)

##     for node, ancestry in all_nodes:
##             if node.isRoot():
##                     # we know that all nodes referenced from will be in 
##                     # routeIpoDict so no need to run node.getDefDict() for every node.
##                     routeIpoDict = node.getRouteIpoDict()
##                     defDict = node.getDefDict()

##                     for key, ipo in routeIpoDict.iteritems():

##                             # Assign anim curves
##                             node = defDict[key]
##                             if node.blendObject==None: # Add an object if we need one for animation
##                                     node.blendObject = bpy.data.scenes.active.objects.new('Empty', 'AnimOb') # , name)

##                             node.blendObject.setIpo(ipo)



##     # Add in hierarchy
##     if PREF_FLAT==False:
##             child_dict = {}
##             for node, ancestry in all_nodes:
##                     if node.blendObject:
##                             blendObject = None

##                             # Get the last parent
##                             i = len(ancestry)
##                             while i:
##                                     i-=1
##                                     blendObject = ancestry[i].blendObject
##                                     if blendObject:
##                                             break

##                             if blendObject:
##                                     # Parent Slow, - 1 liner but works
##                                     # blendObject.makeParent([node.blendObject], 0, 1)

##                                     # Parent FAST
##                                     try:	child_dict[blendObject].append(node.blendObject)
##                                     except:	child_dict[blendObject] = [node.blendObject]

##             # Parent FAST
##             for parent, children in child_dict.iteritems():
##                     parent.makeParent(children, 0, 1)

##             # update deps
##             bpy.data.scenes.active.update(1)
##             del child_dict

from DejaVu import Viewer
vi = Viewer()
for g in geoms:
    vi.AddObject(g)

#geoms[0].writeToFile('SphOrganelle')
#geoms[1].writeToFile('TubeOrganelle')
