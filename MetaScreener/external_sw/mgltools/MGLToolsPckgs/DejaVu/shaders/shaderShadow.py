# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 16:41:32 2014

@author: ludo
"""
header = """
varying vec4 vWorldPosition;
varying vec3 normal;
varying vec4 coord;
varying vec4 shadowDir;
uniform sampler2D shadowMap;
uniform vec2 shadowMapSize;
uniform vec3 LightSourcePos;
uniform mat4 camModel;
uniform mat4 lightProj;
uniform mat4 lightView; 
uniform mat4 lightRot;
uniform float lightNear;
uniform float lightFar;
#define PI 3.14159265

"""

common="""
bool outside(in vec2 point) 
{
    return ( 
	point.x > 1. || point.x < 0.|| 
	point.y > 1. || point.y < 0.
    ) ;
}
"""

simple_shadow="""
float getShadow(){
    vec3 texCoords;
    vec3 shadowDir_ndc = shadowDir.xyz/shadowDir.w;
    texCoords.xy = shadowDir_ndc.xy * 0.5 + 0.5;
    texCoords.z = shadowDir_ndc.z * 0.5 + 0.5;

    float val =texture2D(shadowMap,texCoords.xy).z;// 1.0-(texCoords.z-texture2D(shadowMap,texCoords.xy).x);
    texCoords.z+= 0.0005;
	 float shadow = 1.0;
	 if (shadowDir.w > 0.0){
	 		shadow = val < texCoords.z ? 0.5 : 1.0 ;
    }
    return shadow;
}"""

simple_lighting="""
vec4 lighting_simple(){
   vec3 worldNormal = normalize(normal); 
   vec3 L = normalize(LightSourcePos.xyz - coord.xyz);   
   vec3 E = normalize(-coord.xyz); // we are in Eye Coordinates, so EyePos is (0,0,0)  
   vec3 R = normalize(-reflect(L,worldNormal.xyz));  
 
   //calculate Ambient Term:  
   vec4 Iamb = gl_FrontLightProduct[0].ambient;    

   //calculate Diffuse Term:  
   vec4 Idiff = gl_FrontLightProduct[0].diffuse*gl_Color * max(dot(worldNormal.xyz,L), 0.0);
   Idiff = clamp(Idiff, 0.0, 1.0);     
   
   // calculate Specular Term:
   vec4 Ispec = gl_FrontLightProduct[0].specular  * pow(max(dot(R,E),0.0),0.3*gl_FrontMaterial.shininess);
   Ispec = clamp(Ispec, 0.0, 1.0); 
   // write Total Color:  
   return gl_FrontLightModelProduct.sceneColor + Iamb + Idiff + Ispec; 
}
"""

adv_lighting="""
float attenuation(vec3 dir){
    float dist = length(dir);
    float radiance = 1.0/(1.0+pow(dist/10.0, 2.0));
    return clamp(radiance*10.0, 0.0, 1.0);
}

float influence(vec3 normal, float coneAngle){
    float minConeAngle = ((360.0-coneAngle-10.0)/360.0)*PI;
    float maxConeAngle = ((360.0-coneAngle)/360.0)*PI;
    return smoothstep(minConeAngle, maxConeAngle, acos(normal.z));
}

float lambert(vec3 surfaceNormal, vec3 lightDirNormal){
    //return max(0.0, dot(surfaceNormal, lightDirNormal));
    return max(dot(surfaceNormal,lightDirNormal), 0.0);
    ///return clamp(Idiff, 0.0, 1.0); 
}

vec3 skyLight(vec3 normal){
    return vec3(smoothstep(0.0, PI, PI-acos(normal.y)))*0.8;
}

vec3 gamma(vec3 color){
    return pow(color, vec3(2.2));
}
"""

pcf_function="""
#define PI 3.14159265
float texture2DCompare(sampler2D depths, vec2 uv, float compare){
    float depth = texture2D(depths, uv).r;
    return step(compare, depth);
}

float texture2DShadowLerp(sampler2D depths, vec2 size, vec2 uv, float compare){
    vec2 texelSize = vec2(1.0)/size;
    vec2 f = fract(uv*size+0.5);
    vec2 centroidUV = floor(uv*size+0.5)/size;

    float lb = texture2DCompare(depths, centroidUV+texelSize*vec2(0.0, 0.0), compare);
    float lt = texture2DCompare(depths, centroidUV+texelSize*vec2(0.0, 1.0), compare);
    float rb = texture2DCompare(depths, centroidUV+texelSize*vec2(1.0, 0.0), compare);
    float rt = texture2DCompare(depths, centroidUV+texelSize*vec2(1.0, 1.0), compare);
    float a = mix(lb, lt, f.y);
    float b = mix(rb, rt, f.y);
    float c = mix(a, b, f.x);
    return c;
}

float PCF(sampler2D depths, vec2 size, vec2 uv, float compare){
    float result = 0.0;
    for(int x=-1; x<=1; x++){
        for(int y=-1; y<=1; y++){
            vec2 off = vec2(x,y)/size;
            result += texture2DShadowLerp(depths, size, uv+off, compare);
        }
    }
    return result/9.0;
}
"""

#require 
ao_function="""
float scaleNearFar(in float val, in float near, in float far){
     float res = 0.0;
     res = (2.0*near) / (far + near - val* (far-near));
     //texCoords.z = ((far-near) * 0.5) * val + ((near+far) * 0.5);
     return res;
}

float readDepth(in vec2 coord, in sampler2D DepthTexture, in float near, in float far){
    //linearisation of depth but already done 
    vec4 val = texture2D(DepthTexture, coord );
    return scaleNearFar(val.x,near,far);//(2.0*near) / (far + near - val.x* (far-near));
    }

float compareDepths( in float depth1, in float depth2, in float near, in float far){
    float aorange = 60.0;
    float aoCap = 1.2;
    float depthTolerance = 0.0;
    float aoMultiplier=100.0;
    float diff = sqrt(clamp(1.0-(depth1-depth2) / (aorange/(far-near)),0.0,1.0));
    float ao = min(aoCap,max(0.0,depth1-depth2-depthTolerance) * aoMultiplier) * diff;
    //if (diff > 0.8) {ao = 0.0;}
    return ao;
    }

float computeAO(in vec2 scrCoord, in sampler2D DepthTexture, in vec2 size,in float near, in float far ){
    float depth = texture2D(DepthTexture, scrCoord ).z;//readDepth(scrCoord,DepthTexture,near,far);
    float d;
    float scale = 1.0;
    float aspect = size.x/size.y;
    float w = (1.0 / size.x)/clamp(depth,0.05,1.0)+0.001*scale;//+(noise.x*(1.0-noise.x));
    float h = (1.0 / size.y)/clamp(depth,0.05,1.0)+0.001*scale;//+(noise.y*(1.0-noise.y));	
    float pw;
    float ph;
    
    float ao;
    float s;
    int rings = 6;
    int samples = 6;
    int ringsamples;
    for (int i = 1; i <= rings; i += 1){   
        ringsamples = i * samples;   
        for (int j = 0 ; j < ringsamples ; j += 1)   {   
            float step = PI*2.0 / float(ringsamples);      
            pw = (cos(float(j)*step)*float(i));      
            ph = (sin(float(j)*step)*float(i))*aspect; 
            vec2 coord = vec2(scrCoord.s+pw*w,scrCoord.t+ph*h); //clamp(f, 0.0, 1.0);?   
            d = texture2D(DepthTexture, coord ).z;//readDepth( coord,DepthTexture,near,far);    
            if ( outside(coord) ) {ao+=0.0;}            
            else {ao += compareDepths(depth,d,near,far); }     
            s += 1.0;   
            }
        }
    ao /= s;
    ao = 1.0-ao;
    return ao;
    }
"""

vshadow=header+"""
void main(){
    //model transform
    vWorldPosition = lightRot *gl_Vertex;
    normal = normalize(gl_NormalMatrix * gl_Normal);
    //model-view transform
    coord =  gl_ModelViewMatrix * gl_Vertex;//is this working ?gl_TextureMatrix[7]
    gl_FrontColor = gl_Color;
    //light transform PVM
    shadowDir = lightProj * lightView *  lightRot * gl_Vertex;// * gl_ModelViewMatrix - vec4(LightSourcePos, 1.0);
    //Camera transform PVM    
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;//lightProj * lightView * lightRot * gl_Vertex;//gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""
fshadow=header + simple_shadow + simple_lighting + """
void main(){
    //test ao ?
    //vec3 texCoords;
    //vec3 shadowDir_ndc = shadowDir.xyz/shadowDir.w;
    //texCoords.xy = (1.0+shadowDir_ndc.xy) / 2.0;//shadowDir_ndc.xy * 0.5 + 0.5;
    //texCoords.z = shadowDir_ndc.z * 0.5 + 0.5;
    //float ao = computeAO(texCoords.xy,shadowMap,shadowMapSize,lightNear,lightFar);
    //ao = clamp(ao,0.0,1.0);
    gl_FragColor = getShadow()*lighting_simple();//vec4(lightUV.z,0.0,0.0,1.0);////illuminated*lighting_simple();//vec4(gamma(lighting_simple().rgb), 1.0);//illuminated*lighting_simple();//gl_Color;//vec4(gamma(excident), 1.0);
}
"""

pcf_fshadow=header + pcf_function + adv_lighting + """
void main(){
    vec3 texCoords;
    vec3 shadowDir_ndc = shadowDir.xyz/shadowDir.w;
    texCoords.xy = (1.0+shadowDir_ndc.xy) / 2.0;//shadowDir_ndc.xy * 0.5 + 0.5;
    texCoords.z = shadowDir_ndc.z * 0.5 + 0.5;
    vec4 worldNormal = vec4(normalize(normal),1.0);
    // shadow calculation
    float bias = 0.001;
    float lightDepth2 = clamp(texCoords.z, 0.0, 1.0)-bias;//1.0?/40.0
    float illuminated = PCF(shadowMap, shadowMapSize, texCoords.xy, lightDepth2);
    //shading
    //vec3 lightPos = LightSourcePos.xyz;//(lightView * vWorldPosition).xyz;//vpos in light mvp vWorldPosition
    //vec3 lightPosNormal = normalize(lightPos);
    //vec3 lightSurfaceNormal = worldNormal.xyz;// (lightRot * worldNormal).xyz;

    vec3 lightPosNormal = normalize(LightSourcePos.xyz - coord.xyz);   
    vec3 E = normalize(-coord.xyz); // we are in Eye Coordinates, so EyePos is (0,0,0)  
    vec3 lightSurfaceNormal = normalize(-reflect(lightPosNormal,worldNormal.xyz));  

    vec3 excident = (
        skyLight(worldNormal.xyz)*gl_Color.rgb +
        gl_FrontLightProduct[0].diffuse.rgb * lambert(worldNormal.xyz, lightPosNormal) *
        //influence(E, 10.0) *
        attenuation(LightSourcePos.xyz) *
        illuminated
    );
    //final color
    gl_FragColor = vec4(excident, 1.0);//vec4(gamma(excident), 1.0);//illuminated*lighting_simple();
}
"""

frag_display_shadow="""
varying vec4 vWorldPosition;
varying vec3 normal;
varying vec4 coord;
varying vec4 shadowDir;
uniform mat4 camModel;
uniform mat4 lightProj;
uniform mat4 lightView; 
uniform mat4 lightRot;
uniform float lightNear;
uniform float lightFar;
uniform sampler2D shadowMap;
uniform vec2 shadowMapSize;
uniform vec3 LightSourcePos;

#define PI 3.14159265
float scaleNearFar(in float val, in float near, in float far){
     float res = 0.0;
     res = (2.0*near) / (far + near - val* (far-near));
     //texCoords.z = ((far-near) * 0.5) * val + ((near+far) * 0.5);
     return res;
}

float texture2DCompare(sampler2D depths, vec2 uv, float compare){
    float depth = texture2D(depths, uv).r;
    return step(compare, scaleNearFar(depth,lightNear,lightFar));
}

float texture2DShadowLerp(sampler2D depths, vec2 size, vec2 uv, float compare){
    vec2 texelSize = vec2(1.0)/size;
    vec2 f = fract(uv*size+0.5);
    vec2 centroidUV = floor(uv*size+0.5)/size;

    float lb = texture2DCompare(depths, centroidUV+texelSize*vec2(0.0, 0.0), compare);
    float lt = texture2DCompare(depths, centroidUV+texelSize*vec2(0.0, 1.0), compare);
    float rb = texture2DCompare(depths, centroidUV+texelSize*vec2(1.0, 0.0), compare);
    float rt = texture2DCompare(depths, centroidUV+texelSize*vec2(1.0, 1.0), compare);
    float a = mix(lb, lt, f.y);
    float b = mix(rb, rt, f.y);
    float c = mix(a, b, f.x);
    return c;
}

float PCF(sampler2D depths, vec2 size, vec2 uv, float compare){
    float result = 0.0;
    for(int x=-1; x<=1; x++){
        for(int y=-1; y<=1; y++){
            vec2 off = vec2(x,y)/size;
            result += texture2DShadowLerp(depths, size, uv+off, compare);
        }
    }
    return result/9.0;
}

float attenuation(vec3 dir){
    float dist = length(dir);
    float radiance = 1.0/(1.0+pow(dist/10.0, 2.0));
    return clamp(radiance*10.0, 0.0, 1.0);
}

float influence(vec3 normal, float coneAngle){
    float minConeAngle = ((360.0-coneAngle-10.0)/360.0)*PI;
    float maxConeAngle = ((360.0-coneAngle)/360.0)*PI;
    return smoothstep(minConeAngle, maxConeAngle, acos(normal.z));
}

float lambert(vec3 surfaceNormal, vec3 lightDirNormal){
    return max(0.0, dot(surfaceNormal, lightDirNormal));
}

vec3 skyLight(vec3 normal){
    return vec3(smoothstep(0.0, PI, PI-acos(normal.y)))*0.4;
}

vec3 gamma(vec3 color){
    return pow(color, vec3(2.2));
}


void main(){
    vec3 ndc_space_values = coord.xyz / coord.w;
    vec3 texCoords;
    vec3 shadowDir_ndc = shadowDir.xyz/shadowDir.w;
    texCoords.xy = shadowDir_ndc.xy * 0.5 + 0.5;
    texCoords.z = shadowDir_ndc.z * 0.5 + 0.5;
    vec4 worldNormal = vec4(normalize(normal),1.0);
    vec3 realShadowMapPosition = (coord.xyz/coord.w);//*0.5+0.5;
    //vec3 new_coord = coord.xyz/coord.w;
    // Add an offset to prevent self-shadowing and moiré pattern
    //realShadowMapPosition.z += 0.0005;
    //vec2 mult=vec2(coord.x*float(shadowMapSize.x),coord.y*float(shadowMapSize.y))*0.5+0.5;
    vec2 uv = realShadowMapPosition.xy;
    //floor(uv*size+0.5)/size;
    float depthSm = texture2D(shadowMap, floor(uv*shadowMapSize+0.5)/shadowMapSize).r;
    depthSm = scaleNearFar(depthSm,lightNear,lightFar);
    vec3 L = (LightSourcePos.xyz - vWorldPosition.xyz);
    vec3 lightPos = (lightView * vWorldPosition).xyz;//vpos in light mvp vWorldPosition
    vec3 lightPosNormal = normalize(lightPos);
    vec3 lightSurfaceNormal = worldNormal.xyz;// (lightRot * worldNormal).xyz;
    vec4 lightDevice = lightProj * vec4(lightPos, 1.0);
    vec2 lightDeviceNormal = lightDevice.xy/lightDevice.w;
    vec2 lightUV = texCoords.xy;//realShadowMapPosition.xy;///shadowMapSize;//*0.5+0.5;
    //lightDevice = lightRot * lightView * lightProj * vWorldPosition;
    //lightDeviceNormal = lightDevice.xy/lightDevice.w;
    lightUV = lightDeviceNormal*0.5+0.5;
    // shadow calculation
    float bias = 0.001;
    float lightDepth2 = clamp(length(lightPos), 0.0, 1.0)-bias;//1.0?/40.0
    float illuminated = PCF(shadowMap, shadowMapSize, lightUV, lightDepth2);
    vec3 excident = (
        skyLight(worldNormal.xyz) +
        lambert(lightSurfaceNormal, -lightPosNormal) *
        influence(lightPosNormal, 55.0) *
        attenuation(lightPos) *
        illuminated
    );
    //float near = 0.1;
    //float far = 200.0;    
    //vec2 coord = ((lightProj * lightView * vWorldPosition ).xy/shadowMapSize)*0.5+0.5;//(lightPos.xy/shadowMapSize)*0.5+0.5;
    //vec2 centroidUV = floor(coord.xy*shadowMapSize+0.5)/shadowMapSize;
    //floor(uv*size+0.5)/size;
    vec2 centroidUV =floor(texCoords.xy*shadowMapSize+0.5)/shadowMapSize;
    uv  =  floor((( coord/coord.w )*0.5+0.5).xy*shadowMapSize+0.5)/shadowMapSize;
    float val =texture2D(shadowMap,texCoords.xy).z;// 1.0-(texCoords.z-texture2D(shadowMap,texCoords.xy).x);
    //val=scaleNearFar(val,lightNear,lightFar);
    //float depth =  val;//scaleNearFar(val,lightNear,lightFar);//( coord/coord.w ).z+0.0005;//(2.0*near) / (far + near - val* (far-near));
    vec4 col =lighting_simple();
    //float realDpeth = realShadowMapPosition.z;
    //realDpeth =scaleNearFar(realDpeth,lightNear,lightFar*2.0);
    //texCoords.z = ((f-n) * 0.5) * ndc_space_values.z + ((n+f) * 0.5);
    //if (depthSm < realDpeth-0.0001)
    //{
    //   col == vec4(0, 0, 0, 1);     
    //}
    texCoords.z+= 0.0003;
	 float shadow = 1.0;
	 if (shadowDir.w > 0.0){
	 		shadow = val < texCoords.z ? 0.5 : 1.0 ;
    }
    //gl_FragColor = vec4(texCoords.xy,0.0,1.0);//texture2D(shadowMap,texCoords.xy );//vec4 (texCoords.x,0.0,0.0,1.0);
    //float frag_depth = length(shadowDir.xyz/shadowDir.w);
    //vec3 norm_shadowDir = normalize(shadowDir).xyz;  
    //float shadow_map_depth = texture2D(shadowMap, norm_shadowDir.xy).r; 
    //val = frag_depth;     
    //gl_FragColor = vec4(val,val,val,1.0)*gl_Color;//ndc_space_values.z);
    //gl_FragColor = vec4(gamma(excident), 1.0);// w ?
    gl_FragColor = shadow*lighting_simple();//vec4(lightUV.z,0.0,0.0,1.0);////illuminated*lighting_simple();//vec4(gamma(lighting_simple().rgb), 1.0);//illuminated*lighting_simple();//gl_Color;//vec4(gamma(excident), 1.0);
}
"""
