# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VolumeCalculationToolDialog
                                 A QGIS plugin
 Calculates volume based on DEM height layers
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-09-23
        git sha              : $Format:%H$
        copyright            : (C) 2020 by REDcatch GmbH.
        email                : support@redcatch.at
 ***************************************************************************/

/***************************************************************************
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from qgis.PyQt.QtCore import QUrl
from enum import Enum

DEFAULT_ATTRIBUTE_NAME = "V_above"
DEFAULT_ATTRIBUTE_NAME_NEG = "V_below"
ATTRIBUTE_FIELD_MAX_LENGTH = 10

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'volume_calculation_tool_dialog_base.ui'))


class BaseLevelOptions(Enum):
    APPROXIMATE_VIA_MIN = 0
    APPROXIMATE_VIA_AVG = 1
    USE_DEM_LAYER = 2
    MANUAL_BASE_LEVEL = 3
    
    def __str__(self):
        if self.value == 0:
            return "Approximate base level via AVERAGE of polygon vertices"
        if self.value == 1:
            return "LOWEST Point: Use minimum height of polygon vertices"
        if self.value == 2:
            return "Use a SECOND DEM layer as a base"
        if self.value == 3:
            return "Manually enter base level"


class CountOptions(Enum):
    COUNT_ABOVE_AND_BELOW = 0
    COUNT_ONLY_ABOVE = 1
    COUNT_ONLY_BELOW = 2
    SUBTRACT_VOL_BELOW = 3
    ADD_VOL_BELOW_TO_ABOVE = 4
    
    def __str__(self):
        if self.value == 0:
            return "Count both, above and below (cut/fill)"
        if self.value == 1:
            return "Count only above (eg. stock pile)"
        if self.value == 2:
            return "Count only below (eg. gravel pit)"
        if self.value == 3:
            return "Subtract below count from above count"
        if self.value == 4:
            return "Add below count to above count"

        


class VolumeCalculationToolDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, updateDefaultSampleStepOnHeightLayerChange, determineBandsForHeight, determineBandsForBase, workflow_function, cancel_long_workflow, parent=None):
        """Constructor."""
        super().__init__()
        self.setupUi(self)
        self.populateStaticOptions()
        self.radioButtonAccurate.setChecked(True)
        self.radioButtonSimple.setChecked(False)
        self.toggleAccurateWorkFlow()

        self.radioButtonSimple.toggled.connect(self.toggleWorkflow)
        self.radioButtonAccurate.toggled.connect(self.toggleAccurateWorkFlow)
        self.pushButtonStartCalculation.clicked.connect(workflow_function)
        self.pushButtonCancelCalculation.clicked.connect(cancel_long_workflow)
        self.pushButtonHelp.clicked.connect(self.show_help)

        self.clearLog.clicked.connect(self.clear_log)
        self.saveLog.clicked.connect(self.log_save)

        self.mFieldComboHeightLayerBase.setEnabled(False)
        self.mFieldComboBandBase.setEnabled(False)
        self.doubleSpinBoxBaseLevel.setEnabled(False)
        
        self.mFieldComboHeightLayer.currentIndexChanged.connect(determineBandsForHeight)
        self.mFieldComboHeightLayer.currentIndexChanged.connect(updateDefaultSampleStepOnHeightLayerChange)
        self.mFieldComboHeightLayerBase.currentIndexChanged.connect(determineBandsForBase)
        self.mFieldComboBaseLevelMethod.currentIndexChanged.connect(self.toggleBaseLevelOptions)
        
        self.progressBar.reset()
        self.progressBar.setRange(0, 100)
        self.doubleSpinBoxBaseLevel.setValue(0.00)
        self.doubleSpinBoxBaseLevel.setRange(-100000, 100000)
        
        self.fieldName.setMaxLength(ATTRIBUTE_FIELD_MAX_LENGTH)
        self.fieldName_2.setMaxLength(ATTRIBUTE_FIELD_MAX_LENGTH)
        self.doubleSpinBoxSampleStepX.setValue(1)
        self.doubleSpinBoxSampleStepY.setValue(1)
        self.doubleSpinBoxSampleStepX.setRange(0, 100000)
        self.doubleSpinBoxSampleStepY.setRange(0, 100000)
        self.logOutput.setReadOnly(True)
        self.fieldName.setPlaceholderText(DEFAULT_ATTRIBUTE_NAME)
        self.fieldName_2.setPlaceholderText(DEFAULT_ATTRIBUTE_NAME_NEG)
        self.checkBox_add_field.setChecked(True)
        self.pushButtonExit.clicked.connect(self.closeIt)
        self.pushButtonAbout.clicked.connect(self.popAboutBox)
    
    def toggleBaseLevelOptions(self, index):
        if index == 0:
            self.mFieldComboHeightLayerBase.setEnabled(False)
            self.mFieldComboBandBase.setEnabled(False)
            self.doubleSpinBoxBaseLevel.setEnabled(False)
        if index == 1:
            self.mFieldComboHeightLayerBase.setEnabled(False)
            self.mFieldComboBandBase.setEnabled(False)
            self.doubleSpinBoxBaseLevel.setEnabled(False)
        if index == 2:
            self.mFieldComboHeightLayerBase.setEnabled(True)
            self.mFieldComboBandBase.setEnabled(True)
            self.doubleSpinBoxBaseLevel.setEnabled(False)
        if index == 3:
            self.mFieldComboHeightLayerBase.setEnabled(False)
            self.mFieldComboBandBase.setEnabled(False)
            self.doubleSpinBoxBaseLevel.setEnabled(True)

    def closeIt(self): 
        self.close()
        
    def show_help(self):
        help_file = 'file:///%s/help/build/html/index.html' % os.path.dirname(__file__)
        QDesktopServices.openUrl(QUrl(help_file))

    def toggleWorkflow(self):
        isActivatedSimple = self.radioButtonSimple.isChecked()
        isActivatedAccurate = self.radioButtonAccurate.isChecked()
        self.progressBar.reset()
        self.pushButtonStartCalculation.setEnabled(isActivatedSimple or isActivatedAccurate)
        self.pushButtonCancelCalculation.setEnabled(isActivatedSimple or isActivatedAccurate)
        
    def toggleAccurateWorkFlow(self):
        isActivated = self.radioButtonAccurate.isChecked()
        self.mFieldComboCountingMethod.setEnabled(isActivated)
        self.doubleSpinBoxSampleStepX.setEnabled(isActivated)
        self.doubleSpinBoxSampleStepY.setEnabled(isActivated)
        self.mFieldComboCountingMethod.setEnabled(isActivated)
        self.toggleWorkflow()

    def populateStaticOptions(self):
        self.mFieldComboCountingMethod.addItem(str(CountOptions.COUNT_ABOVE_AND_BELOW))
        self.mFieldComboCountingMethod.addItem(str(CountOptions.COUNT_ONLY_ABOVE))
        self.mFieldComboCountingMethod.addItem(str(CountOptions.COUNT_ONLY_BELOW))
        #self.mFieldComboCountingMethod.addItem(str(CountOptions.SUBTRACT_VOL_BELOW))
        #self.mFieldComboCountingMethod.addItem(str(CountOptions.ADD_VOL_BELOW_TO_ABOVE))
        self.mFieldComboBaseLevelMethod.addItem(str(BaseLevelOptions.APPROXIMATE_VIA_MIN))
        self.mFieldComboBaseLevelMethod.addItem(str(BaseLevelOptions.APPROXIMATE_VIA_AVG))
        self.mFieldComboBaseLevelMethod.addItem(str(BaseLevelOptions.USE_DEM_LAYER))
        self.mFieldComboBaseLevelMethod.addItem(str(BaseLevelOptions.MANUAL_BASE_LEVEL))

    
    def lockupGUIDuringCalculation(self):
        self.mFieldComboCountingMethod.setEnabled(False)
        self.doubleSpinBoxSampleStepX.setEnabled(False)
        self.doubleSpinBoxSampleStepY.setEnabled(False)
        self.mFieldComboCountingMethod.setEnabled(False)
        self.radioButtonAccurate.setEnabled(False)
        self.radioButtonSimple.setEnabled(False)
        self.doubleSpinBoxBaseLevel.setEnabled(False)
        self.pushButtonStartCalculation.setEnabled(False)
        self.pushButtonCancelCalculation.setEnabled(True)
        self.mFieldComboHeightLayer.setEnabled(False)
        self.mFieldComboPolygon.setEnabled(False)
        self.checkBox_add_field.setEnabled(False)
        self.fieldName.setEnabled(False)
        self.fieldName_2.setEnabled(False)
        
    def unlockGUI(self):
        self.mFieldComboCountingMethod.setEnabled(True)
        self.doubleSpinBoxSampleStepX.setEnabled(True)
        self.doubleSpinBoxSampleStepY.setEnabled(True)
        self.mFieldComboCountingMethod.setEnabled(True)
        self.radioButtonAccurate.setEnabled(True)
        self.radioButtonSimple.setEnabled(True)
        self.doubleSpinBoxBaseLevel.setEnabled(True)
        self.pushButtonStartCalculation.setEnabled(True)
        self.pushButtonCancelCalculation.setEnabled(False)
        self.mFieldComboHeightLayer.setEnabled(True)
        self.mFieldComboPolygon.setEnabled(True)
        self.checkBox_add_field.setEnabled(True)
        self.fieldName.setEnabled(True)
        self.fieldName_2.setEnabled(True)
        
    def popFatalErrorBox(self, error_msg):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Error")
        msgBox.setText(error_msg)
        msgBox.exec_()
        
    def popAboutBox(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("About")
        msgBox.setText("Made by the team @ REDCatch, we also make other (hopefully) (useful) things :)")
        msgBox.exec_()
        
    def log_save(self):
        name = QFileDialog.getSaveFileName(self, 'Save Log To File')
        file = open(name[0],'w')
        log_text = self.logOutput.toPlainText()
        file.write(log_text)
        file.close()
        
    def clear_log(self):
        self.logOutput.clear()
