# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 17:00:56 2014

@author: ludo
"""
#import the shader
from opengltk.OpenGL.GL import *
from opengltk.extent import _gllib,_glextlib
from opengltk.extent._glextlib import *
from opengltk.OpenGL.GLU import gluPerspective, gluPickMatrix, gluUnProject, gluErrorString, gluLookAt
#for now use the simple shader for shadow
from DejaVu.shaders.shaderShadow import fshadow,pcf_fshadow, vshadow

GL_DEPTH_COMPONENT32=0x81A7

import numpy
from numpy import matrix
import math

class Shadow:
    def __init__(self,viewer=None, camera=None ,light=None):
        self.light=light
        self.viewer=viewer
        self.camera=camera
#        self.light_direction = self.light.direction
        self.width=1024#self.camera.width # 2048
        self.height=1024#self.camera.height #
        self.uniforms={}
        self.shadow_depthtextureName=None
        self.initialized = False
        self.shader_initialized = False
#        self.setupFBO()
#        self.fragmentShaderCode=frag_shadow_gem
#        self.vertexShaderCode=vert_shadow_gem
        self.fragmentShaderCode=pcf_fshadow#fshadow
        self.vertexShaderCode=vshadow
        self.lookAt = numpy.zeros(3)
        self.lookFrom = numpy.zeros(3)#self.camera.far
        self.cam_model = numpy.eye(4)
        self.distance = 100.0
        self.near = 0.1
        self.far = self.camera.far*2.0#too far for orthographic
        self.bias = numpy.array([	
                0.5, 0.0, 0.0, 0.0, 
                0.0, 0.5, 0.0, 0.0,
                0.0, 0.0, 0.5, 0.0,
                0.5, 0.5, 0.5, 1.0],'f');
        self.distance = self.camera.far
        self.d=0
        
    def setLight(self,light):
        self.light=light
        nc = numpy.sqrt(numpy.add.reduce(self.camera.lookFrom*self.camera.lookFrom))
        v = self.camera.lookAt + numpy.array(self.light.direction)[:3]
        nv = numpy.sqrt(numpy.add.reduce(v*v))
        v = (v/nv)*self.distance#self.light.length
        self.lookAt = self.camera.lookAt#numpy.array(self.light.direction)[:3]
        self.lookFrom = v#numpy.array(self.light.direction)[:3]*-self.camera.far#self.distance#self.camera.far#self.camera.far
        aspect = self.width / float(self.height)

        fov2 = (45.0*math.pi) / 360.0  # fov/2 in radian
        self.d = self.near + (self.far - self.near)*0.5
#        d = self.light.length
        self.top = self.d*math.tan(fov2)
        self.bottom = -self.top
        self.right = aspect*self.top
        self.left = -self.right
        #projection ? this actually the view matrix...
        self.lightRot = numpy.array(self.getLookAtMatrix(self.lookFrom,self.lookAt,numpy.array([0.,1.,0.])),'f').flatten()
#        print "setLight",self.lightRot#,self.lightView
        
    def setShader(self,):
        self.program=None
        f = _glextlib.glCreateShader(_glextlib.GL_FRAGMENT_SHADER)
        v = _glextlib.glCreateShader(_glextlib.GL_VERTEX_SHADER)
        lStatus = 0x7FFFFFFF
        _glextlib.glShaderSource(v, 1, self.vertexShaderCode, lStatus)
        _glextlib.glCompileShader(v)
        _glextlib.glShaderSource(f, 1, self.fragmentShaderCode, lStatus)
        _glextlib.glCompileShader(f)

        lStatus1 = _glextlib.glGetShaderiv(f, _glextlib.GL_COMPILE_STATUS, lStatus )
        lStatus2 = _glextlib.glGetShaderiv(v, _glextlib.GL_COMPILE_STATUS, lStatus )
        if lStatus1 == 0 or lStatus2 == 0:
#                print "compile status", lStatus
            charsWritten  = 0
            shaderInfoLog = '\0' * 2048
            charsWritten, infoLog = _glextlib.glGetShaderInfoLog(f, len(shaderInfoLog), 
                                                                 charsWritten, shaderInfoLog)
            print "shaderInfoLog", shaderInfoLog
            print "shader didn't compile",infoLog
        else:
            self.program = _glextlib.glCreateProgram()
            _glextlib.glAttachShader(self.program,v)
            _glextlib.glAttachShader(self.program,f)                
            _glextlib.glLinkProgram(self.program)
            lStatus = 0x7FFFFFFF
            lStatus = _glextlib.glGetProgramiv(self.program,
                                               _glextlib.GL_LINK_STATUS,
                                               lStatus )
            if lStatus == 0:
#                    print "link status", lStatus
                log = ""
                charsWritten  = 0
                progInfoLog = '\0' * 2048
                charsWritten, infoLog = _glextlib.glGetProgramInfoLog(self.program, len(progInfoLog), 
                                                                 charsWritten, progInfoLog)
                print "shader didn't link"
                print "log ",progInfoLog

            else:
                _glextlib.glValidateProgram(self.program)
                lStatus = 0x7FFFFFFF
                lStatus = _glextlib.glGetProgramiv(self.program,
                                                   _glextlib.GL_VALIDATE_STATUS,
                                                   lStatus )
                if lStatus == 0:
                    print "shader did not validate, status:", lStatus
#                else:
                    # Get location 
#                    

    def getUniforms1(self):
        self.uniforms['camMatrix'] = glGetUniformLocation(self.program, 'camMatrix')
        self.uniforms['shadowMatrix'] = glGetUniformLocation(self.program, 'shadowMatrix')
        self.uniforms['shadowMap'] = glGetUniformLocation(self.program, 'shadowMap')
        self.uniforms['useShadow'] = glGetUniformLocation(self.program, 'useShadow')

    def getUniforms(self):
        self.uniforms['camModel'] = glGetUniformLocation(self.program, 'camModel')
        self.uniforms['lightProj'] = glGetUniformLocation(self.program, 'lightProj')
        self.uniforms['lightView'] = glGetUniformLocation(self.program, 'lightView')
        self.uniforms['lightRot'] = glGetUniformLocation(self.program, 'lightRot')
        self.uniforms['lightNear'] = glGetUniformLocation(self.program, 'lightNear')
        self.uniforms['lightFar'] = glGetUniformLocation(self.program, 'lightFar')
        self.uniforms['shadowMap'] = glGetUniformLocation(self.program, 'shadowMap')
        self.uniforms['shadowMapSize'] = glGetUniformLocation(self.program, 'shadowMapSize')
        self.uniforms['LightSourcePos'] = glGetUniformLocation(self.program, 'LightSourcePos')

    def setModeMAtrixUniform(self,matrice):
        glUniformMatrix4fv(self.uniforms['camModel'], 1, False, matrice)

    def setUniforms(self): 
        glUniformMatrix4fv(self.uniforms['camModel'], 1, False, self.light_mvp)#self.cam_model)
        glUniformMatrix4fv(self.uniforms['lightProj'], 1, False, self.lightProj)
        glUniformMatrix4fv(self.uniforms['lightView'], 1, False, self.lightView)
        glUniformMatrix4fv(self.uniforms['lightRot'], 1, False, self.cam_model)
        glUniform1i(self.uniforms['shadowMap'],7)
        glUniform1f(self.uniforms['lightNear'],float(self.near)) 
        glUniform1f(self.uniforms['lightFar'],float(self.far))
        glUniform2f(self.uniforms['shadowMapSize'],float(self.width), float(self.height))
        glUniform3f(self.uniforms['LightSourcePos'],float(self.lookFrom[0]),float(self.lookFrom[1]),float(self.lookFrom[2]))
        #glUniformMatrix4fv(self.shader.uniforms['shadowMatrix'], 1, False, glGetFloatv(GL_MODELVIEW_MATRIX))
        
    def setShadowTexture(self):
        self.shadow_depthtextureName=int(glGenTextures(1)[0])
        glActiveTexture(GL_TEXTURE7) 
        glPrioritizeTextures(numpy.array([self.shadow_depthtextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture (GL_TEXTURE_2D, self.shadow_depthtextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);
#        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
#        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        _gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self.width,
                      self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None); 
#        _gllib.glBindTexture (GL_TEXTURE_2D, 0);              

    def setupFBO(self):
#        if not self.initialized:
#            self.setShadowTexture()
#            self.setShader()
#            self.getUniforms()
#        return
        glClearColor(0,0,0,1.0);
#        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        if not self.initialized:
            self.initialized = True
            self.setShadowTexture()
            self.fbo = 0#glGenFramebuffers(1);
            self.fbo = _glextlib.glGenFramebuffersEXT(1, self.fbo)
            #self.shadowTexture = glGenTextures(1)
            lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            if lCheckMessage != _glextlib.GL_FRAMEBUFFER_COMPLETE_EXT: # 0x8CD5
                print 'glCheckFramebufferStatusEXT %x'%lCheckMessage
            print "fbo ",self.fbo,lCheckMessage
            _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, self.fbo )
                
            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)
                
    #        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.fbo, 0)
            ## attaching the current stencil to the FBO (Frame Buffer Object)
            _glextlib.glFramebufferTexture2DEXT(_glextlib.GL_FRAMEBUFFER_EXT,
                                         _glextlib.GL_DEPTH_ATTACHMENT_EXT,
                                         GL_TEXTURE_2D, self.shadow_depthtextureName,0)
            _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, 0)
#        else :
#            _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, self.fbo )
#            glActiveTexture(GL_TEXTURE7)
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.shadow_depthtextureName);
#            _gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self.width,
#                      self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None); 
        #glActiveTexture(GL_TEXTURE0)   
        print "OK"
            
    def shadow_pass(self,):
        self.setupFBO()
        #glUniform1i(self.uniforms['useShadow'], 0)
#        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0,0.0,0.0,1.0)
        glEnable(GL_CULL_FACE)
#        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, self.fbo )
        glClear(GL_DEPTH_BUFFER_BIT)
        self.viewer.rootObject.culling=GL_FRONT
#        self.viewer.rootObject.Set(culling=GL_FRONT)
#        glCullFace(GL_FRONT)
#        glCullFace(GL_BACK)  
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE); 
        self.setProjection()    
        #FORCE FRONT CULLING?
        self.camera.RedrawObjectHierarchy()
        _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, 0)
        #grab the depth buffer
        _gllib.glBindTexture (GL_TEXTURE_2D, 0);
#        glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self.width,
#                     self.height, 0);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);

    def normal_pass(self):
        if not self.shader_initialized:
            self.setShader()
            self.getUniforms()
            self.shader_initialized=True
#        self.cam_model = self.camera.GetMatrixInverse().flatten()#.transpose().flatten()
        self.setProjection()
        self.cam_model = self.viewer.rootObject.GetMatrix(transpose=False).flatten()
        glActiveTexture(GL_TEXTURE7);#is this working ?
        glBindTexture(GL_TEXTURE_2D,self.shadow_depthtextureName);
#        self.setTextureMatrix()
        self.setMVPLight()
        glUseProgram( self.program )
        self.setUniforms()
        self.camera.SetupProjectionMatrix()
        self.viewer.rootObject.culling=GL_BACK
#        self.viewer.rootObject.Set(culling=GL_BACK)
#        glCullFace(GL_BACK) 
#        glCullFace(GL_FRONT)
	        
        
    def getLookAtMatrix(self,_eye, _lookat, _up):
          ez = _eye - _lookat
          ez = ez / numpy.linalg.norm(ez)
        
          ex = numpy.cross(_up, ez)
          ex = ex / numpy.linalg.norm(ex)
        
          ey = numpy.cross(ez, ex)
          ey = ey / numpy.linalg.norm(ey)
        
          rmat = numpy.eye(4)
          rmat[0][0] = ex[0]
          rmat[0][1] = ex[1]
          rmat[0][2] = ex[2]
        
          rmat[1][0] = ey[0]
          rmat[1][1] = ey[1]
          rmat[1][2] = ey[2]
        
          rmat[2][0] = ez[0]
          rmat[2][1] = ez[1]
          rmat[2][2] = ez[2]
        
          tmat = numpy.eye(4)
          tmat[0][3] = -_eye[0]
          tmat[1][3] = -_eye[1]
          tmat[2][3] = -_eye[2]
        
          # numpy.array * is element-wise multiplication, use dot()
          lookatmat = numpy.dot(rmat, tmat).transpose()
        
          return lookatmat
        
    def setProjectionOLD(self):
#        oldType = self.camera.projectionType
#        self.camera.projectionType = self.camera.ORTHOGRAPHIC
#        self.camera.SetupProjectionMatrix()
#        self.camera.projectionType = oldType
        self.lightProj = glGetFloatv(GL_PROJECTION_MATRIX)
        self.lightView = glGetDoublev(GL_MODELVIEW_MATRIX);#pointer or actual matrix
        fx, fy, fz = self.lookFrom
        ax, ay, az = self.lookAt#[0,0,0]#self.lookAt / should be center o fmolecule
        gluLookAt( float(fx), float(fy), float(fz),
                   float(ax), float(ay), float(az),
                   float(0), float(1), float(0))

    def setProjection(self):        
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
#        gluPerspective(90.0, self.width/float(self.height), 1, 1000)
#        gluPerspective(float(45.0),
#                           float(self.width)/float(self.height),
#                           float(self.camera.near), float(self.camera.far))#        
#        glOrtho(-40,40,-40,40, 0.1,500.0);
        glOrtho(float(self.left), float(self.right),
                    float(self.bottom), float(self.top), 
                    float(self.near),float(self.far))
        self.lightProj = numpy.array(glGetFloatv(GL_PROJECTION_MATRIX)[:],'f')
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        fx, fy, fz = self.lookFrom
        ax, ay, az = self.lookAt#[0,0,0]#self.lookAt / should be center o fmolecule
        #ux, uy, uz = self.up
        #thats what change
        gluLookAt( float(fx), float(fy), float(fz),
                   float(ax), float(ay), float(az),
                   float(0), float(1), float(0))
        self.lightView = numpy.array(glGetFloatv(GL_MODELVIEW_MATRIX)[:],'f')
        
#        self.shadow_model_view = glGetDoublev(GL_MODELVIEW_MATRIX);
#        self.shadow_projection = glGetDoublev(GL_PROJECTION_MATRIX);
#        glMatrixMode(GL_MODELVIEW)
#        glLoadIdentity()
#        glMultMatrixd(self.shadow_projection)
#        glMultMatrixd(self.shadow_model_view)       
##        #glUniformMatrix4fv(self.uniforms['camMatrix'], 1, False, glGetFloatv(GL_MODELVIEW_MATRIX))
#        glLoadIdentity()  
#        gluLookAt( float(fx), float(fy), float(fz),
#                   float(ax), float(ay), float(az),
#                   float(0), float(1), float(0))

    def setMVPLightNumpy(self):
        m1=matrix(self.bias.reshape(4,4))
        m2=matrix(self.lightProj.reshape(4,4))
        m3=matrix(self.lightView.reshape(4,4))
        m4=matrix(self.cam_model.reshape(4,4))
        self.light_mvp = m4 * m3 * m2 

    def setMVPLight(self):
        #    		static double modelView[16];
        #    		static double projection[16];    		
        #    		// Moving from unit cube [-1,1] to [0,1]  
        		
        #    		// Grab modelview and transformation matrices
        #    		self.lightView =glGetDoublev(GL_MODELVIEW_MATRIX)#, modelView);
        #    		self.lightProj =glGetDoublev(GL_PROJECTION_MATRIX)#, projection);
        		
        glMatrixMode(GL_TEXTURE);
        #    		glActiveTextureARB(GL_TEXTURE7);
        _glextlib.glActiveTexture(GL_TEXTURE7);
        		
        glLoadIdentity();	
        glLoadMatrixf(self.bias); 
#        print "bias",self.bias
        #    		// concatating all matrices into one.
        glMultMatrixf (self.lightProj);
#        print self.lightProj
        glMultMatrixf (self.lightView);
#        print self.lightView
#        glMultMatrixf (self.cam_model);
#        print self.cam_model
        #    		// Go back to normal matrix mode
        self.light_mvp = glGetFloatv(GL_TEXTURE_MATRIX)
#        print "mvp",self.light_mvp    		
        glMatrixMode(GL_MODELVIEW);
#        glGetDoublev(GL_MODELVIEW_MATRIX)
#        print "OK set TextureMatrix",self.lightProj,self.lightView,self.cam_model
