
import sys, thread, time, traceback

import pymedia.muxer as muxer
import pymedia.audio.acodec as acodec
import pymedia.video.vcodec as vcodec
import pymedia.audio.sound as sound

SEEK_IN_PROGRESS= -2
PAUSE_SLEEP= 0.003
FILE_CHUNK= 300000
EXITING_FLAG=-1

########################################################################3
# Simple video player 
class Player:
  """
  Player is a class that plays all audio/video formats supported by pymedia
  It provides very simple interface and many features such as:
  - seeking
  - extracting metadata
  - multiple sound cards support
  - different sources for video rendering
  - error handling
  - volume operations
  
  Here is the simple way of calling Player:
    player= pymedia.Player()
    player.start()
    player.startPlayback( '<YOUR_MP3_FILE>' )
    while player.isPlaying():
      time.sleep( 0.01 )
  
  Player supports the following callback:
    class Callback:
      # called _before_ the audio frame is rendered
      # return your audio data after you process the audio frame
      # or return none for using the default sound processing
      def onAudioReady( self, afr ):
        pass
      
      # Called when the video frame is about to be rendered
      def onVideoReady( self, vfr ):
        pass
  
  Use the callback like below:
    c= Callback()
    player= pymedia.Player( c )
  """
  # ------------------------------------
  def __init__( self, callback= None ):
    """
    Create new Player instance. In case if you want to play video you have to supply the callback class instance
    which will get video data and will be able to display it properly ( onVideoReady() call ).
    For audio data the playback is done through the pymedia.sound.Output object.
    Before playing audio the onAudioReady( afr ) callback is called so you can modify audio data.
    Just return None if you do not wish to modify that data or return a sound data as string in case if you do.
    Remember that sampling frequency and number of channels should remain the same as in afr object.
    """
    self.frameNum= -1
    self.exitFlag= 1
    self.ct= None
    self.pictureSize= None
    self.paused= 0
    self.snd= None
    self.aDelta= 0
    self.aBitRate= 0
    self.vBitRate= 0
    self.seek= -1
    self.vc= None
    self.ac= None
    self.ovlTime= 0
    self.playingFile= None
    self.endPos= None
    self.loops= 0
    self.volume= 0xffff
    self.startPos= 0
    self.fileSize= 0
    self.initADelta= -1
    # Set length to 1 sec by default
    self.length= -1
    # By default the first audio card 
    self.audioCard= 0
    self.callback= callback
    self.metaData= {}
    self.fileFormat= 'mp3'
    self.aPTS= self.aindex= self.vindex= -1
    self.clearError()
    self.maxBufSize= -1
  
  # ------------------------------------
  def _resetAudio( self ):
    # No delta for audio so far
    self.snd= self.resampler= None
    self.aBitRate= self.aSampleRate= self.aChannels= self.aDelta= 0
    self.aDecodedFrames= []
    if self.ac:
      self.ac.reset()
  
  # ------------------------------------
  def _initAudio( self, params ):
    try:
      # Reset audio stream
      self._resetAudio()
      # Initializing audio codec
      self.ac= acodec.Decoder( params )
      self.aindex= -1
    except:
      self.err.append( sys.exc_info() )
  
  # ------------------------------------
  def _resetVideo( self ):
    # Init all used vars first
    self.decodeTime= self.vBitRate= self.frameNum= \
    self.sndDelay= self.hurry= self.videoPTS= \
    self.lastPTS= self.frRate= self.vDelay= 0
    self.seek= -1
    self.pictureSize= None
    if self.initADelta!= -1:
      self.seekADelta= self.initADelta
    
    # Zeroing out decoded pics queue
    self.decodedFrames= []
    self.rawFrames= []
    if self.vc:
      self.vc.reset()
  
  # ------------------------------------
  def _initVideo( self, params ):
    # There is no overlay created yet
    try:
      # Set the initial sound delay to 0 for now
      # It defines initial offset from video in the beginning of the stream
      self.initADelta= -1
      self.vindex= -1
      self._resetVideo()
      self.seekADelta= 0
      # Setting up the HW video codec
      self.vc= pymedia.video.ext_codecs.Decoder( params ) 
    except:
      try:
        # Fall back to SW video codec
        self.vc= vcodec.Decoder( params )
      except:
        pass
  
  # ------------------------------------
  def _getStreamLength( self, format, dm, f, fr ):
    # Get file size if possible
    pos= f.tell()
    f.seek( 0, 2 )
    self.fileSize= f.tell()
    f.seek( pos, 0 )
  
    # Demux frames from the beginning and from the end and get the PTS diff
    if not dm.hasHeader():
      startPTS= -1
      for d in fr:
        if d[ 3 ]> 0:
          startPTS= d[ 3 ] / 90
          break

      # Seek to the end and get the PTS from the end of the file
      if startPTS> 0:
        pos= f.tell()
        f.seek( 0, 0 )
        dm1= muxer.Demuxer( format )
        s= f.read( FILE_CHUNK )
        r= dm1.parse( s )
        endPTS= startPTS
        for d in fr:
          if d[ 3 ]> 0:
            endPTS= d[ 3 ] / 90

        f.seek( pos, 0 )
        self.length= endPTS- startPTS
    else:
      lStreams= filter( lambda x: x and ( x[ 'length' ]> 0 ), dm.streams )
      if len( lStreams ):
        self.length= max( [ x[ 'length' ] for x in lStreams ] )
      else:
        self.length= -1
        # Check file size against length and bitrates
        #if self.length* ( self.getBitRate()/ 8 )< self.fileSize:
        #  self.length= self.fileSize/ ( self.getBitRate()/ 8 )
    
  # ------------------------------------
  def _getVStreamParams( self, vindex, vparams, r ):
    # Decode one video frame and 1 audio frame to get stream data
    vDec= None
    for d in r:
      try:
        # Demux file into streams
        if d[ 0 ]== vindex:
          if not vDec:
            vDec= vcodec.Decoder( vparams )
          vfr= vDec.decode( d[ 1 ] )
          if vfr and vfr.data:
            if vfr.aspect_ratio> .0:
              self.pictureSize= ( int( vfr.size[ 1 ]* vfr.aspect_ratio ), vfr.size[ 1 ] )
            else:
              self.pictureSize= vfr.size
            
            self.vBitRate= vfr.bitrate
            break
      except:
        self.err.append( sys.exc_info() )
        break
  
  # ------------------------------------
  def _processVideoFrame( self, d, forced= False ):
    # See if we should show video frame now
    if not forced:
      self.rawFrames.append( d )
    if len( self.decodedFrames )== 0:
      if self._decodeVideoFrame( forced )== -1:
        return
    
    # See if we have our frame inline with the sound
    self._processVideo( forced )

  # ------------------------------------
  def _decodeVideoFrame( self, forced= False ):
    # Decode the video frame
    if self.snd== None and self.seek!= SEEK_IN_PROGRESS and self.aindex!= -1 and not forced:
      return -1
    
    if len( self.decodedFrames )> vcodec.MAX_BUFFERS- 4:
      # Cannot decode video frame because of too many decoded frames already
      return 0
    
    while len( self.rawFrames ):
      d= self.rawFrames.pop( 0 )
      vfr= self.vc.decode( d[ 1 ] )
      if vfr:
        if self.seek== SEEK_IN_PROGRESS and not forced:
          if vfr.data:
            self.seek= -1
          else:
            # We decode video frame after seek, but no I frame so far
            return 0
        
        # If frame has data in it, put it in to the queue along with PTS
        self.decodedFrames.append( ( vfr, self.videoPTS ) )
        # Set up the video bitrate for the informational purpose
        if self.vBitRate== 0:
          self.vBitRate= vfr.bitrate
          
        # Handle the PTS
        rate= float( vfr.rate_base )/ vfr.rate
        if d[ 3 ]> 0 and self.lastPTS< d[3]:
          # Get the first lowest PTS( we do not have DTS :( )
          self.lastPTS= d[3]
          self.videoPTS= float( d[ 3 ] ) / 90000
          #print 'VPTS:', self.videoPTS, vfr.pict_type, self.getSndLeft()
        else:
          # We cannot accept PTS, just calculate it
          self.videoPTS+= rate
        
        return 0
    
    # No more raw frames to decode
    return -2
  
  # ------------------------------------
  def _processVideo( self, forced= False ):
    while 1:
      if len( self.decodedFrames )== 0:
        return
      
      vfr, videoPTS= self.decodedFrames[ 0 ]
      self.vDelay= videoPTS- self.seekADelta- self._getPTS()
      frRate= float( vfr.rate_base )/ vfr.rate
      res= self._decodeVideoFrame()
      #print '<<', res, self.vDelay, self.frameNum, videoPTS, self._getPTS(), len( self.decodedFrames ), len( self.rawFrames ), self._getSndLeft(), self.aindex, self.isPaused()
      #if res== -1 or ( self.snd and self.getSndLeft()< frRate ) or ( res== -2 and self.vDelay> 0 and self.getSndLeft()< self.vDelay and not forced ):
      if res== -1 or ( res== -2 and self.vDelay> 0 and self._getSndLeft()< self.vDelay and not forced ):
        return
      
      # If audio queue is empty and we still have video frames, add 1 audio frame per every video frame
      if self.vDelay> 0 and self._getSndLeft()< 0.01 and self.aindex!= -1 and len( self.aDecodedFrames )== 0 and self._getPTS()> 0:
        if self.vDelay> frRate:
          self.vDelay= frRate
          
        #print 'Appending dummy audio...', self.vDelay, frRate
        self._appendDummyAudio( self.vDelay )
        time.sleep( self.vDelay )
        self.vDelay= 0
      
      # If delay
      #print '!!', self.vDelay, self.frameNum, videoPTS, self._getPTS(), len( self.decodedFrames ), len( self.rawFrames ), self._getSndLeft(), self.seekADelta
      if self.vDelay> 0 and self._getSndLeft()> self.vDelay:
        time.sleep( self.vDelay / 6 )
        #print 'Delay', self.vDelay, self.getSndLeft()
        self.vDelay= 0
      
      if self.vDelay< frRate / 4 or forced:
        # Remove frame from the queue
        del( self.decodedFrames[ 0 ] )
        
        # Get delay for seeking
        if self.frameNum== 0 and self.initADelta== -1:
          self.initADelta= self._getSndLeft()
        
        # Increase number of frames
        self.frameNum+= 1
        
        # Skip frame if no data inside, but assume it was a valid frame though
        if vfr.data:
          try: self.callback.onVideoReady( vfr )
          except: pass
          
          self.vDelay= frRate
  
  # ------------------------------------
  def _appendDummyAudio( self, length ):
    # Get PCM length of the audio frame
    l= self.aSampleRate* self.aChannels* 2* length
    self.aDecodedFrames.append( ( '\0'* int( l ), self.aSampleRate, self.aChannels ) )
    self._processAudio()
  
  # ------------------------------------
  def _processAudioFrame( self, d ):
    # Decode audio frame
    afr= self.ac.decode( d[ 1 ] )
    if afr:
      # See if we have to set up the sound
      if self.snd== None:
        self.aBitRate= afr.bitrate
        self.aSampleRate= afr.sample_rate
        self.aChannels= afr.channels
        try:
          # Hardcoded S16 ( 16 bit signed ) for now
          #print 'Opening sound', afr.sample_rate, afr.channels, sound.AFMT_S16_LE, self.audioCard
          self.snd= sound.Output( afr.sample_rate, afr.channels, sound.AFMT_S16_LE, self.audioCard )
          self.resampler= None
        except:
          try:
            # Create a resampler when no multichannel sound is available
            self.resampler= sound.Resampler( (afr.sample_rate,afr.channels), (afr.sample_rate,2) )
            # Fallback to 2 channels
            #print 'Falling back to', afr.sample_rate, 2, sound.AFMT_S16_LE, self.audioCard
            self.snd= sound.Output( afr.sample_rate, 2, sound.AFMT_S16_LE, self.audioCard )
          except:
            self.err.append( sys.exc_info() )
            raise
         
        # Calc max buf size for better audio handling
        if self.maxBufSize== -1:
          self.maxBufSize= self.snd.getSpace()
      
      # Handle the PTS accordingly
      snd= self.snd
      if d[ 3 ]> 0 and self.aDelta== 0 and snd:
        # set correction factor in case of PTS presence
        self.aDelta= ( float( d[ 3 ] ) / 90000 )- snd.getPosition()- snd.getLeft()
      
      # Play the raw data if we have it
      if len( afr.data )> 0:
        # Split the audio data if the size of data chunk larger than the buffer size
        data= afr.data
        if len( data )> self.maxBufSize:
          data= str( data )
        
        while len( data )> self.maxBufSize:
          chunk= data[ : self.maxBufSize ]
          data= data[ self.maxBufSize: ]
          self.aDecodedFrames.append( ( chunk, afr.sample_rate, afr.channels ) )
        
        self.aDecodedFrames.append( ( data, afr.sample_rate, afr.channels ) )
        self._processAudio()
  
  # ------------------------------------
  def _processAudio( self ):
    snd= self.snd
    while len( self.aDecodedFrames ) and snd:
      # See if we can play sound chunk without clashing with the video frame
      if len( self.aDecodedFrames[ 0 ][ 0 ] )> snd.getSpace() and self.vindex!= -1:
        break
      
      #print 'player SOUND LEFT:', self.snd.getLeft(), self.snd.getSpace(), self.isPlaying()
      if self.isPlaying():
        data, sampleRate, channnels= self.aDecodedFrames.pop(0)
        if self.callback:
          try:
            data1= self.callback.onAudioReady( data, sampleRate, channnels )
            if data1:
              data= data1
          except:
            pass
        
        # See if we need to resample the audio data
        if self.resampler:
          data= self.resampler.resample( data )
        
        snd.play( data )
  
  # ------------------------------------
  def start( self ):
    """
    Start player object. It starts internal loop only, no physical playback is started.
    You have to call start only once for the player instance.
    If you wish to play multiple files just call startPlayback() subsequently.
    """
    if self.ct:
        raise 'cannot run another copy of vplayer'
    self.exitFlag= 0
    self.pictureSize= None
    self.ct= thread.start_new_thread( self._readerLoop, () )
  
  # ------------------------------------
  def stop( self ):
    """
    Stop player object. It stops internmal loop and any playing file.
    Once the internal loop is stopped the further playback is not possible until you issue start() again.
    """
    self.stopPlayback()
    if self.callback:
      try: self.callback.removeOverlay()
      except: pass
    
    # Turn the flag to exist the main thread
    self.exitFlag= EXITING_FLAG
  
  # ------------------------------------
  def startPlayback( self, file, format= 'mp3', paused= False ):
    """
    Starts playback of the file passed as string or file like object.
    Player should already be started otherwise this call has no effect.
    If any file is already playing it will stop the playback and start playing the file you pass.
    'paused' parameter can specifiy if the playback should not start until unpausePlayback() is called.
    'paused' parameter is helpfull when you want to start your playback exactly at a certain time avoiding any delays
    caused by the file opening or codec initilizations.
    """
    self.stopPlayback()
    # Set the new file for playing
    self.paused= paused
    self.fileFormat= format
    self.playingFile= file
    try:
      self.setVolume( vars.volume )
    except:
      pass
  
  # ------------------------------------
  def stopPlayback( self ):
    """
    Stops file playback. If media file is not playing currently, it does nothing.
    If file was paused it will unpause it first.
    """
    self.playingFile= None
    self.unpausePlayback()
    if self.snd:
      self.snd.stop()
      self.snd= None
  
  # --------------------------------------------------------
  def pausePlayback( self ):
    """ Pause playing the current file """
    if self.isPlaying():
      self.paused= 1
      if self.snd:
        self.snd.pause()
  
  # --------------------------------------------------------
  def unpausePlayback( self ):
    """ Resume playing the current file """
    if self.isPlaying():
      if self.snd:
        self.snd.unpause()
    
    self.paused= 0
  
  # ------------------------------------
  def isPaused( self ):
    """ Returns whether playback is paused """
    return self.paused
  
  # ------------------------------------
  def seekTo( self, secs ):
    """
    Seeks the file playback position to a given number of seconds from the beginning.
    Seek may position not exactly as specified especially in video files.
    It will look for a first key frame and start playing from that position.
    In some files key frames could resides up to 10 seconds apart.
    """
    while self.seek>= 0:
      time.sleep( 0.01 )
    
    if secs< 0:
      secs= 0
    
    self.seek= secs
  
  # ------------------------------------
  def isPlaying( self ):
    """ Returns whether playback is active """
    return self.playingFile!= None and self.isRunning()
  
  # ------------------------------------
  def isRunning( self ):
    """
    Returns whether Player object can do the playback.
    It will return False after you issue stop()
    """
    return self.exitFlag in ( EXITING_FLAG, 0 )
  
  # ------------------------------------
  def getError( self ):
    """
    Return error list if any
    """
    return self.err
  
  # ------------------------------------
  def clearError( self ):
    """
    Clear all errors
    """
    self.err= []
  
  # ------------------------------------
  def setLoops( self, loops ):
    """
    Set number of loops the player will play current file
    """
    self.loops= loops
  
  # ------------------------------------
  def setStartTime( self, timePosSec ):
    """
    Set start time for the media track to start playing.
    Whenever file is played it will start from the timePosSec position in the file.
    """
    self.startPos= timePosSec
  
  # ------------------------------------
  def setEndTime( self, timePos ):
    """
    Set end time for the media track.
    Whenever file is reached the endTime it will stop playing.
    """
    self.endPos= timePos
  
  # ------------------------------------
  def setVolume( self, volume ):
    """
    Set volume for the media track to play
    volume = [ 0..65535 ]
    """
    self.volume= volume
    # Asume the very first is the the Master volume
    conns= sound.Mixer().getControls()
    if len( conns ):
      conns[ 0 ][ 'control' ].setValue( self.volume )
  
  # ------------------------------------
  def getVolume( self ):
    """
    Get volume for the playing media track 0..65535
    """
    # Asume the very first is the the Master volume
    conns= sound.Mixer().getControls()
    if len( conns ):
      return conns[ 0 ][ 'control' ].getValue()
    
    return 0
  
  # ------------------------------------
  def getPictureSize( self ):
    """
    Whenever the file containing video is played, this function returns the actual picture size for the
    video part. It may be None if no video is found in the media file.
    Note: picture size may be unknown for up to 1 second after you call startPlayback() !
    """
    return self.pictureSize

  # ------------------------------------
  def getLength( self ):
    """
    Get length of the media file in seconds
    Note: length may be unknown for up to 1 second after you call startPlayback() !
    """
    return self.length

  # ------------------------------------
  def getMetaData( self ):
    """
    Get meta data from the media file as dictionary
    Note: metadata may be unknown for up to 1 second after you call startPlayback() !
    """
    return self.metaData

  # ------------------------------------
  def getSampleRate( self ):
    """
    Get sample rate of the playing file
    """
    return self.sampleRate

  # ------------------------------------
  def getABitRate( self ):
    """
    Get bitrate for the audio stream if present
    """
    if self.aindex!= -1:
      return self.aBitRate
    
    return 0

  # ------------------------------------
  def getBitRate( self ):
    """
    Get bitrate for the full stream
    """
    return self.getABitRate()+ self.vBitRate

  # ------------------------------------
  def getPosition( self ):
    """
    Returns current position for the media
    """
    if self.isPlaying():
      return self._getPTS()
    
    return 0
  
  # ------------------------------------
  def _hasQueue( self ):
    queue= 0
    if self.aindex!= -1:
      queue+= len( self.aDecodedFrames )
    if self.vindex!= -1:
      queue+= len( self.rawFrames )+ len( self.decodedFrames )
    
    return queue> 0

  # ------------------------------------
  def _getPTS( self ):
    if self.aindex== -1:
      if not self.aPTS:
        self.aPTS= time.time()
      
      return time.time()- self.aPTS
    
    if self.snd== None:
      return 0
    
    p= self.snd.getPosition()
    return p+ self.aDelta
  
  # ------------------------------------
  def _getSndLeft( self ):
    if self.snd== None:
      if self.aindex== -1:
        return 1
      else:
        return 0
    
    return self.snd.getLeft()
  
  # ------------------------------------
  def _readerLoop( self ):
    f= None
    try:
      while self.exitFlag== 0:
        if self.playingFile== None:
          time.sleep( 0.01 )
          continue
        
        self.length= self.frameNum= -1
        # Initialize demuxer and read small portion of the file to have more info on the format
        self.clearError()
        if type( self.playingFile ) in ( str, unicode ):
          try:
            f= open( self.playingFile, 'rb' )
            format= self.playingFile.split( '.' )[ -1 ].lower()
          except:
            traceback.print_exc()
            self.err.append( sys.exc_info() )
            self.playingFile= None
            continue
        else:
          format= self.fileFormat
          f= self.playingFile
        
        try:
          dm= muxer.Demuxer( format )
          s= f.read( FILE_CHUNK )
          r= dm.parse( s )
        except:
          traceback.print_exc()
          self.err.append( sys.exc_info() )
          self.playingFile= None
          continue
        
        try: self.metaData= dm.getHeaderInfo()
        except: self.metaData= {}
        
        # This seek sets the seeking position already at the desired offset from the beginning
        if self.startPos:
          self.seekTo( self.startPos )
        
        # Setup video( only first matching stream will be used )
        self.clearError()
        self.vindex= -1
        streams= filter( lambda x: x, dm.streams )
        for st in streams:
          if st and st[ 'type' ]== muxer.CODEC_TYPE_VIDEO:
            self._initVideo( st )
            self.vindex= list( streams ).index( st )
            break
        
        # Setup audio( only first matching stream will be used )
        self.aindex= -1
        self.aPTS= None
        for st in streams:
          if st and st[ 'type' ]== muxer.CODEC_TYPE_AUDIO:
            self._initAudio( st )
            self.aindex= list( streams ).index( st )
            break
        
        # Open current file for playing
        currentFile= self.playingFile
        if self.vindex>= 0:
          self._getVStreamParams( self.vindex, streams[ self.vindex ], r )
        
        self._getStreamLength( format, dm, f, r )
        
        # Play until no exit flag, not eof, no errs and file still the same
        while len(s) and len( self.err )== 0 and \
            self.exitFlag== 0 and self.playingFile and len( streams ) and \
            self.playingFile== currentFile:
          
          if self.isPaused():
            time.sleep( PAUSE_SLEEP )
            continue
        
          for d in r:
            if self.playingFile!= currentFile:
              break
            
            # Seeking stuff
            if self.seek>= 0:
              # Find the file position first
              if self.length> 0 and self.fileSize> 0:
                #print self.seek, self.length, self.fileSize, ( float( self.seek ) / self.length )* self.fileSize
                f.seek( ( float( self.seek ) / self.length )* self.fileSize, 0 )
              else:
                f.seek( self.seek* self.getBitRate()/ 8, 0 )
                #print self.seek, self.getBitRate(), f.tell()
              
              #print 'seek to', self.seek, f.tell()
              seek= self.seek
              self.aDecodedFrames= []
              if self.ac:
                self.ac.reset()
                self.snd.stop()
              self.rawFrames= []
              self.decodedFrames= []
              if self.vc:
                self.vc.reset()
              
              dm.reset()
              if self.vindex== -1:
                # Seek immediately if only audio stream is available
                self.seek= -1
                self.aDelta= seek
              else:
                # Wait for a key video frame to arrive
                self.seek= SEEK_IN_PROGRESS
              break
            
            # See if we reached the end position of the video clip
            if self.endPos and self._getPTS()* 1000> self.endPos:
              # Seek at the end and close the reading loop instantly 
              f.seek( 0, 2 )
              break
            
            try:
              # Update length if not set already
              if self.getLength()== -1 and self.getBitRate()> 0:
                # Check file size against length and bitrates
                self.length= self.fileSize/ ( self.getBitRate()/ 8 )
              
              # Demux file into streams
              if d[ 0 ]== self.vindex:
                # Process video frame
                seek= self.seek
                self._processVideoFrame( d )
                if self.seek!= SEEK_IN_PROGRESS and seek== SEEK_IN_PROGRESS:
                  # If key frame was found, change the time position
                  self.videoPTS= ( float( f.tell() )/ self.fileSize )* self.length
                  self.aDelta= self.videoPTS+ self.initADelta
                  #print '---->position', f.tell(), self.aDelta
              elif d[ 0 ]== self.aindex and self.seek!= SEEK_IN_PROGRESS:
                # Decode and play audio frame
                self._processAudioFrame( d )
            except:
              traceback.print_exc()
              self.err.append( sys.exc_info() )
              self.playingFile= None
              break
          
          # Read next encoded chunk and demux it
          try:
            s= f.read( 512 )
            r= dm.parse( s )
          except:
            traceback.print_exc()
            self.err.append( sys.exc_info() )
            self.playingFile= None
            continue
        
        if f: f.close()

        # Close current file when error detected
        if len( self.err ):
          self.stopPlayback()
        
        # Wait until all frames are played
        while self._hasQueue()> 0 and self.isPlaying():
          self._processVideoFrame( None, True )
          self._processAudio()
        
        while self.aindex!= -1 and self._getSndLeft()> 0 and self.isPlaying():
          time.sleep( 0.01 )
        
        self._resetAudio()
        self._resetVideo()
        
        if self.loops> 0:
          self.loops-= 1
          continue
        
        # Report the file end
        try: f= self.callback.onPlaybackEnd
        except: f= None
        if f: 
          f( self )
        else:
          self.playingFile= None
    except:
      traceback.print_exc()
    
    self.exitFlag= 1
