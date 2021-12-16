#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/fileCmds.py,v 1.8 2014/07/12 02:04:42 sanner Exp $
#
# $Id: fileCmds.py,v 1.8 2014/07/12 02:04:42 sanner Exp $
#

from PmvApp.Pmv import MVCommand
from MolKit.molecule import MoleculeSet

import sys, os

class MoleculesReader(MVCommand):
    """Command to read molecules.
    filenames --- a list of molecule files,
    addToRecent --- if set to True, adds to the list of applivcation recent files;
    modelsAs --- can be either 'molecules' or 'conformations' (default-'molecules');
    group --- can be None, a MoleculeGroup instance or a name(string) of existing group, if specified , the molecules are added to the group.
    """

    def doit(self, filenames, addToRecent=True, modelsAs='molecules', group=None):

        mols = MoleculeSet([])
        app = self.app()
        for name in filenames:
            try:
                mols.extend(self.app().readMolecule(
                    name, modelsAs=modelsAs,
                    addToRecent=addToRecent, group=group))
                app._executionReport.addSuccess('read %s successfully'%name, obj=name)
                
            except:
                msg = 'Error while reading %s'%name
                app.errorMsg(sys.exc_info(), msg, obj=name)
        return mols
    

    def undoCmdAfter(self, result, *args, **kw):
        #this is called in VFCmd.afterDoit(). result is a returned value of the doit().
        # (in this case - a list of molecule objects)
        name = ""
        for mol in result:
            name += mol.name +','
        if not hasattr(self.app(), "deleteMolecules"):
            return
        return ([(self.app().deleteMolecules, (result,), {'undoable':0, 'cleanRedo':False, "redraw":True})],
                self.name+ " %s"%name[:-1])

                
    def checkArguments(self, filenames, addToRecent=True,
                       modelsAs='molecules', group=None):

        assert isinstance(filenames, (list, tuple))
        for name in filenames:
            assert isinstance(name, str), "File names have to be strings"
        assert addToRecent in [0,1,True, False]
        assert modelsAs in ['molecules', 'chains', 'conformations']
        args = (filenames,)
        if group is not None:
            from MolKit.molecule import MoleculeGroup
            assert isinstance (group ,(MoleculeGroup, str))
        kw = {'addToRecent':addToRecent, 'modelsAs':modelsAs, 'group':group}
        return args, kw


class ReadAny(MVCommand):
    """Reads Molecule or Python script pmv session, vision network or 3D grids \n
    Package : PmvApp \n
    Module  : fileCmds \n
    Class   : ReadAny \n
    Command : readAny \n
    Synopsis:\n
        None <- readAny([files])
    """        

    def doOneFile(self, file, addToRecent=True, modelsAs='molecules'):
        
        ext = os.path.splitext(file)[1].lower()
        if ext in ['.py','.rc']:
            if file.find('_pmvnet') > 0 or file.find('_net') > 0:
                vision = self.app().vision
                if hasattr(vision, 'loadCommand'):
                    vision = vision.loadCommand()
                vision.show()
                vision.ed.loadNetwork(file)
            else:
                self.app().source(file, log=0)
        elif ext == ".psf":
            # Load Pmv session file
            self.app().readFullSession(file)
        elif ext in ['.pdb', '.pdbqt', '.pqr', '.cif', '.mol2']:
            self.app().readMolecule(file, modelsAs=modelsAs,
                    addToRecent=addToRecent)
        else: # not a recognized format
            raise ValueError, "file %s is not a recognized format for %s"%(
                file, self.name)


    def doit(self, files, addToRecent=True, modelsAs='molecules'):
        for ff in files:
            try:
                self.doOneFile(ff, modelsAs=modelsAs, addToRecent=addToRecent)
            except:
                msg = 'Error while reading %s' %ff
                self.app().errorMsg(sys.exc_info(), msg, obj=ff)


    def checkArguments(self, files, addToRecent=True, modelsAs='molecules'):
        """
        files - list of filenames
        """
        for name in files:
            assert isinstance(name, str), "names in filenames should be strings %s"%repr(name)
        kw = {}
        assert addToRecent in [True, False, 1, 0]
        assert modelsAs in ['molecules', 'chains', 'conformations']
        kw['addToRecent'] =  addToRecent
        kw['modelsAs']=  modelsAs
        return (files,), kw


class ReadPmvSession(MVCommand):
    """Reads Full Pmv Session \n
    Package : PmvApp \n
    Module  : fileCmds \n
    Class   : ReadPmvSession \n
    Command : readPmvSession \n
    Synopsis:\n
        None <- readPmvSession(path)
    """        

    def doit(self, files):
        for name in files:
            try:
                self.app().readFullSession(name)
            except:
                msg = 'Error while reading %s'%name
                self.app().errorMsg(sys.exc_info(), msg, obj=file)
                    

    def checkArguments(self, files):
        if not isinstance(files, (list, tuple)):
            files = [files,]
        for file in files:
            assert isinstance(file, str)
        return (files,), {}
        

import urllib                   

class Fetch(MVCommand):
    """This command read a molecule from the web. /n
    Package : PmvApp /n
    Module  : fileCommands /n
    Class   : fetch /n
    Command : fetch /n
    Synopsis:\n
        mols <- fetch(pdbID=None, URL="Default") /n
    guiCallback:  /n
Opens InputForm with 3 EntryFields /n
        PDB ID: 4-character code (e.g. 1crn). /n
        Keyword: searched using RCSB.ORG search engine /n
        URL: should point to an existing molecule  /n
        (e.g http://mgltools.scripps.edu/documentation/tutorial/molecular-electrostatics/HIS.pdb) /n
        If Keyword contains a text it is searched first.  /n
        When URL field is not empty this URL is used instead of PDB ID to retrieve /n
        molecule. Mouse over PDB Cache Directory label to see the path, /n
        or click Clear button to remove all files from there.
    """
    
    baseURI = "http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=pdb&compression=NO&structureId="
    resultURI = "http://www.rcsb.org/pdb/results/results.do"
    
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    rcFolder = getResourceFolderWithVersion()
   
    forceIt = False #do we force the fetch even if in the pdbcache dir


    def  onAddCmdToApp(self):
        if not self.app().userpref.has_key('PDB Cache Storage (MB)'):
            self.app().userpref.add( 'PDB Cache Storage (MB)', 100, 
                                  validateFunc = None,
                                  callbackFunc = [],
                                  doc="""Maximum space allowed for File -> Read -> fetch From Web.""")        
        

    def pdb_keyword_search(self, keyword):
        """This function  RCSB PDB RESTful Web Service interface using structure descritption 
        See http://www.pdb.org/pdb/software/rest.do for more info"""
        if  keyword:
            keyword = keyword.replace(' ','%20')
            post_query = """<orgPdbQuery>

<queryType>org.pdb.query.simple.StructDescQuery</queryType>

<description>StructDescQuery: entity.pdbx_description.comparator=contains entity.pdbx_description.value=%s </description>

<entity.pdbx_description.comparator>contains</entity.pdbx_description.comparator>

<entity.pdbx_description.value>%s</entity.pdbx_description.value>

</orgPdbQuery>
"""%(keyword, keyword)
            f = urllib.urlopen("http://www.pdb.org/pdb/rest/search", post_query)
            pdbid_list = f.read().split()
            self.mol_ids=[]
            self.description_list=[] 
            
            for pdbid in pdbid_list: 
                 desc_url = "http://www.pdb.org/pdb/rest/describeMol?structureId="+pdbid
                 xml_out = urllib.urlopen(desc_url).read()
                 try:
                     description = xml_out.split('description="')[1].split('" />')[0]
                 except:
                     pass
                 self.description_list.append(description)
                 self.mol_ids.append(pdbid)


    def checkArguments(self, pdbID=None, URL="Default", force=False):
        kw = {}
        assert isinstance (URL, str)
        assert force in [False, True, 1, 0]
        return (pdbID,URL), {'force':force}


    def doit(self, pdbID=None, URL="Default", force=False):
        gz=False
        self.forceIt = force
        ext = ".pdb"
        URI = URL
        if not hasattr(self,'db'):
            self.db=""
        if pdbID == None and URL !="Default":
                URI = URL
                txt  = URL.split("/")[-1]
                pdbID = txt[:-4]
                ext =  txt[-4:]
        elif pdbID != None:
            if len(pdbID) > 4 or self.db != "":
                if pdbID[4:] == '.trpdb' or self.db == "Protein Data Bank of Transmembrane Proteins (TMPDB)":
                    #most are xml format just look if the 1t5t.trpdb.gz exist
                    URI = 'http://pdbtm.enzim.hu/data/database/'+pdbID[1:3]+'/'+pdbID[:4]+'.trpdb.gz'
                    pdbID = pdbID[:4]
                    gz=True
                    #print "URI:", URI, "ID:", pdbID
                elif pdbID[4:] == '.pdb' or self.db == "Protein Data Bank (PDB)" :
                    pdbID = pdbID[:4]
                    URI = self.baseURI + pdbID
                elif pdbID[4:] == '.opm' or self.db == "Orientations of Proteins in Membranes (OPM)" :
                    pdbID = pdbID[:4]
                    URI = 'http://opm.phar.umich.edu/pdb/'+pdbID[:4]+'.pdb'
                elif pdbID[4:] == '.cif' or self.db == "Crystallographic Information Framework (CIF)":
                    pdbID = pdbID[:4]
                    URI = 'http://www.rcsb.org/pdb/files/'+pdbID[:4]+'.cif'
                    ext = ".cif"
                elif pdbID[4:] == '.pqs' or self.db == "PQS":
                    pdbID = pdbID[:4]
                    URI ='ftp://ftp.ebi.ac.uk/pub/databases/msd/pqs/macmol/'+pdbID[:4]+'.mmol'   
                    ext = '.mmol'
            else : #==4 ?    
                URI = self.baseURI + pdbID
        #print self.name, "URI:", URI, "ID:", pdbID
        if pdbID:
            #pdbID
            if self.rcFolder is not None:
                dirnames = os.listdir(self.rcFolder)
            else:
                dirnames = []
            #checks in pdb cache before searching in rcsb.org.
            
            if "pdbcache" in dirnames:
                #forceit : even if in pdbcache use the web pdb file
                filenames = os.listdir(self.rcFolder+os.sep+'pdbcache')
                if pdbID+ext in filenames and not self.forceIt:
                    tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                    mols = self.app().readMolecule(tmpFileName)
                    if hasattr(self.app(), 'recentFiles'):
                        self.app().recentFiles.add(os.path.abspath(tmpFileName),
                                                'guiSafeLoadMolecule')
                    return mols
            try:
                #print "ok try urllib open", URI
                #but first check it ...
                import WebServices
                test = WebServices.checkURL(URI)
                if test:
                    fURL = urllib.urlopen(URI)
                else:
                    #self.app().warningMsg("%s: could not find %s, try another ID" % (self.name, pdbID))
                    #return None
                    raise RuntimeError("%s: could not find %s, try another ID" % (self.name, pdbID))
            except:
                msg = 'Error while fetching %s'%pdbID
                self.app().errorMsg(sys.exc_info(), msg, obj=pdbID)
                #return None
            #if URL != "Default" or fURL.headers['content-type'] =='application/download':
            if self.rcFolder is not None:
                    if "pdbcache" not in dirnames:
                        curdir = os.getcwd()
                        os.mkdir(self.rcFolder + os.sep +"pdbcache")
                    #check if gzipped file...
                    tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                    if gz :
                        tmpFileName = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext+'.gz'
                    tmpFile = open(tmpFileName,'w')
                    tmpFile.write(fURL.read())
                    tmpFile.close()
                    if gz :
                        #print "ok gunzip"
                        out = self.rcFolder + os.sep +"pdbcache"+os.sep+pdbID+ext
                        gunzip(tmpFileName, out)
                        tmpFileName = out
                    mols = self.app().readMolecule(tmpFileName)
                    if hasattr(self.app(), 'recentFiles'):
                        self.app().recentFiles.add(os.path.abspath(tmpFileName),
                                                'guiSafeLoadMolecule')
                    return mols
    
    

    def getPDBCachedir(self):
        from mglutil.util.packageFilePath import getResourceFolderWithVersion 
        rcFolder = getResourceFolderWithVersion()
        if rcFolder is not None \
          and os.path.exists(self.rcFolder+os.sep+'pdbcache'):
            dirname = self.rcFolder+os.sep+'pdbcache'
            return    dirname     
        else:
            return None

    def clearPDBCache(self):
        dirname =  self.getPDBCachedir()
        if dirname and os.path.exists(dirname):
                filenames = os.listdir(dirname)
                for f in filenames:
                    os.remove(dirname+os.sep+f)



    def checkCache(self, threshold = 1024*1024):
        size = self.getCacheSize()
        maxSize = self.app().userpref['PDB Cache Storage (MB)']['value']
        if size > maxSize:
            folder = self.getPDBCachedir()
            if not folder: return
            folder_size = 0
            for (path, dirs, files) in os.walk(folder):
              for file in files:
                filename = os.path.join(path, file)
                fileSize = os.path.getsize(filename)
                if fileSize > threshold:
                    os.remove(filename)
                else:
                    folder_size += os.path.getsize(filename)
            if (folder_size/(1024*1024.0)) > maxSize:
                self.checkCache(threshold = threshold/2.)
                
    def getCacheSize(self):
        # pick a folder you have ...
        folder = self.getPDBCachedir()
        if not folder: return
        folder_size = 0
        for (path, dirs, files) in os.walk(folder):
          for file in files:
            filename = os.path.join(path, file)
            folder_size += os.path.getsize(filename)
        
        return (folder_size/(1024*1024.0))
                       


class PDBWriter(MVCommand):
    """
    Command to write the given molecule or the given subset of atoms
    of one molecule as PDB file.
    \nPackage : PmvApp
    \nModule  : fileCommands
    \nClass   : PDBWriter 
    \nCommand : writePDB
    \nSynopsis:\n
        None <- writePDB( nodes, filename=None, sort=True,
                          pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
                          bondOrigin=('File', 'UserDefined'), ssOrigin=None, **kw)
    \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
        filename --- name of the PDB file (default=None). If None is given
                  The name of the molecule plus the .pdb extension will be used\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'MODRES', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
    """

    def __init__(self):
        MVCommand.__init__(self)

        
    def doit(self, nodes, filename, sort=True, transformed=True,
             pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
             bondOrigin=('File', 'UserDefined'), ssOrigin=None):
        
        if transformed:
            oldCoords = {}
            from MolKit.molecule import Atom
            molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
            for mol, atoms in zip(molecules, atomSets):
                coords = atoms.coords
                # save curent coords
                oldCoords[mol] = coords
                # set transformed coords:
                atoms.coords = self.app().getTransformedCoords(mol, coords)
        from MolKit.pdbWriter import PdbWriter
        writer = PdbWriter()
        try:
            writer.write(filename, nodes, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)
        except:
                msg = 'Error while writing %s'%filename
                self.app().errorMsg(sys.exc_info(), msg, obj=filename)
        if transformed:
            for mol, atoms in zip(molecules, atomSets):
                atoms.coords = oldCoords[mol]


    def checkArguments (self, nodes, filename, sort=True, transformed=True,
                 pdbRec=['ATOM', 'HETATM', 'MODRES', 'CONECT'],
                 bondOrigin=('File','UserDefined'), ssOrigin=None):
        """
        \nRequired Argument:\n
        nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n
        filename --- name of the PDB file\n
        sort --- Boolean flag to either sort or not the nodes before writing
                  the PDB file (default=True)\n
        pdbRec --- List of the PDB Record to save in the PDB file.
                  (default: ['ATOM', 'HETATM', 'MODRES', 'CONECT']\n
        bondOrigin --- string or list specifying the origin of the bonds to save
                    as CONECT records in the PDB file. Can be 'all' or a tuple\n

        ssOrigin --- Flag to specify the origin of the secondary structure
                    information to be saved in the HELIX, SHEET and TURN
                    record. Can either be None, File, PROSS or Stride.\n
        transformed --- transformed canbe True or False (default is True)
        """
        assert  isinstance(filename, str), "File names have to be strings"
        assert isinstance (pdbRec , (list, tuple))
        # ??? bondOrigin according to the doc string is a list, tuple or string
        #     how can it be 0 or 1 ???
        if bondOrigin == 0:
            bondOrigin = ('File', 'UserDefined')
        elif bondOrigin == 1:
            bondOrigin = 'all'
        ##
        assert isinstance(bondOrigin, (list, tuple, str))
        assert ssOrigin in [None, "File", "PROSS" , "Stride"]
        assert sort in (True, False, 0, 1)
        args = (nodes, filename)
        kw = {'sort':sort, 'bondOrigin':bondOrigin, 'pdbRec':pdbRec,
              'ssOrigin':ssOrigin, 'transformed':transformed}
        return args, kw




commandClassFromName = {
    'readMolecules' : [MoleculesReader, None],
    'writePDB':  [PDBWriter, None],
    'readAny': [ReadAny, None],
    'readPmvSession' : [ReadPmvSession, None],
    'fetch': [Fetch, None]
    }

    


def initModule(app):
    print "initModule", app
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        app.addCommand(cmdClass(), cmdName, None)
