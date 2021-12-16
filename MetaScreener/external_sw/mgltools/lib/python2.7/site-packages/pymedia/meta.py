
import os, traceback
import pymedia

HEADER_CHUNK_SIZE= 30000
FREQUENCY_KEY= 'sample_freq'
CHANNELS_KEY= 'channels'
BITRATE_KEY= 'bitrate'

# -----------------------------------------------------
# Get metadata from the media file
def getMetaData( f, ext= None ):
  info= {}
  if type( f ) in ( str, unicode ):
    ext= f.split( os.path.extsep )[ -1 ]
    f= open( f, 'rb' )
  
  try: s= f.read( HEADER_CHUNK_SIZE )
  except: traceback.print_exc(); return info;
  
  ext= ext.lower()
  dm= pymedia.muxer.Demuxer( ext )
  fr= dm.parse( s )
  if len( dm.streams )== 0:
    return {}
  
  dec= pymedia.audio.acodec.Decoder( dm.streams[ 0 ] )
  # Decode only first frame to get frame parameters
  d= dec.decode( fr[ 0 ][ 1 ] )
  if d and ( dm.hasHeader()> 0 or len( d.data )> 0 ):
    # Assign parameters to the file
    info.update( { FREQUENCY_KEY: d.sample_rate,
                CHANNELS_KEY: d.channels,
                BITRATE_KEY: d.bitrate / 1000 } )
  
  # Hardcoding for mp3
  if not dm.hasHeader() and ext== 'mp3':
    try:
      f.seek( -128, 2 )
      dm= pymedia.muxer.Demuxer( ext )
      dm.parse( f.read( 128 ) )
    except:
      traceback.print_exc(); 
  
  if dm.hasHeader():
    info.update( dm.getHeaderInfo() )
  
  return info
