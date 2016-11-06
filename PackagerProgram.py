#!/usr/bin/env python2
from PyQt4 import QtGui, QtCore
from distutils.dir_util import copy_tree
import sys
import os
import interface
import json
import shutil
import csv
import sys
import getpass
import subprocess
from subprocess import Popen
from subprocess import check_output
from itertools import islice


global inpDirLoc
global outDirLoc
global SIPJARLoc
global MDFileLoc

inpDirLoc = ""
outDirLoc = ""
SIPJARLoc = ""
MDFileLoc = ""



from os.path import expanduser
spath = os.path.join(expanduser("~"),'DiskImagePackager','settings.json')

#print spath

class packagerMain(QtGui.QMainWindow, interface.Ui_DiskImagePackager):

  def __init__(self, parent=None):
    #don't really understand global variables well enough, but I think I need to put these here
    global inpDirLoc
    
    global outDirLoc
    
    global SIPJARLoc
    global MDFileLoc
    # start the whole gui thing
    super(packagerMain, self).__init__(parent)
    self.setupUi(self)	
    # Check for existence of settings file for local user. If it doesn't
    # exist (e.g. on first use) warn and create)

    if not os.path.exists(spath):
      QtGui.QMessageBox.warning(self,"First run notice","It looks like you're running the program for the first time as this user. I'm creating a new default settings file for you in " + spath,QtGui.QMessageBox.Ok,QtGui.QMessageBox.NoButton,QtGui.QMessageBox.NoButton)
      os.mkdir(os.path.join(expanduser("~"),'DiskImagePackager'))
      sfile = open(spath, 'w+')
      sfile.write('{"inputFolder":"C:\Users\Euan\Box Sync\Digital Preservation System\Workflows\DigitalAccessioning\TestData","outputFolder":"C:\Users\Euan\Box Sync\Digital Preservation System\Workflows\DigitalAccessioning\TestOutputFolder","metadataFile":"C:\Users\Euan\Box Sync\Digital Preservation System\Workflows\DigitalAccessioning\ExampleSheet.csv","SIPJARFile":"C:\Preservica\Local\Sip Creator\configuration\org.eclipse.osgi\bundles\2\1\.cp\lib\dist\sdb-xipbuilder-5.5.1.jar"}')
      sfile.close()

    #open the settings.json file for reading
    if os.stat(spath).st_size != 0:
      with open(spath) as settings_file:    
      
    #set main settings to values from settings json file
        settings = json.load(settings_file)
        #print settings
 
        inpDirLoc = settings["inputFolder"]
        #print inpDirLoc
        self.inputFolderText.setText(inpDirLoc)
        outDirLoc = settings["outputFolder"]
        self.outputFolderText.setText(outDirLoc)
        MDFileLoc = settings["metadataFile"]
        self.MDFileText.setText(MDFileLoc)
        SIPJARLoc = settings["SIPJARFile"]
        self.SIPJarText.setText(SIPJARLoc)
    

  def chooseInputFolder(self):
    inpDirLoc = QtGui.QFileDialog.getExistingDirectory(self,"Select an Output folder") + "\\"
    inpDirLoc = str(inpDirLoc)
    self.inputFolderText.setText(inpDirLoc)

    if os.stat(spath).st_size != 0:
# if it is not empty open it for reading
      with open(spath,'r') as settings_file: 
        settings = json.load(settings_file)
        settings["inputFolder"] = inpDirLoc
        jsoutput = json.dumps(settings)
        outfile = open(spath, 'w')
        outfile.write(jsoutput)
        outfile.close()
	
  def chooseOutputFolder(self):
    global outDirLoc
    outDirLoc = QtGui.QFileDialog.getExistingDirectory(self,"Select an Output folder") + "\\"
    outDirLoc = str(outDirLoc)
    self.outputFolderText.setText(outDirLoc)

    if os.stat(spath).st_size != 0:
# if it is not empty open it for reading
      with open(spath,'r') as settings_file: 
        settings = json.load(settings_file)
        settings["outputFolder"] = outDirLoc
        jsoutput = json.dumps(settings)
        outfile = open(spath, 'w')
        outfile.write(jsoutput)
        outfile.close()
	
  def chooseMetadataFile(self):
    MDFileLoc = QtGui.QFileDialog.getOpenFileName(self, 'Choose Metadata File file location')
    MDFileLoc = str(MDFileLoc).replace("\\","\\\\").replace("/","\\\\")
    self.MDFileText.setText(MDFileLoc)

    if os.stat(spath).st_size != 0:
# if it is not empty open it for reading
      with open(spath,'r') as settings_file: 
        settings = json.load(settings_file)
        settings["metadataFile"] = MDFileLoc
        jsoutput = json.dumps(settings)
        outfile = open(spath, 'w')
        outfile.write(jsoutput)
        outfile.close()
	
  def chooseSIPJARFile(self):
    SIPJARLoc = QtGui.QFileDialog.getOpenFileName(self, 'Choose SIP Creator JAR file location')
    SIPJARLoc = str(SIPJARLoc)
    self.SIPJarText.setText(SIPJARLoc)
    
    if os.stat(spath).st_size != 0:
# if it is not empty open it for reading
      with open(spath,'r') as settings_file: 
        settings = json.load(settings_file)
        settings["SIPJARFile"] = SIPJARLoc
        jsoutput = json.dumps(settings)
        outfile = open(spath, 'w')
        outfile.write(jsoutput)
        outfile.close()
	
  def startPackaging(self):
    global MDFileLoc
    commands = []
    source_dirname = inpDirLoc
    dest_dir = outDirLoc
    # check the input folder and find all sub directories
    for dir in os.listdir(source_dirname):

    # rename the content directory to have the CUID at the start
      try:
        os.stat(os.path.join(inpDirLoc,dir,dir + "_Content"))
      except:
        os.rename(os.path.join(inpDirLoc,dir,"Content"), os.path.join(inpDirLoc,dir, dir + "_Content"))
    #rename the metadata directory to include CUID also
      try:
        os.stat(os.path.join(inpDirLoc,dir,dir + "_Metadata"))
      except:
        os.rename(os.path.join(inpDirLoc,dir,"Metadata"), os.path.join(inpDirLoc,dir, dir + "_Metadata"))
    #create function to list only files in folder
      def files(path):
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                yield file
    #create variables to use to test whether to move disk images into image folder
      imageDir = os.path.join(inpDirLoc,dir,dir + "_Content","Image")
      contentDir = os.path.join(inpDirLoc,dir, dir + "_Content")
    #check to see if image directory exists and create it if not
      try:
        os.stat(imageDir)
      except:
        os.mkdir(imageDir)
        
    #move every file in the content directory to the content/image directory
      for file in files(contentDir):
       # print file 
        os.rename(os.path.join(contentDir,file), os.path.join(imageDir,file))
      presColCode = ""
      #print str(MDFileLoc)
      with open(MDFileLoc, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
          #print str(row[3])
          if str(row[3]) == str(dir):
            #print row[3] + ": " + row[1]
            presColCode = row[1]
# Create commands to run sip creator
# Start with the SIP for the content directory
      commands.append(("java -jar \"" + str(SIPJARLoc).replace("\\","\\\\").replace("/","\\\\") + "\" -input \"" + str(os.path.join(inpDirLoc, dir,dir + "_Content")).replace("\\","\\\\").replace("/","\\\\") + "\\\\\" -e -md5 -colcode \"" + presColCode + "\" -output \"" + str(outDirLoc).replace("\\","\\\\").replace("/","\\\\") + "\\\\\" -colcode \"/resources/5543#tree::archival_object_2207952\""))
# Now create the command for the SIP for the Metadata directory (with "-filedus" parameter included)	  
      commands.append(("java -jar \"" + str(SIPJARLoc).replace("\\","\\\\").replace("/","\\\\") + "\" -input \"" + str(os.path.join(inpDirLoc, dir,dir + "_Metadata")).replace("\\","\\\\").replace("/","\\\\") + "\\\\\" -e -md5 -colcode \"" + presColCode + "\" -output \"" + str(outDirLoc).replace("\\","\\\\").replace("/","\\\\") + "\\\\\" -filedus -colcode \"/resources/5543#tree::archival_object_2207952\""))



    # Now run the commands in paralell
    # set max concurrent instances from feild in gui -- not implemented yet
    max_workers = 2   #int(self.DTCInstances.text())  
    
    processes = (Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for cmd in commands)
  
    running_processes = list(islice(processes, max_workers))  
    while running_processes:
      results = []
      for i, process in enumerate(running_processes):
        results.append("\"" + str(process) + "\"")
        out, err = process.communicate()
        if process.poll() is not None:  # the process has finished
          running_processes[i] = next(processes, None)  # start new process
          if running_processes[i] is None: # no new processes
            del running_processes[i]
            break
#update the text browser with the status
        
        
        results.append(str(out) + str(err))
# process the update to the gui
        QtGui.QApplication.processEvents()
        if process.poll() is not None:  # the process has finished
          running_processes[i] = next(processes, None)  # start new process
          if running_processes[i] is None: # no new processes
            del running_processes[i]
            break
      for result in results:
        self.progressBox.append(result)
# once finished put a message to say it is all finished
    self.progressBox.append(" ")
    self.progressBox.append("------------------------------------------------")
    self.progressBox.append("Creation of packages complete")
    self.progressBox.append("------------------------------------------------")
			
			
  def saveLog(self):
     # get file path from user input browsing
    saveLogPath = QtGui.QFileDialog.getSaveFileName(self,'Choose save file location',str(outDirLoc),selectedFilter='*.txt')
    #make file extension .txt if not already
    if str(saveLogPath)[-4:] != '.txt':
      saveLogPath = saveLogPath + ".txt"
    #assing textbrowser contents to a variable and write it to the file selected above
    progressBox = self.progressBox.toPlainText()
    outfile = open(saveLogPath, 'w')
    outfile.write(progressBox)
    outfile.close()
  
  def closeProgram(self):
    QtCore.QCoreApplication.instance().quit()


def main():
    app = QtGui.QApplication(sys.argv)
    form = packagerMain()
    form.show()
    app.exec_()
  

	

if __name__ == '__main__':
    main()
