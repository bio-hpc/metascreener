########################################################################
#
# Date: Sept 2012  Author: Michel Sanner
#
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/drawNode.py,v 1.3 2013/08/21 20:47:51 sanner Exp $
#
# $Id: drawNode.py,v 1.3 2013/08/21 20:47:51 sanner Exp $
#

import cairo, os
from PIL import Image, ImageFilter
from math import sqrt, pi

def dropShadow( image, offset=(5,5), background=0x00ffffff, shadow=0xff000000, 
                border=8, iterations=3):
    # taken from http://code.activestate.com/recipes/474116-drop-shadows-with-pil/
    # modified by Michel Sanner to work with transparency, using masks
    #
    #  adds offset + 2*border padding
    #  the original image is at (border - min(offset[0], 0), border - min(offset[1], 0))
    """
    Add a gaussian blur drop shadow to an image.  
    
    image       - The image to overlay on top of the shadow.
    offset      - Offset of the shadow from the image as an (x,y) tuple.  Can be
                  positive or negative.
    background  - Background colour behind the image.
    shadow      - Shadow colour (darkness).
    border      - Width of the border around the image.  This must be wide
                  enough to account for the blurring of the shadow.
    iterations  - Number of times to apply the filter.  More iterations 
                produce a more blurred shadow, but increase processing time.
    """

    # to fix bug in 1.1.7 http://hg.effbot.org/pil-2009-raclette/changeset/fb7ce579f5f9
    image.load()
    r,g,b,a = image.split()

    # Create the backdrop image -- a box in the background colour with a 
    # shadow on it.
    totalWidth = image.size[0] + abs(offset[0]) + 2*border
    totalHeight = image.size[1] + abs(offset[1]) + 2*border
    back = Image.new(image.mode, (totalWidth, totalHeight), background)
  
    # Place the shadow, taking into account the offset from the image
    shadowLeft = border + max(offset[0], 0)
    shadowTop = border + max(offset[1], 0)
    back.paste(shadow, [shadowLeft, shadowTop, shadowLeft + image.size[0], 
                        shadowTop + image.size[1]], mask=a )
  
    # Apply the filter to blur the edges of the shadow.  Since a small kernel
    # is used, the filter must be applied repeatedly to get a decent blur.
    n = 0
    while n < iterations:
        back = back.filter(ImageFilter.BLUR)
        n += 1
    
    # Paste the input image onto the shadow backdrop  
    imageLeft = border - min(offset[0], 0)
    imageTop = border - min(offset[1], 0)
    back.paste(image, (imageLeft, imageTop), mask=a)
  
    return back, (imageLeft,imageTop) # return offset of original image in new image 


class CairoNodeRenderer:

    def __init__(self):
        self.nodeOutLineWidth = 4
        self.border = 10
        self.bbox = [99999, 99999, 0,0] # node icon bbox


    def drawSquareFlatBox(self, width, height, outline, fill, macro=False):
        # draw the box
        # old version that drew flat boxes (no shadow)
        
        # fill the rectangle with 0.5 alpha
        self.ctx.rectangle( ulx, uly, width, height)
        self.ctx.set_source_rgba(*fill)
        self.ctx.fill()

        # update bbox
        if ulx<self.bbox[0]: self.bbox[0] = ulx
        if uly<self.bbox[1]: self.bbox[1] = uly
        if ulx+width>self.bbox[2]: self.bbox[2] = ulx+width
        if uly+height>self.bbox[3]: self.bbox[3] = uly+height

        # set color
        self.ctx.set_source_rgba(*outline)
        # build a path for a rectangle with 5 pixels padding
        self.ctx.rectangle( ulx, uly, width, height)
        self.ctx.set_line_width(4)
        # the draw the rectangle out line
        self.ctx.stroke()

        if macro:
            # draw outter box
            self.ctx.set_source_rgba(*outline)
            # build a path for a rectangle with 5 pixels padding
            self.ctx.rectangle( ulx+8, uly+8, width-16, height-16)
            self.ctx.set_line_width(4)
            # the draw the rectangle out line
            self.ctx.stroke()


    def roundedRectangle(self, x, y, width, height):
        ctx = self.ctx
        aspect = width / height       # aspect ratio
        corner_radius = height / 5.0 # and corner curvature radius

        radius = corner_radius / aspect
        degrees = pi / 180.0

        ctx.new_sub_path()
        ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)

        ctx.close_path()


    def roundedRectangleEdge(self, x, y, width, height, thickness=4):
        ctx = self.ctx
        aspect = width / height       # aspect ratio
        corner_radius = height / 5.0 # and corner curvature radius

        radius = corner_radius / aspect
        degrees = pi / 180.0

        ctx.new_sub_path()
        ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)

        x += thickness
        y += thickness
        width -= 2*thickness
        height -= 2*thickness
        aspect = width / float(height) # aspect ratio
        corner_radius = height / 5.0 # and corner curvature radius

        radius = corner_radius / aspect
        degrees = pi / 180.0

        ctx.new_sub_path()
        ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)

        ctx.close_path()


    def draw3DFrame(self, x, y, width, height, outline, fill, thickness):
        ctx = self.ctx
        ctx.new_path()

        # first 2 rectangles (ramp going up of width thickness)
        self.roundedRectangleEdge(x, y, width, height, thickness)
        size = max(width, height)/2
        cx = width/2
        cy = height/2
        pat = cairo.LinearGradient(cx-size, cy-size, cx+size, cy+size)
        pat.add_color_stop_rgba(0, *outline) 
        pat.add_color_stop_rgba(1, 0.2, 0.2, 0.2, 1)
        ctx.set_source(pat)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.fill()
        #ctx.set_source_rgb(0,0,0)
        #ctx.stroke()
        thick2 = 2*thickness
        thick3 = 3*thickness
        thick4 = 4*thickness
        thick6 = 6*thickness

        # second set of 2 rectangles flat color (top of ridge) of witdh thickness
        self.roundedRectangleEdge(x+thickness, y+thickness, width-thick2, height-thick2, thickness)
        ctx.set_source_rgb( outline[0]-0.01, outline[1]+0.01, outline[2] )
        ctx.fill()

        # third set of 2 rectangles flat color (top of ridge)
        self.roundedRectangleEdge(x+thick2, y+thick2, width-thick4, height-thick4, thickness)
        pat = cairo.LinearGradient(cx-size, cy-size, cx+size, cy+size)
        pat.add_color_stop_rgba(1, *outline)
        pat.add_color_stop_rgba(0,  0.2, 0.2, 0.2, 1)
        ctx.set_source(pat)
        ctx.fill()

        # add fill
        self.roundedRectangle(x+thick3, y+thick3, width-thick6, height-thick6)
        #ctx.set_source_rgba(0,0,0,1)
        #ctx.stroke()
        ctx.set_source_rgba(*fill)
        ctx.fill()

    def getPilImage(self):
        buf = self.surface.get_data()
        width = self.width+2*self.border
        height = self.height+2*self.border
        return Image.frombuffer('RGBA', (width, height), buf, 'raw',
                                'BGRA', 0, 1)


    def addDropShadow(self):
        image = self.getPilImage()
        return dropShadow(image)


    def makeCircleNodeImage(self, width, height, outline, fill, macro=False):
        self.width = int(width)
        self.height = int(height)
        # upper left corner of the box
        #self.ul = ulx, uly = self.size/2-width/2, self.size/2-height/2
        self.ul = ulx, uly = self.border, self.border
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width+2*self.border,
                                          self.height+2*self.border)
        self.ctx = cairo.Context (self.surface)

        self.ctx.save()
        self.ctx.translate(self.border+self.width/2., self.border+self.height/2)
        self.ctx.scale (self.width, self.height)
        #pat = cairo.RadialGradient (0.35, 0.3, 0.1,
        #                            0.5,  0.5, .8)
        #self.ctx.set_source (pat)
        #pat.add_color_stop_rgba (0, 1, 1, 1, 1)
        #pat.add_color_stop_rgba (1, 0, 0, 0, 1)
        self.ctx.arc (0., 0., (width-10)/(2*width), 0, 2*pi)
        self.ctx.set_line_width(.03)
        self.ctx.set_source_rgba(*outline)
        self.ctx.stroke()
        self.ctx.arc (0., 0., (width-15)/(2*width), 0, 2*pi)
        self.ctx.set_source_rgba(*fill)
        self.ctx.fill()
        self.ctx.restore()
        
        #self.drawSquareFlatBox(width, height, outline, fill, macro)
    
    def makeNodeImage(self, width, height, outline, fill, macro=False):

        self.width = int(width)
        self.height = int(height)
        #self.size = int(sqrt(self.width*self.width + self.height*self.height))
        # upper left corner of the box
        #self.ul = ulx, uly = self.size/2-width/2, self.size/2-height/2
        self.ul = ulx, uly = self.border, self.border
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width+2*self.border,
                                          self.height+2*self.border)
        self.ctx = cairo.Context (self.surface)

        #self.drawSquareFlatBox(width, height, outline, fill, macro)
        if macro:
            self.draw3DFrame(ulx, uly, self.width, self.height, outline, fill, 2)
        else:
            self.draw3DFrame(ulx, uly, self.width, self.height, outline, fill, 1.5)
            
        
    def drawIcon(self, filename):
        iconImage = cairo.ImageSurface.create_from_png(filename)
        imwidth = iconImage.get_width()
        imheight = iconImage.get_height()
        ulx, uly = self.ul[0]+5, self.ul[1]+5 # define upper left corner
        self.ctx.set_source_surface(iconImage, ulx, uly)
        self.ctx.rectangle(ulx, uly, ulx+imwidth, uly+imheight)
        self.ctx.fill()


    #def drawPort(self, ptype, x, y, size, vector, line, fill, outline, label, edge):
    def drawPort(self, ptype, x, y, descr):
        vector = descr.get('vector')
        # flip y as cairo origin is upper left corner
        vector = [vector[0], -vector[1]]
        size = descr.get('size', 10)
        fill = descr.get('fill', (1,1,1,1))
        line = descr.get('line', (0,0,0,1))
        outline = descr.get('outline', (0,0,0,1))
        label = descr.get('label', None)
        edge = descr['edge']
        
        # draw a Port
        # set color
        halfSize = size/2
        self.ctx.set_source_rgba(*fill)
        self.ctx.rectangle( x-halfSize, y-halfSize, size, size)
        self.ctx.fill()
        
        self.ctx.set_source_rgba(*outline)
        self.ctx.rectangle(  x-halfSize, y-halfSize, size, size)
        self.ctx.set_line_width(2)
        self.ctx.stroke()

        # update bbox
        if x-halfSize<self.bbox[0]: self.bbox[0] = x-halfSize
        if y-halfSize<self.bbox[1]: self.bbox[1] = y-halfSize
        if x+halfSize>self.bbox[2]: self.bbox[2] = x+halfSize
        if y+halfSize>self.bbox[3]: self.bbox[3] = y+halfSize

        # draw the arrow head
        if ptype=='in':
            vx, vy = -vector[0]*halfSize, -vector[1]*halfSize
        else:
            vx, vy = vector[0]*halfSize, vector[1]*halfSize
        px, py = -vy*.5, vx*.5 # orthogonal vector
        self.ctx.set_source_rgba(*line)
        self.ctx.set_line_width(4)
        self.ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
        self.ctx.move_to(x-vx*.5-px, y-vy*.5-py)
        self.ctx.line_to(x+vx*.8, y+vy*.8) #arrow tip
        self.ctx.line_to(x-vx*.5+px, y-vy*.5+py)
        self.ctx.stroke()

        # draw the arrow line
        self.ctx.set_line_width(1)
        self.ctx.move_to(x+vx, y+vy)
        self.ctx.line_to(x-vx, y-vy)
        self.ctx.stroke()

        # draw port name
        if label:
            self.ctx.set_source_rgb(0, 0, 0)
            self.ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                                      cairo.FONT_WEIGHT_NORMAL)
            self.ctx.set_font_size(10.)
            x_bearing, y_bearing, width, height = self.ctx.text_extents(label)[:4]
            if edge=='top':
                self.ctx.move_to( x - width/2, y + halfSize + 4 + height)
            elif edge=='bottom':
                self.ctx.move_to( x - width/2, y - halfSize - 4 )
            elif edge=='left':
                self.ctx.move_to( x + halfSize + 4, y + height/2.)
            elif edge=='right':
                self.ctx.move_to( x - width - x_bearing - 10, y + height/2.)
            self.ctx.show_text(label)


    def drawLabel(self, label, padding):
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(18.)
        x_bearing, y_bearing, width, height = self.ctx.text_extents(label)[:4]
        cx = self.border + padding['left'] + (self.width-padding['left']-padding['right'])/2
        cy = self.border + padding['top'] + (self.height-padding['top']-padding['bottom'])/2
        self.ctx.move_to(cx - width/2 - x_bearing, cy-height/2 - y_bearing)
        self.ctx.show_text(label)


    def getLabelSize(self, label, font='Sans', size=18,
                     slant=cairo.FONT_SLANT_NORMAL,
                     weight=cairo.FONT_WEIGHT_BOLD):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 800)
        ctx = cairo.Context(surface)
        ctx.select_font_face(font, slant, weight)
        ctx.set_font_size(size)
        x_bearing, y_bearing, width, height = ctx.text_extents(label)[:4]
        return x_bearing, y_bearing, width, height


#ctx.scale (WIDTH, HEIGHT) # Normalizing the canvas
## pat = cairo.LinearGradient (0.0, 0.0, 0.0, 1.0)
## pat.add_color_stop_rgba (1, 0.7, 0, 0, 0.5) # First stop, 50% opacity
## pat.add_color_stop_rgba (0, 0.9, 0.7, 0.2, 1) # Last stop, 100% opacity

## ctx.rectangle (0, 0, 1, 1) # Rectangle(x0, y0, x1, y1)
## ctx.set_source (pat)
## ctx.fill ()

## ctx.translate (0.1, 0.1) # Changing the current transformation matrix

## ctx.move_to (0, 0)
## ctx.arc (0.2, 0.1, 0.1, -math.pi/2, 0) # Arc(cx, cy, radius, start_angle, stop_angle)
## ctx.line_to (0.5, 0.1) # Line to (x,y)
## ctx.curve_to (0.5, 0.2, 0.5, 0.4, 0.2, 0.8) # Curve(x1, y1, x2, y2, x3, y3)
## ctx.close_path ()

## ctx.set_source_rgb (0.3, 0.2, 0.5) # Solid color
## ctx.set_line_width (0.02)
## ctx.stroke ()
## fill = (0.82, 0.88, 0.95, 0.5)
## line = (0.28, 0.45, 0.6, 1.)

## from math import pi
## renderer = CairoNodeRenderer()
## renderer.makeNodeImage(200, 100, line, fill)
## ulx, uly = renderer.ul
## renderer.drawPort(ulx+60, uly, 'input', line, (1,1,1,1))
## renderer.drawPort(ulx+120, uly, 'output', line, (1,1,1,1))
## renderer.drawPort(ulx+60, uly+100, 'output', line, (1,1,1,1))
## renderer.drawPort(ulx+120, uly+100, 'input', line, (1,1,1,1))
## renderer.drawLabel('Node 1')
## renderer.surface.write_to_png ("node1.png") # Output to PNG
