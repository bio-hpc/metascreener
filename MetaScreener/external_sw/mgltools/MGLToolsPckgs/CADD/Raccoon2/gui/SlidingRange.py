#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli, Michel Sanner
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
import Tkinter, tkFont

from mglutil.util.callback import CallbackFunction

class RangeSlider(Tkinter.Frame):
    """
    - added method for setting the actual range values that can be returned by the slider
    - added getvalues method for getting current slider values
    - added min/max labels to the range
    - minor esthetic changes

    # TODO 
    - the widget is not tolearant with other non-pack placement managers? (i.e. grid?)
            remove the Tkinter packing configuration?

    """
    def __init__(self, master=None, width=100, height=15, vmin=0, vmax=100, cb=None,
                 canvasCfg={}):

        self.cb = cb
        self.vmin = vmin
        self.vmax = vmax
        self.currmin = self.vmin
        self.currmax = self.vmax

        family = 'Arial'
        #family = 'Helvetica'
        self.FONT = tkFont.Font(family=family,size=9)
        self.FONTbold = tkFont.Font(family=family,size=9,weight="bold")
        self.FONTsmall = tkFont.Font(family=family,size=height/2)
        self.BORDER = { 'bd':1,'highlightbackground':'black',
                    'borderwidth':2,'highlightcolor':'black','highlightthickness':1}

        self.minval = Tkinter.Label(master, text=self.vmin, anchor='e', width=8, padx=0, pady=0,
            font=self.FONTbold)
        self.minval.pack(side='left', anchor='w',padx=2)

        sett = self.BORDER.copy()
        sett['highlightbackground'] = 'gray40'

        Tkinter.Frame.__init__(self, master, **sett)
        Tkinter.Pack.config(self, side='left', anchor='w')

        self.maxval = Tkinter.Label(master, text=self.vmax, anchor='w', width=8, padx=0, pady=0,
            font=self.FONTbold)
        self.maxval.pack(side='left', anchor='w',padx=2)

        self.width = width
        self.height = height
        self.canvasCfg = canvasCfg
        self.orient = 'horizontal'
        self.createCanvas(master)


    def setrange(self, vmin=None, vmax=None):
        """ defines the value of the min and max allowed values"""
        #print "SLIDERSETRANGE>", vmin, vmax
        if not vmin == None:
            self.vmin = self.currmin = vmin
        if not vmax == None:
            self.vmax = self.currmax = vmax
        self.minval.configure(text="%2.3f" % self.vmin)
        self.maxval.configure(text="%2.3f" % self.vmax)
        self.reset()

    def reset(self, event=None):
        """ reset the sliders to the far edges"""
        canvas = self.canvas
        bb = canvas.bbox('left')
        if self.orient=='horizontal':
            canvas.move('left', self.leftOrigBB[0]-bb[0], 0)
        else:
            canvas.move('left', 0, bb[1]-self.leftOrigBB[1])

        bb = canvas.bbox('right')
        if self.orient=='horizontal':
            canvas.move('right', self.rightOrigBB[2]-bb[2], 0)
        else:
            canvas.move('right', 0, bb[3]-self.rightOrigBB[3])
        self.updateBackPoly(event)

##        c = self.canvas
##        bb1 = c.bbox('left')
##        bb2 = c.bbox('right')
##        print "BB1", bb1
##        print "BB2", bb2
##        print "\n\n\n\n ASK MICHEL!!!"
##        #self.canvas.move('left', 0, 0)
##        #self.canvas.move('right', 0, self.width) #-40, 0)
##

    def mouseDown(self, tag, event=None):
        if self.orient=='horizontal':
            self.lastx = event.x
        else:
            self.lastx = event.y


    def restrictHorizontalMotion(self, tag, dx):
        # tag wants to move by dx
        canvas = self.canvas
        bb1 = canvas.bbox('left')
        bb2 = canvas.bbox('right')        
        if tag=='left':
            if bb1[0]+dx <= 0:
                return -bb1[0]
            if bb1[2]+dx >= bb2[0]:
                return dx - (bb1[2]+dx-bb2[0])
            return dx
        if tag=='right':
            if bb2[2]+dx >= self.width+self.bw:
                return self.width - bb2[2] + self.bw
            if bb2[0]+dx <= bb1[2]:
                return dx - (bb2[0]+dx-bb1[2])
            return dx

        if tag=='left||right':
            if bb1[0]+dx <= self.bw:
                return -bb1[0]
            if bb2[2]+dx >= self.width + self.bw:
                return self.width-bb2[2] + self.bw
            return dx

        
    def restrictVerticalMotion(self, tag, dx):
        print 'NOT IMPLEMENTED'


    def mouseMove(self, tag, event=None):
        if tag=='poly':
            tag = "left||right"
        canvas = self.canvas
        if self.orient=='horizontal':
            dx = event.x - self.lastx
            self.lastx = event.x
            # make sure we keep in bounds
            dx1 = self.restrictHorizontalMotion(tag, dx)
            self.canvas.move(tag, dx1, 0)
            #print 'AAA', canvas.bbox(tag)
        else:
            dx = event.y - self.lastx
            self.lasty = event.y
            dx1 = self.restrictVerticalMotion(tag, dx)
            self.canvas.move(tag, 0, dx1)
        self.updateBackPoly()
        

    def mouseUp(self, tag, event=None):
        pass
    

    def createCanvas(self, master):
        height = self.height
        width = self.width

        cd={'width':width, 'height':height, 'relief':'sunken', 'borderwidth':0,
            'bg':'white'}
            #'bg':'grey70'}
        cd.update(self.canvasCfg)
        canvas = self.canvas = Tkinter.Canvas(self, **cd)
        self.canvas.configure(cursor='sb_h_double_arrow')

        self.bw = bw = cd['borderwidth']

        # create the background  polygon between the cursors
        # bb of poly is (0, 0, 200, 16)
        lp1 = canvas.create_rectangle( 1+bw, 1+bw, width+bw-1, height+bw,
                                       fill='SteelBlue1', outline='black',
                                       #fill='#0081FF', outline='black',
                                       tags=('poly',))

        # create left cursor (light upper left line)
        ## bb for 'leftl is (0,0,20,16)
        lc1 = canvas.create_line( 2+bw, height+bw-1, 2+bw, 2+bw, 18+bw, 2+bw,
                                  fill='white', width=1, tags=('left',))

        # create a polygon filling the cursor
        lp1 = canvas.create_rectangle( bw+3, bw+3, 17+bw, height+bw-2,
                                       fill='grey75', outline='grey75',
                                       tags=('left',), width=1)

        # create left cursor (dark lower rigth line)
        lc2 = canvas.create_line( 18+bw, 2+bw, 18+bw, height+bw-1, 2+bw, 
                                  height+bw-1, width=1, fill='black', tags=('left',))

        # create a letter in the cursor
        ll1 = canvas.create_text( bw+11, 1+bw+self.height/2, text=unicode(u"\u25B6"), font=self.FONTsmall, tags=('left',))
        self.leftOrigBB = canvas.bbox('left')
        
        # create right cursor (light upper left line)
        rc1 = canvas.create_line( 2+bw, height+bw-1, 2+bw, 2+bw, 18+bw, 2+bw,
                                  fill='white', tags=('right',))
        # create a polygon filling the cursor
        rp1 = canvas.create_rectangle( bw+3, bw+3, 17+bw, height+bw-2,
                                       fill='grey75', outline='grey75',
                                       tags=('right',))
        # create right cursor (dark lower rigth line)
        rc2 = canvas.create_line( 18+bw, 2+bw, 18+bw, height+bw-1, 2+bw,
                                  height+bw-1, fill='black', tags=('right',))
        # create a letter in the cursor
        rl1 = canvas.create_text( bw+11, bw+self.height/2, text=unicode(u"\u25C0"), font=self.FONTsmall, tags=('right',))
        self.canvas.move( 'right', width-20, 0)
        self.rightOrigBB = canvas.bbox('right')

        self.updateBackPoly()

        canvas.tag_bind('left', "<ButtonPress-1>",
                        CallbackFunction(self.mouseDown, 'left'))
        #canvas.tag_bind('left', "<ButtonRelease-1>",
        #                CallbackFunction( self.mouseUp, 'left'))
        canvas.tag_bind('left', "<B1-Motion>",
                        CallbackFunction( self.mouseMove, 'left'))

        canvas.tag_bind('right', "<ButtonPress-1>",
                        CallbackFunction( self.mouseDown, 'right'))
        #canvas.tag_bind('right', "<ButtonRelease-1>",
        #                CallbackFunction( self.mouseUp, 'right'))
        canvas.tag_bind('right', "<B1-Motion>",
                        CallbackFunction( self.mouseMove, 'right'))

        canvas.tag_bind('poly', "<ButtonPress-1>",
                        CallbackFunction( self.mouseDown, 'poly'))
        canvas.tag_bind('poly', "<B1-Motion>",
                        CallbackFunction( self.mouseMove, 'poly'))
        #canvas.tag_bind('poly', "<ButtonRelease-1>",
        #                CallbackFunction( self.mouseUp, 'poly'))

        self.canvas.pack(side=Tkinter.LEFT)


    def updateBackPoly(self, event=None):
        """update the background polygon to span betweent the cursors"""
        canvas = self.canvas
        bb1 = canvas.bbox('left')
        bb2 = canvas.bbox('right')
        canvas.coords('poly', bb1[2]+1, bb1[1]+1, bb2[0]-1, bb1[3]-1)
        self.currmin = self.vmin + (self.vmax - self.vmin) * self.pc(bb1[2])
        self.currmax = self.vmin + (self.vmax - self.vmin) * self.pc(bb2[0])
        if self.cb:
            try:
                self.cb(self.currmin, self.currmax)
            except:
                # this is here to catch when the widget 
                #is packed the first time
                #print "catched exception with callback... first-time init?"
                return
        
    def pc(self, value):
        if value == 0:
            return 0
        return (float(value-self.bw-20)/float(self.width-40)) #*100
        
    def getvalues(self):
        """ return the current slider values"""
        return (self.currmin, self.currmax)
        

if __name__=='__main__':
    root = Tkinter.Tk()
    rangeSlider = RangeSlider(root, width=200, height=15)
    #rangeSlider2 = RangeSlider(root, width=200, height=15)
    print rangeSlider.canvas.bbox('left')
    print rangeSlider.canvas.bbox('right')
    print rangeSlider.canvas.bbox('poly')
