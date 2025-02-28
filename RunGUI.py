import sys
import RandomizerGUI
import time
import yaml
import json
import random
import string
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QInputDialog
import RunCustomRandomizationAssumedFill as RunCustomRandomization
from shutil import copyfile
from collections import OrderedDict
import traceback
import hashlib
import csv
import os

class RunWindow(QtWidgets.QMainWindow, RandomizerGUI.Ui_MainWindow):
	def __init__(self, parent=None):
		super(RunWindow, self).__init__(parent)
		self.setupUi(self)
		_translate = QtCore.QCoreApplication.translate
		yamlfile = open('RandomizerConfig.yml')
		yamltext = yaml.load(yamlfile)
		self.loadSettings(yamltext['DefaultSettings'])
		self.modifierList.itemSelectionChanged.connect(self.updateModifierDescription)
		self.ChooseSettings.clicked.connect(self.selectLogicSettings)
		self.LoadModifier.clicked.connect(self.loadModifier)
		self.DeleteModifier.clicked.connect(self.deleteModifier)
		self.romPath = ''
		self.SelectRomFile.clicked.connect(self.selectRom)
		self.Randomize.setEnabled(False)
		self.Randomize.setText(_translate("MainWindow", "No Rom Loaded!"))
		self.Randomize.clicked.connect(self.runRandomizer)
		self.SaveSettings.clicked.connect(self.saveSettings)
		self.PlandoMode = False
		self.PlandoData = {}
		self.LoadPlandoFile.clicked.connect(self.SetUpPlando)
		self.TurnOffPlando.clicked.connect(self.DeactivatePlando)
		self.DefaultSettings.clicked.connect(self.SelectDefaultSettings)
		self.AddItem.clicked.connect(self.AddBonusItem)
		self.View_Items.clicked.connect(self.RemoveBonusItem)

		self.itemsList = []
		with open('AddItemValues.csv', newline='',encoding='utf-8-sig') as csvfile:
			reader = csv.reader(csvfile)
			for i in reader:
				if(len(i)>0):
					self.itemsList.append(i[0])
					#self.ItemList.addItem(i[0])

	def runRandomizer(self):
		os.environ['PYTHONHASHSEED'] = '0'#this needs to be reproducible! so this can't be random!
		rngSeed = str(time.time())
		random.seed(rngSeed)
		rngSeed = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
		if(self.SeedInput.text() != ''):
			rngSeed = self.SeedInput.text()
		rngSeedBytes = rngSeed.encode('utf-8')
		rSeed = int(hashlib.md5(rngSeedBytes).hexdigest(),16)
		print('numeric seed is: '+str(rSeed))
		random.seed(rSeed)
		_translate = QtCore.QCoreApplication.translate
		yamlfile = open(self.settings['BasePatch'])
		yamltext = yamlfile.read()
		patches = json.loads(yamltext)
		modFileList = self.settings['DefaultModifiers']
		try:
			tlv = 0
			wlv = 0
			self.Randomize.setEnabled(False)
			self.Randomize.setText(_translate("MainWindow", "Randomizing"))
			QtGui.QGuiApplication.processEvents()
			QtWidgets.QMessageBox.about(self, 'Message', 'Please select the name for the file. Make sure that you used a Speeedchoice V7.2 Rom as the base rom, or your game WILL crash.')
			validFileName = False

			base_dir = ""
			for i in range(0, len(self.romPath.split("/"))-1):
				if base_dir != "":
					base_dir+="/"
				base_dir += self.romPath.split("/")[i]

			while not validFileName:
				file = QFileDialog.getSaveFileName(directory = base_dir)[0]
				if file != '':
					validFileName = True
				else:
					QtWidgets.QMessageBox.about(self, 'ERROR', 'Please name and save the generated rom...')
			randomizedFileName = file

			if not randomizedFileName.endswith(".gbc"):
				randomizedFileName+=".gbc"

			copyfile(self.romPath, randomizedFileName)
			with open('SAVEDSEEDLOG.log','w') as f:
				f.write(rngSeed)
				
			if('ProgressItems' in self.settings):
				if 'CoreProgress' in self.settings:
					result = RunCustomRandomization.randomizeRom(randomizedFileName,self.settings['Goal'], rSeed, self.settings['FlagsSet'],patches, banList = self.settings['BannedLocations'], allowList = self.settings['AllowedLocations'], modifiers = self.modList,adjustTrainerLevels = False, adjustRegularWildLevels = False, adjustSpecialWildLevels = False, trainerLVBoost = tlv, wildLVBoost=wlv, requiredItems = self.settings['ProgressItems'],coreProgress = self.settings['CoreProgress'], otherSettings = self.settings, plandoPlacements = self.PlandoData)
				else:
					result = RunCustomRandomization.randomizeRom(randomizedFileName,self.settings['Goal'], rSeed, self.settings['FlagsSet'],patches, banList = self.settings['BannedLocations'], allowList = self.settings['AllowedLocations'], modifiers = self.modList,adjustTrainerLevels = False, adjustRegularWildLevels = False, adjustSpecialWildLevels = False, trainerLVBoost = tlv, wildLVBoost=wlv, requiredItems = self.settings['ProgressItems'], otherSettings = self.settings, plandoPlacements = self.PlandoData)
			else:
				if 'CoreProgress' in self.settings:
					result = RunCustomRandomization.randomizeRom(randomizedFileName,self.settings['Goal'], rSeed, self.settings['FlagsSet'],patches, banList = self.settings['BannedLocations'], allowList = self.settings['AllowedLocations'], modifiers = self.modList,adjustTrainerLevels = False, adjustRegularWildLevels = False, adjustSpecialWildLevels = False, trainerLVBoost = tlv, wildLVBoost=wlv,coreProgress = self.settings['CoreProgress'], otherSettings = self.settings, plandoPlacements = self.PlandoData)
				else:
					result = RunCustomRandomization.randomizeRom(randomizedFileName,self.settings['Goal'], rSeed, self.settings['FlagsSet'],patches, banList = self.settings['BannedLocations'], allowList = self.settings['AllowedLocations'], modifiers = self.modList,adjustTrainerLevels = False, adjustRegularWildLevels = False, adjustSpecialWildLevels = False, trainerLVBoost = tlv, wildLVBoost=wlv, otherSettings = self.settings, plandoPlacements = self.PlandoData)

			self.Randomize.setEnabled(True)
			if(self.OutputSpoiler.isChecked()):
				outputSpoiler = {}
				outputSpoiler['RNG Seed'] = rngSeed
				outputSpoiler['Solution'] = result[1]
				outputSpoiler['Useless Stuff'] = result[4]
				with open(randomizedFileName+'_SPOILER.txt', 'w') as f:
					yaml.dump(outputSpoiler, f, default_flow_style=False)
			self.Randomize.setText(_translate("MainWindow", "Randomize Rom"))
			QtWidgets.QMessageBox.about(self, 'Success', 'Sucessfully randomized rom')
			_translate = QtCore.QCoreApplication.translate
		except Exception:
			error_dialog = QtWidgets.QErrorMessage()
			error_dialog.showMessage(''.join(traceback.format_exc()))
			error_dialog.exec_()

	def AddBonusItem(self):
		(addedItem, ok1) = QInputDialog.getItem(self, "Select item you wish to add to the pool", "Select item you wish to add to the pool", self.itemsList, 0, False)
		if ok1:
			(nAdded, ok2) = QInputDialog.getInt(self,"Add how many?","Add how many?")
		if not ('BonusItems' in self.settings):
			self.settings['BonusItems'] = []
		if ok1 and ok2:
			for i in range(0,nAdded):
				self.settings['BonusItems'].append(addedItem)
		print(self.settings)

	def RemoveBonusItem(self):
		if 'BonusItems' in self.settings and len(self.settings['BonusItems']) > 0:
			self.settings['BonusItems'] = []
			if ('BonusItems' in self.settings): 
				(addedItem, ok1) = QInputDialog.getItem(self, r"View/Remove Items in pool", "Select any item you wish to remove, or cancel to remove nothing", self.settings['BonusItems'], 0, False)
			if ok1:
				(nAdded, ok2) = QInputDialog.getInt(self,"Remove how many?","Remove how many?")
			if not ('BonusItems' in self.settings):
				self.settings['BonusItems'] = []
			if ok1 and ok2:
				for i in range(0,nAdded):
					if addedItem in self.settings['BonusItems']:
						self.settings['BonusItems'].remove(addedItem)
		print(self.settings)


	def selectRom(self):
		_translate = QtCore.QCoreApplication.translate
		file = QFileDialog.getOpenFileName(directory = '.')[0]
		self.romPath = file
		if file != '':
			self.Randomize.setEnabled(True)
			self.Randomize.setText(_translate("MainWindow", "Randomize Rom"))
		else:
			self.Randomize.setEnabled(False)
			self.Randomize.setText(_translate("MainWindow", "No Rom Loaded!"))


	def selectLogicSettings(self):
		file = QFileDialog.getOpenFileName(directory = 'Modes')[0]
		if file != '':
			self.loadSettings(file)

	def loadModifier(self):
		modfile = QFileDialog.getOpenFileName(directory = 'Modifiers')[0]
		if modfile != '':
			yamlfile = open(modfile)
			yamltext = yamlfile.read()
			self.modList.append(yaml.load(yamltext))
			self.modList[-1]['fileName'] = modfile
			self.updateModListView()

	def deleteModifier(self):
		row = self.modifierList.currentRow()
		if(row != -1):
			self.modifierList.setCurrentRow(-1)
			self.modList.pop(row)
			self.updateModListView()



	def loadSettings(self, settingsFile):
		_translate = QtCore.QCoreApplication.translate
		yamlfile = open(settingsFile)
		yamltext = yamlfile.read()
		settings = yaml.load(yamltext)
		self.settings = settings
		yamlfile = open(settings['BasePatch'])
		yamltext = yamlfile.read()
		patches = json.loads(yamltext)
		modFileList = settings['DefaultModifiers']
		self.modList = []
		for i in modFileList:
			yamlfile = open(i)
			yamltext = yamlfile.read()
			self.modList.append(yaml.load(yamltext))
			self.modList[-1]['fileName'] = i
		self.updateModListView()
		self.CurentSettings.setText(_translate("MainWindow", settings['Name']))
		self.SettingsDescription.setText(_translate("MainWindow", settings['Description']))
		self.CurrentGoal.setText(_translate("MainWindow", settings['Goal']))

	def saveSettings(self):
		fName = QFileDialog.getSaveFileName(directory = 'Modes')[0]
		if(fName != ''):
			self.settings['DefaultModifiers'] = []
			for i in self.modList:
				self.settings['DefaultModifiers'].append(i['fileName'])
			with open(fName+'.yml', 'w') as f:
				yaml.dump(self.settings, f, default_flow_style=False)
				
	def SetUpPlando(self):
		QtWidgets.QMessageBox.about(self, 'Plandomizer Mode', 'Select a log file (which need not specify every item allocation) to use as basis for plandomizer.\n NOTE: We are not reponsible for any lost friendships due to use of plandomizer mode')
		file = QFileDialog.getOpenFileName(directory = '.')[0]
		if file != '':
			yamlfile = open(file)
			yamltext = yamlfile.read()
			spoiler = yaml.load(yamltext)
			newSpoiler = OrderedDict()
			for i in sorted(spoiler['Solution'],reverse=True):
				print(i)
				print(spoiler['Solution'][i])
				newSpoiler[spoiler['Solution'][i]] = i
			print(newSpoiler)
			if 'Useless Stuff' in spoiler:
				for i in spoiler['Useless Stuff']:
					newSpoiler[i] = spoiler['Useless Stuff'][i]
			self.PlandoData = newSpoiler
			self.PlandoMode = True
			self.TurnOffPlando.setEnabled(True)
			
	def DeactivatePlando(self):
		self.PlandoData = {}
		self.PlandoMode = False
		self.TurnOffPlando.setEnabled(False)

	def updateModListView(self):
		self.modifierList.clear()
		for i in self.modList:
			self.modifierList.addItem(i['Name'])

	def updateModifierDescription(self):
		_translate = QtCore.QCoreApplication.translate
		row = self.modifierList.currentRow()
		if(row != -1 and row < len(self.modList)):
			self.ModifierDescription.setText(_translate("MainWindow", self.modList[row]['Description']))
		else:
			self.ModifierDescription.setText(_translate("MainWindow", "No modifier selected!"))
			
	def SelectDefaultSettings(self):
		QtWidgets.QMessageBox.about(self, 'Choose default settings', 'Select the mode which should be loaded by default when you open up the randomizer')
		fName = QFileDialog.getOpenFileName(directory = 'Modes')[0]
		if(fName != ''):
			yamlfile = open('RandomizerConfig.yml')
			yamltext = yaml.load(yamlfile)
			yamltext['DefaultSettings'] = fName
			with open('RandomizerConfig.yml', 'w') as f:
				yaml.dump(yamltext, f, default_flow_style=False)
		else:
			error_dialog = QtWidgets.QErrorMessage()
			error_dialog.showMessage('A file was not selected!')
			error_dialog.exec_()
def main():
	os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
	app = QApplication(sys.argv)
	form = RunWindow()
	form.show()
	app.exec_()

if __name__ == '__main__':
	main()
