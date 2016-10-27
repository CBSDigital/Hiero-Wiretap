# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wiretapBrowserB02.ui'
#
# Created: Tue May 13 11:41:22 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_browserDialog(object):
    def setupUi(self, browserDialog):
        browserDialog.setObjectName("browserDialog")
        browserDialog.resize(540, 400)
        self.verticalLayout = QtGui.QVBoxLayout(browserDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(browserDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.nodeButtonsLayout = QtGui.QHBoxLayout()
        self.nodeButtonsLayout.setObjectName("nodeButtonsLayout")
        self.refreshButton = QtGui.QPushButton(browserDialog)
        self.refreshButton.setObjectName("refreshButton")
        self.nodeButtonsLayout.addWidget(self.refreshButton)
        self.refreshAllButton = QtGui.QPushButton(browserDialog)
        self.refreshAllButton.setObjectName("refreshAllButton")
        self.nodeButtonsLayout.addWidget(self.refreshAllButton)
        self.newNodeButton = QtGui.QPushButton(browserDialog)
        self.newNodeButton.setEnabled(False)
        self.newNodeButton.setObjectName("newNodeButton")
        self.nodeButtonsLayout.addWidget(self.newNodeButton)
        self.deleteNodeButton = QtGui.QPushButton(browserDialog)
        self.deleteNodeButton.setEnabled(False)
        self.deleteNodeButton.setObjectName("deleteNodeButton")
        self.nodeButtonsLayout.addWidget(self.deleteNodeButton)
        self.filtersButton = QtGui.QPushButton(browserDialog)
        self.filtersButton.setEnabled(False)
        self.filtersButton.setObjectName("filtersButton")
        self.nodeButtonsLayout.addWidget(self.filtersButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.nodeButtonsLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.nodeButtonsLayout)
        self.nodeTreeView = NodeTreeView(browserDialog)
        self.nodeTreeView.setObjectName("nodeTreeView")
        self.verticalLayout.addWidget(self.nodeTreeView)
        self.pathLayout = QtGui.QHBoxLayout()
        self.pathLayout.setObjectName("pathLayout")
        self.pathEdit = QtGui.QLineEdit(browserDialog)
        self.pathEdit.setObjectName("pathEdit")
        self.pathLayout.addWidget(self.pathEdit)
        self.idButton = QtGui.QPushButton(browserDialog)
        self.idButton.setMaximumSize(QtCore.QSize(23, 16777215))
        font = QtGui.QFont()
        font.setWeight(50)
        font.setItalic(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.idButton.setFont(font)
        self.idButton.setCheckable(True)
        self.idButton.setFlat(False)
        self.idButton.setObjectName("idButton")
        self.pathLayout.addWidget(self.idButton)
        self.verticalLayout.addLayout(self.pathLayout)
        self.confirmButtonBox = QtGui.QDialogButtonBox(browserDialog)
        self.confirmButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Open)
        self.confirmButtonBox.setObjectName("confirmButtonBox")
        self.verticalLayout.addWidget(self.confirmButtonBox)

        self.retranslateUi(browserDialog)
        QtCore.QObject.connect(self.confirmButtonBox, QtCore.SIGNAL("accepted()"), browserDialog.accept)
        QtCore.QObject.connect(self.confirmButtonBox, QtCore.SIGNAL("rejected()"), browserDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(browserDialog)
        browserDialog.setTabOrder(self.confirmButtonBox, self.refreshButton)
        browserDialog.setTabOrder(self.refreshButton, self.refreshAllButton)
        browserDialog.setTabOrder(self.refreshAllButton, self.newNodeButton)
        browserDialog.setTabOrder(self.newNodeButton, self.deleteNodeButton)
        browserDialog.setTabOrder(self.deleteNodeButton, self.filtersButton)
        browserDialog.setTabOrder(self.filtersButton, self.nodeTreeView)

    def retranslateUi(self, browserDialog):
        browserDialog.setWindowTitle(QtGui.QApplication.translate("browserDialog", "Choose Wiretap node", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("browserDialog", "Select a destination library or reel.", None, QtGui.QApplication.UnicodeUTF8))
        self.refreshButton.setText(QtGui.QApplication.translate("browserDialog", "Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.refreshAllButton.setText(QtGui.QApplication.translate("browserDialog", "Refresh All", None, QtGui.QApplication.UnicodeUTF8))
        self.newNodeButton.setText(QtGui.QApplication.translate("browserDialog", "New", None, QtGui.QApplication.UnicodeUTF8))
        self.deleteNodeButton.setText(QtGui.QApplication.translate("browserDialog", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.filtersButton.setText(QtGui.QApplication.translate("browserDialog", "Filters", None, QtGui.QApplication.UnicodeUTF8))
        self.idButton.setToolTip(QtGui.QApplication.translate("browserDialog", "Toggle to reveal the unique node ID instead of the display names.", None, QtGui.QApplication.UnicodeUTF8))
        self.idButton.setText(QtGui.QApplication.translate("browserDialog", "ID", None, QtGui.QApplication.UnicodeUTF8))

from WiretapView import NodeTreeView
