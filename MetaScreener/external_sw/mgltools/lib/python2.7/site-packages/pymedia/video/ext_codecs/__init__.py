##    Copyright (C) 2002-2003  Dmitry Borisov
##
##    This library is free software; you can redistribute it and/or
##    modify it under the terms of the GNU Library General Public
##    License as published by the Free Software Foundation; either
##    version 2 of the License, or (at your option) any later version.
##
##    This library is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##    Library General Public License for more details.
##
##    You should have received a copy of the GNU Library General Public
##    License along with this library; if not, write to the Free
##    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##

# Get all modules under current module
import os, glob, string, traceback
codecs= []

class NeedBufferException( Exception ):
  pass

def loadCodecs():
  """
   loadCodecs() -> Initially load codecs upon module start. Do not use after the module is loaded.
  """
  dir, file= os.path.split( __file__ )
  modules= glob.glob( os.path.join( dir, '*.*' ))
  probed= { '__init__': 1 }
  for module in modules:
    dir, file= os.path.split( module )
    name= string.split( file, '.' )[ 0 ]
    if name.endswith( '_d' ):
      name= name[ : len( name )- 2 ]
    if not probed.has_key( name ):
      m= __import__( '%s' % name, globals() )
      try:
        # See if codec can work on this platform
        m.probe()
        codecs.append( m )
      except:
        pass
        #traceback.print_exc()
      
      probed[ name ]= 1

def findCodec( params ):
  """
   findCodec( params ) -> codec, returns codec that closely matches params passed. 
				 Params are the same as taken form codec.getParam().
  """
  id= params[ 'id' ]
  for codec in codecs:
    if codec.id== id:
      return codec
  
  raise 'No codec with id %d exists' % id

def Decoder( params ):
  """
    Decoder( params )-> codec, creates Decoder out of the set of params. Look through all registered 
			       ext_codecs and chooses the closest one. Raises an exception when no 
				codecs are found.
  """
  c= findCodec( params )
  return c.Decoder( params )

def Encoder( params ):
  """
    Encoder( params )-> codec, creates Encoder out of the set of params. Look through all registered 
				ext_codecs and chooses the closest one. Raises an exception when no 
				codecs are found.
  """
  c= findCodec( params )
  return c.Encoder( params )

loadCodecs()
