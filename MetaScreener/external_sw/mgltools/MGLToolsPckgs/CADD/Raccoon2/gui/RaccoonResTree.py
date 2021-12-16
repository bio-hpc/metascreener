#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import TkTreectrl, os, Tkinter, Pmw
import tkMessageBox as tmb
import tkFileDialog as tfd
import CADD.Raccoon2.HelperFunctionsN3P as hf
import CADD.Raccoon2
import Tkinter as tk
from PIL import Image, ImageTk




class DictTreeCheckSelector:

    def __init__(self, master, history):
        
        self.master = master
        self.history = history
        self.initIcons()

        self.results = []
        self.checkedItems = {}
        self.createTree()

    def initIcons(self):
        """ initialize the icons for the interface"""
        #icon_path = '/entropia/code/latest/MGLToolsPckgs/CADD/Raccoon2/gui/icons'
        icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'prj.png'
        self._ICON_prj = ImageTk.PhotoImage(Image.open(f))

        f = icon_path + os.sep + 'exp.png'
        self._ICON_exp = ImageTk.PhotoImage(Image.open(f))
        
        f = icon_path + os.sep + 'vs.png'
        self._ICON_vs = ImageTk.PhotoImage(Image.open(f))



    def createTree(self):
        self.win = Pmw.Dialog(self.master, title='Select downloaded results', buttons=('OK','Cancel'),
                command=self.close)
        #pathlabel = Tkinter.StringVar(value=hf.truncateName(self.RESULTS_LOCATION, 55))

        self.treeObj = TkTreectrl.ScrolledTreectrl(self.win.interior())
        self.treeObj.pack(expand=1,fill='both', padx=5,pady=3)
        self.tree = self.treeObj.treectrl
        #self.itemToName = { TkTreectrl.ROOT : self.history }
        #self.nameToItem = { self.history : TkTreectrl.ROOT }
        self._treeStyles = {}

        # checkbox 
        self.tree.state_define('Checked')
        
        self._checkedIcon = check = \
            Tkinter.PhotoImage(master=self.master,
            data=('R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39',
                   '////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53N',
                   'JVNpmryZqsYDnemT3BQA7'))
        self._unCheckedIcon = uncheck = \
            Tkinter.PhotoImage(master=self.master,
            data=('R0lGODlhDQANABEAACwAAAAADQANAI',
            'EAAAB/f3/f39////8CIYyPNgHtLxYYtNbIrMZTX+l9WThwZAmSppqGmADHcnRaBQA7'))

        el_image = self.tree.element_create(type='image', image=(
            check, 'Checked', uncheck, ()))
        self.checkboxStyle = styleCheckbox = self.tree.style_create()
        self.tree.style_elements(styleCheckbox, el_image)

        self.tree.style_layout(styleCheckbox, el_image, padx=9, pady=2)
        self.treecol = self.tree.column_create(text='Results')
        self.tree.configure(treecolumn=self.treecol, showbuttons=1) #, expand=1)

        self.checkcol = self.tree.column_create(text='Select', expand=0)

        self._prjIcon = prjIcon = self._ICON_prj
        self._expIcon = expIcon = self._ICON_exp
        #self.tree.column_create(text='results URL', expand=0)
        # style for project
        styleProject = self.tree.style_create()
        pel_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(prjIcon, TkTreectrl.OPEN, prjIcon, ''))

        pel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        pel_select = self.tree.element_create(type=TkTreectrl.RECT, showfocus=1,
                                     fill=('blue4', TkTreectrl.SELECTED))
        self.tree.style_elements(styleProject, pel_image, pel_select, pel_text)
        self.tree.style_layout(styleProject, pel_image, pady=1)
        self.tree.style_layout(styleProject, pel_select, union=(pel_text,), padx=1, pady=1, squeeze='')
        self.tree.style_layout(styleProject, pel_text, padx=1, pady=1, ipadx=2,ipady=2) #, squeeze='y')
        self._treeStyles['prj'] = { 'img' : pel_image, 'txt' : pel_text, 'style' : styleProject}

        # style for jobs
        styleJob = self.tree.style_create()
        job_image = self.tree.element_create(type=TkTreectrl.IMAGE,
                                    image=(expIcon, TkTreectrl.OPEN, expIcon, ''))
        self.tree.style_elements(styleJob, job_image, pel_select, pel_text)
        self.tree.style_layout(styleJob, pel_select, union=(pel_text,), padx=1, pady=1, ipadx=1,ipady=1 ) #, squeeze='y')
        self.tree.style_layout(styleJob, job_image, pady=2)
        self._treeStyles['job'] = { 'img' : job_image, 'txt' : pel_text, 'style' : styleJob}

        # style for string cell
        styleString = self.tree.style_create()
        cel_text = self.tree.element_create(type=TkTreectrl.TEXT,  fill=('white', TkTreectrl.SELECTED))
        self.tree.style_elements(styleString, pel_select, cel_text)
        self.tree.style_layout(styleString, cel_text, padx=1, pady=1, squeeze='y')
        self.tree.style_layout(styleString, pel_select, union=(cel_text,), padx=1, pady=1, ipadx=1,ipady=1 )

        self._treeStyles['cell'] = { 'txt' : cel_text, 'style' : styleString}

        # bindings
        self.tree.notify_bind('<Expand-before>', self.expand)
        self.tree.notify_generate('<Expand-before>', item=TkTreectrl.ROOT)
        self.tree.bind('<ButtonRelease-1>', self.on_button1)
        self.win.activate()


    def close(self, event=None):
        result = []
        if event == 'OK':
            for prj in self.tree.item_children(TkTreectrl.ROOT):
                result = self.traverseTree( prj, result)
            #for l in result:
            #    print l
        self.win.destroy()
        self.result = result

    def traverseTree(self, node, result):
        #
        if not node == TkTreectrl.ROOT:
            names = [self.tree.item_text(node, self.treecol)[0] ]
        state = self.tree.itemstate_forcolumn(node, self.checkcol)
        if not state == None:
            names = [self.tree.item_text(node, self.treecol)[0] ]
            for parent in self.tree.item_ancestors(node)[:-1]:
                names.append(self.tree.item_text(parent, self.treecol)[0] )
            names.reverse()
            result.append(names)
            return result
        else:
            for child in self.tree.item_children(node):
                result = self.traverseTree(child, result)

        return result
        


    def expand(self, event):
        print "EXPANDING"
        item = event.item
        if not self.tree.item_numchildren(item) == 0:
            return

        t = event.widget
        ancestors = t.item_ancestors(item)
        if ancestors:
            generation = len(ancestors)
        else:
            generation = 0
        # if generation < 3 and generation > 0:
        #    self.tree.item_config(item, button=True)


        prj  = self._treeStyles['prj']
        #cell = self._treeStyles['cell']
        job  = self._treeStyles['job']
        
        if generation < 2:
            txt = prj['txt']
            img = prj['img']
            style = prj['style']
        else:
            txt = job['txt']
            img = job['img']
            style = job['style']


        if generation == 0:
            obj = self.history
        else:
            names = [ self.tree.item_text(item, self.treecol)[0]]
            #print "ANCESTOR", t.item_ancestors(item)
            for parent in t.item_ancestors(item)[:-1]:
                names.append(self.tree.item_text(parent, self.treecol)[0] )
            names.reverse()
            #print "NAME1", names
            obj = self.history
            for name in names:
                #print "OBJ", obj
                obj = obj[name]

        state = t.itemstate_forcolumn(item, self.checkcol)

        for child in obj.keys():
            button = generation < 2
            new = self.tree.create_item(parent=item, button=button, open=0)[0]
            self.tree.itemstyle_set(new, self.treecol, style)
            self.tree.itemstyle_set(new, self.checkcol, self.checkboxStyle)
            self.tree.itemelement_config(new, self.treecol, txt, text=child)
            
            if state is not None:
                t.itemstate_forcolumn(new, self.checkcol,state)

    def on_button1(self, event):
        t = event.widget
        identify = t.identify(event.x, event.y)
        
        if identify:
            try:
                item, column, element = identify[1], identify[3], identify[5]
                if int(column)==1: # The value column was pressed
                    ## handle button click on check buttons in columns 1 (i.e. values)
                    t.itemstate_forcolumn(item, column, '~Checked')
                    state = t.itemstate_forcolumn(item, self.checkcol)
                    self.propagateCheckButtonDown( item, state)
                    if state == None: # if uncheck, uncheck all ancestors
                        for parent in t.item_ancestors(item):
                            t.itemstate_forcolumn(parent, 1, '!Checked')
                    return 'break'
            except IndexError:
                pass

    def propagateCheckButtonDown(self, item, state):
        # go down the tree and check all buttons
        for child in self.tree.item_children(item):
            if state == None:
                if child:    
                    self.tree.itemstate_forcolumn(child, 1, '!Checked')
            else:
                if child:
                    self.tree.itemstate_forcolumn(child, 1, 'Checked')
            self.propagateCheckButtonDown(child, state)




if __name__ == '__main__':
    root = Tkinter.Tk()
    history = { 'prj1': 
                    {'exp1': 
                        { 'vs1':  [1,2,3]}, 
                     'exp2':
                        {'vs1': [2,3,4], 
                         'vs2':[9,8,7]
                         }} } 

    x = DictTreeCheckSelector(root, history)
    
    root.mainloop()

