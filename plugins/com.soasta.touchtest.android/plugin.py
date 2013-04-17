#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, subprocess, hashlib, time, shutil, zipfile
from time import sleep

def compile(c):
    global project_dir
    global builder
    global android
    global config
    global template_dir
    global jar_dir
    global restore_performed
    global classpath_separator
    
    print "[DEBUG] TouchTest : %s" % c
    
    config = c
    
    if config['platform'] == 'android':
        from android import Android
        from compiler import Compiler
      
        # Initialize variables
        project_dir = config['project_dir']
        template_dir = config['template_dir']
        jar_dir = project_dir + "/plugins/com.soasta.touchtest.android/lib/"
            
        # Initialize the restore_performed value to be False
        restore_performed = False
        
        # Initialize classpath
        builder = config['android_builder']
        android = Android(builder.name, builder.app_id, builder.sdk, 'test', builder.java)
        full_resource_dir = os.path.join(builder.project_dir, builder.project_dir + "/bin/assets/Resources")
        compiler = Compiler(config['tiapp'],
            full_resource_dir,
            builder.java,
            project_dir + "/bin/Classes",
            builder.project_gen_dir,
            project_dir,
            include_all_modules=True)
        classpath = os.pathsep.join([builder.sdk.get_android_jar(), os.pathsep.join(compiler.jar_libraries)])
      
        # Classpath separator on Windows is a semi-colon instead of a colon
        classpath_separator = ":"
        if (os.name == 'nt'):
       	    classpath_separator = ";"

        classpath = classpath + classpath_separator + jar_dir + "aspectjrt.jar"
        classpath = classpath + classpath_separator + jar_dir + "aspectjtools.jar"

        print "[INFO] TouchTest : Installing TouchTest Driver for Android"
            
        print "[DEBUG] TouchTest : Preparing libraries"
        print "[DEBUG] TouchTest : Using classpath %s" % classpath
      
        createBackup("titanium")
        createBackup("modules/titanium-ui")
        
        step = 0
        try:
          step = 1
          instrument(classpath, "titanium")
          step = 2
          instrument(classpath, "modules/titanium-ui")
          step = 3
          merge()

          print "[INFO] TouchTest : TouchTest Driver for Android installed"

        except:
          print "[ERROR] TouchTest : Unexpected error:", sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2], "- step ", str(step)
          print "[ERROR] TouchTest : Exception occured. Restoring Titanium jar files."
          restore("titanium")
          restore("modules/titanium-ui")
          print "[ERROR] TouchTest : TouchTest Driver was not installed."

def postbuild():
    
    finalize()

                
def finalize():
    global restore_performed
    
    if config['platform'] == 'android' and restore_performed == False:
         
        print "[DEBUG] TouchTest : Restoring files changed during build."
        restore("titanium")
        restore("modules/titanium-ui")
        restore_performed = True
        print "[INFO] TouchTest : The application is now TouchTest ready."

def createBackup(jar):

    jar_file = template_dir + "/" + jar + ".jar"
    jar_bak_file = jar_file + ".bak"
    
    if not os.path.exists(jar_bak_file):
      print "[DEBUG] TouchTest: Creating backup of file: {file}".format(file=jar_file)
      shutil.copy(jar_file, jar_bak_file)
    else:
      print "[DEBUG] TouchTest: Backpup already present: {file}".format(file=jar_file)
      shutil.copy(jar_file + ".bak", jar_file)
      
def restore(jar):
  
    jar_file = template_dir + "/" + jar + ".jar"
  
    print "[DEBUG] TouchTest: Restoring file: {file}".format(file=jar_file)
    shutil.copy(jar_file + ".bak", jar_file)
    os.remove(jar_file + ".bak")

def instrument(classpath, jar):

    if not os.path.exists(template_dir + "/touchtest/"):
        os.makedirs(template_dir + "/touchtest/")     
            
    inpath = template_dir + "/" + jar + ".jar.bak"
    print "[DEBUG] TouchTest : Process %s " % inpath
    aspectpath = jar_dir + "TouchTestDriver.jar" + classpath_separator + jar_dir + "TouchTestDriver-Titanium.jar"
    outjar = template_dir + "/" + jar + ".jar"
    
    if os.path.exists(outjar):
        os.remove(outjar)
    
    param = "-Xlint:ignore -inpath \"" + inpath + "\" -aspectpath \"" + aspectpath + "\" -outjar \"" + outjar + "\" -cp \"" + classpath + "\""
    
    # Weave aspects into jar files
    ajc = [];
    ajc.append("java")
    ajc.append("-classpath")
    ajc.append(classpath)
    ajc.append("-Xmx64M")
    ajc.append("org.aspectj.tools.ajc.Main")
    ajc.append("-Xlint:ignore")
    ajc.append("-inpath")
    ajc.append(inpath)
    ajc.append("-aspectpath")
    ajc.append(aspectpath)
    ajc.append("-outjar")
    ajc.append(outjar)
    print "[DEBUG] TouchTest :   Using %s " % param
    sys.stdout.flush()
    subprocess.call(ajc)
    print "[DEBUG] TouchTest : %s processed" % inpath
    
def mergeAll(jars, targetjar):
    
    # Create the new tnp JAR
    tmpjar = targetjar + ".tmp"
    if os.path.exists(tmpjar):
      os.remove(tmpjar)    
    with zipfile.ZipFile(tmpjar, mode='a') as zMerged:
      for fname in jars:
        zf = zipfile.ZipFile(fname, 'r')
        for n in zf.namelist():
            zMerged.writestr(n, zf.open(n).read())

    if os.path.exists(targetjar):
      # Remove the target JAR
      os.remove(targetjar)    
      
    # Rename to tmp JAR to target JAR
    shutil.move(tmpjar, targetjar)
    
def merge():
    
    print "[DEBUG] TouchTest : Add TouchTest capabilities in %s" % template_dir + "/titanium.jar"
    
    mergeAll([template_dir + "/titanium.jar",
              jar_dir + "aspectjrt.jar",
              jar_dir + "TouchTestDriver-APIv12.jar",
              jar_dir + "TouchTestDriver-APIv11.jar",
              jar_dir + "TouchTestDriver-Titanium.jar",
              jar_dir + "TouchTestDriver.jar"],
             template_dir + "/titanium.jar")
