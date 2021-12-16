#########################################################################
#########################################################################
# $Header: /opt/cvs/CADD/FormsCADD.py,v 1.6 2013/06/18 00:07:49 nadya Exp $
# $Id: FormsCADD.py,v 1.6 2013/06/18 00:07:49 nadya Exp $

import Tkinter
import sys, re, os
import string
from Tkinter import *

from mglutil.util.misc import ensureFontCase
from Vision.Forms import Dialog, ChangeFonts, BugReport, VarDict

class ColorDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)

    def setDialogColor(self, bg, fg):
        self.bg = bg
        self.fg = fg
        self.textFrame.config(bg = self.bg, fg = self.fg )


class AboutWF(Dialog, ColorDialog):

    def __init__(self, name='', text='', bg="white", fg="black", avg="#000044"):
        self.panel = None
        self.name = name
        self.text = text
        self.bg = bg
        self.fg = fg
	self.avg = avg

        self.buildPanel()
        self.panel.protocol("WM_DELETE_WINDOW", self.Ok)
        self.textFrame.configure(state='disabled')

    def resetTags(self):
        self.textFrame.tag_configure('email', font=(ensureFontCase('times'), 10, 'bold'),
                                     foreground=self.avg)
        self.textFrame.tag_configure('http', font=(ensureFontCase('times'), 12, 'bold'),
                                     foreground=self.avg)
        self.textFrame.tag_configure('normal10b',
                                     font=(ensureFontCase('helvetica'), 10, 'bold'),
                                     justify="right",
                                     foreground=self.avg)
        self.textFrame.tag_configure('mediumb',
                                     font=(ensureFontCase('helvetica'), 14, 'bold'),
                                     foreground=self.avg)
        self.textFrame.tag_configure('title',
                                     font=(ensureFontCase('helvetica'), 14, 'bold'),
                                     foreground=self.avg, justify="center")

    def buildPanel(self):
        Dialog.buildPanel(self) 
        self.scroll.forget()

        self.panel.title(self.name + ' workflows')
        self.textFrame.configure()
        self.textFrame.insert('end', self.text, 'normal12')
        self.textFrame.config(bg = self.bg, fg = self.fg, height=15, width=100)
	self.resetTags()


class AboutDialogCADD(AboutWF):

    def __init__(self, bg, fg):
        AboutWF.__init__(self, bg = bg, fg = fg)

    def buildPanel(self):
        AboutWF.buildPanel(self) 

        # remove scrollbar
        self.scroll.forget()

        # add own stuff
        self.panel.title('About CADD')

        self.textFrame.configure()

        self.textFrame.insert('end', 'CADD  Pipeline\n\n', 'title')
        self.textFrame.insert('end', 
                              'The Computer Aided Drug Discovery (CADD) Pipeline is a workflow environment\n'+\
			      'designed to support  Molecular  Dyanmics  Simulations and  Virtual  Screening\n'+\
			      'experiments for in silico drug discovery.\n\n',
                              'normal12')
        self.textFrame.insert('end',
                              'CADD pipeline is released as a set of Vision networks packaged for specific processes.\n\n', 
                               'normal12')
        self.textFrame.insert('end', 'Home page:\t', 'normal12')
        self.textFrame.insert('end', 
                              'http://www.nbcr.net/wiki/index.php?title=CADD_Pipeline\n\n',
                              'http')

class AcknowlDialogCADD(AboutWF):
    def __init__(self, bg, fg):
        AboutWF.__init__(self, bg = bg, fg = fg)

    def buildPanel(self):
        AboutWF.buildPanel(self) 

        # add own stuff
        self.panel.title('Acknowledgements')

        self.textFrame.insert('end', 'CADD Acknowledgements\n', 'title')
        self.textFrame.insert('end',
                              '\n\tTSRI\t\t\t\tUCSD\n\n', 'http')
        self.textFrame.insert('end',
                              'Sargis Dallakyan\t\t\t\tRommie Amaro\n'+\
                              'Stefano Forli\t\t\t\tLuca Clementi \n'+\
                              'Ruth Huey\t\t\t\tWilfred Li \n'+\
                              'Michel Sanner\t\t\t\tAndy Mccammon \n'+\
                              'Art Olson\t\t\t\tJane Ren (alumni) \n'+\
                              'Guillaume Vareille (alumni)\t\t\t\tNadyaWilliams', 'normal10')
        

class RefDialogCADD(AboutWF):

    def __init__(self, bg, fg):
        AboutWF.__init__(self, bg = bg, fg = fg)

    def buildPanel(self):
        AboutWF.buildPanel(self) 

        # remove scrollbar
        self.scroll.forget()

        # add own stuff
        self.panel.title('References')

        self.textFrame.insert('end', 'CADD References\n\n', 'title')

        self.textFrame.insert('end',
            'Opal web services for biomedical applications.\n','normal12') 
        self.textFrame.insert('end',
            'Ren, J., Williams N., Clementi L., Krishnan S. and Li W. ','normal10') 
        self.textFrame.insert('end',
            'Nucleic Acids Res 38: W724-31, 2010.\n\n','normal10')
        self.textFrame.insert('end',
            'Emerging methods for ensemble-based virtual screening.\n', 'normal12')
        self.textFrame.insert('end',
                              'Amaro, R. and Li W. ', 'normal10')
        self.textFrame.insert('end',
        'Curr Top Med Chem 10: 3-13, 2010.\n\n','normal10')


class ChangeFontsCADD(ChangeFonts):

    def __init__(self, editor=None):
	    ChangeFonts.__init__(self, editor=editor)

    def Apply_cb(self, event=None):
        if self.editor is not None:
            cfg = self.get()
            self.editor.setFont(cfg[0], cfg[1])
            from CADD.UserLibBuildCADD import saveFonts4CADDFile
            saveFonts4CADDFile(self.editor.font)
        

class BugReportCADD(AboutWF):
    def __init__(self, bg, fg):
        AboutWF.__init__(self, bg = bg, fg = fg)

    def buildPanel(self):
        AboutWF.buildPanel(self) 

        # remove scrollbar
        self.scroll.forget()

        # add own stuff
        self.panel.title('References')

        self.textFrame.insert('end', 'CADD Bug Report\n\n', 'title')

        self.textFrame.insert('end',
            'Please submit your bug report to admin@nbcr.net \n','http') 


class BugReportCADD2(BugReport):

    def __init__(self, title="Bug Report", message="", bg=None,
                 fg=None, font=(ensureFontCase('helvetica'), 10, 'bold'),):
        BugReport.__init__(self, title, message, bg, fg, font,)


    def show_upload_page(self):
        self.get_description()
         
        sumcont = VarDict['shortdesc_text']
        desccont = VarDict['desc_text']

        if len(sumcont)<=2 or len(desccont)<=2:
            import tkMessageBox
            ok = tkMessageBox.askokcancel("Input","Please enter summary and description")
            return
        from mglutil.TestUtil import BugReport
        if VarDict.has_key('attachfile'):
            upfile = VarDict['attachfile']
        else:
            upfile=[]
        
        print "VarDict 2 :",  VarDict

        BR = BugReport.BugReportCommand("CADD")
        if self.validateEmail(VarDict['email_recipient']):
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,email_ent=VarDict['email_recipient'])
        else:
            idnum = BR.showuploadpage_cb(sumcont,desccont,upfile,email_ent="")
        
        self.Ok() 
        
        # Tk message Box
        root = Tk()
        t  = Text(root)
        t.pack()


        def openHLink(event):
            start, end = t.tag_prevrange("hlink",
                               t.index("@%s,%s" % (event.x, event.y)))
            webbrowser.open_new('%s' %t.get(start, end))
            #print "Going to %s..." % t.get(start, end)

        t.tag_configure("hlink", foreground='blue', underline=1)
        t.tag_bind("hlink", "<Control-Button-1>", openHLink)
        t.insert(END, "BugReport has been Submiited Successfully\n")
        t.insert(END, "BugId is %s" %idnum)
        t.insert(END,"\nYou can visit Bug at\n")
        t.insert(END,"http://mgldev.scripps.edu/bugs/show_bug.cgi?id=%i" %int(idnum),"hlink")
        t.insert(END,"\nControl-click on the link to visit this page\n")
        t.insert(END,"\n")

