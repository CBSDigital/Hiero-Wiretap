# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wiretapShotProcessorA04.ui'
#
# Created: Wed May 21 12:25:55 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(718, 423)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.titleLayout = QtGui.QHBoxLayout()
        self.titleLayout.setObjectName("titleLayout")
        self.titleLabel = QtGui.QLabel(Form)
        self.titleLabel.setObjectName("titleLabel")
        self.titleLayout.addWidget(self.titleLabel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.titleLayout.addItem(spacerItem)
        self.logoLabel = QtGui.QLabel(Form)
        self.logoLabel.setText("")
        self.logoLabel.setPixmap(QtGui.QPixmap("../../resources/images/cbsd_logo.png"))
        self.logoLabel.setObjectName("logoLabel")
        self.titleLayout.addWidget(self.logoLabel)
        self.verticalLayout_2.addLayout(self.titleLayout)
        self.instructionsLabel = QtGui.QLabel(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.instructionsLabel.sizePolicy().hasHeightForWidth())
        self.instructionsLabel.setSizePolicy(sizePolicy)
        self.instructionsLabel.setStyleSheet("")
        self.instructionsLabel.setWordWrap(True)
        self.instructionsLabel.setObjectName("instructionsLabel")
        self.verticalLayout_2.addWidget(self.instructionsLabel)
        self.notesButton = QtGui.QPushButton(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.notesButton.setFont(font)
        self.notesButton.setStyleSheet("text-align:left")
        self.notesButton.setFlat(True)
        self.notesButton.setObjectName("notesButton")
        self.verticalLayout_2.addWidget(self.notesButton)
        self.notesLabel = QtGui.QLabel(Form)
        self.notesLabel.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.notesLabel.sizePolicy().hasHeightForWidth())
        self.notesLabel.setSizePolicy(sizePolicy)
        self.notesLabel.setScaledContents(False)
        self.notesLabel.setObjectName("notesLabel")
        self.verticalLayout_2.addWidget(self.notesLabel)
        spacerItem1 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem1)
        self.inputLayout = QtGui.QGridLayout()
        self.inputLayout.setObjectName("inputLayout")
        self.nodePathEdit = QtGui.QLineEdit(Form)
        self.nodePathEdit.setObjectName("nodePathEdit")
        self.inputLayout.addWidget(self.nodePathEdit, 0, 1, 1, 1)
        self.chooseButton = QtGui.QPushButton(Form)
        self.chooseButton.setObjectName("chooseButton")
        self.inputLayout.addWidget(self.chooseButton, 0, 2, 1, 1)
        self.clipNameLabel = QtGui.QLabel(Form)
        self.clipNameLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.clipNameLabel.setObjectName("clipNameLabel")
        self.inputLayout.addWidget(self.clipNameLabel, 1, 0, 1, 1)
        self.sendToLabel = QtGui.QLabel(Form)
        self.sendToLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.sendToLabel.setObjectName("sendToLabel")
        self.inputLayout.addWidget(self.sendToLabel, 0, 0, 1, 1)
        self.clipNameEdit = QtGui.QLineEdit(Form)
        self.clipNameEdit.setObjectName("clipNameEdit")
        self.inputLayout.addWidget(self.clipNameEdit, 1, 1, 1, 1)
        self.addElementButton = QtGui.QPushButton(Form)
        self.addElementButton.setObjectName("addElementButton")
        self.inputLayout.addWidget(self.addElementButton, 1, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.inputLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.titleLabel.setText(QtGui.QApplication.translate("Form", "<h1>Hiero&lt;&gt;Wiretap</h1>", None, QtGui.QApplication.UnicodeUTF8))
        self.instructionsLabel.setText(QtGui.QApplication.translate("Form", "<html><head/><body><p>Converts and sends the selected shots to a Stone FS via Autodesk Wiretap.</p>\n"
"<ol>\n"
"<li>Choose a Wiretap IFFFS server and a destination library or reel.</li>\n"
"<li>Add a naming scheme for each clip node generated by the Stonify task.</li>\n"
"<li>Verify handle and track settings before pressing the Export button.</li>\n"
"</ol>\n"
"</body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.notesButton.setText(QtGui.QApplication.translate("Form", "Notes  [+]", None, QtGui.QApplication.UnicodeUTF8))
        self.notesLabel.setText(QtGui.QApplication.translate("Form", "<html><head/><body>\n"
"<ul>\n"
"<li>Arrange Stonify tasks (<tt>CLIP</tt>s) hierarchically in the export structure viewer according to this template (<tt>REEL</tt>s are optional):<br/>\n"
"<tt>HOST/VOLUME/PROJECT/LIBRARY/[REEL]/CLIP</tt></li>\n"
"<li>Other types of export tasks, such as Transcode Images, can still generate folders and write media to a standard file system.</li>\n"
"<li>Certain handle and track settings have not yet been implemented for Stonify tasks, including shot retiming and audio clips.</li>\n"
"</ul>\n"
"</body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.chooseButton.setText(QtGui.QApplication.translate("Form", "Choose...", None, QtGui.QApplication.UnicodeUTF8))
        self.clipNameLabel.setText(QtGui.QApplication.translate("Form", "Clip Name:", None, QtGui.QApplication.UnicodeUTF8))
        self.sendToLabel.setText(QtGui.QApplication.translate("Form", "Send To:", None, QtGui.QApplication.UnicodeUTF8))
        self.clipNameEdit.setText(QtGui.QApplication.translate("Form", "{shot}", None, QtGui.QApplication.UnicodeUTF8))
        self.addElementButton.setText(QtGui.QApplication.translate("Form", "Add", None, QtGui.QApplication.UnicodeUTF8))

