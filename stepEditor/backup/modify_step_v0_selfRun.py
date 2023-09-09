import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog, QComboBox, QLineEdit, QTextBrowser

import re


class StepFileViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.category_dict = {}
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.load_button = QPushButton('Open STEP File', self)
        self.load_button.clicked.connect(self.openFile)
        layout.addWidget(self.load_button)

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.itemClicked.connect(self.showElementInfo)
        layout.addWidget(self.tree_widget)

        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search...")
        self.search_box.textChanged.connect(self.searchElements)
        layout.addWidget(self.search_box)

        self.info_browser = QTextBrowser(self)
        layout.addWidget(self.info_browser)

        self.ref_tree_widget = QTreeWidget(self)
        layout.addWidget(self.ref_tree_widget)  # Adicione esta linha

        self.central_widget.setLayout(layout)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('STEP File Viewer')
        self.show()

    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open STEP File", "", "STEP Files (*.stp *.step);;All Files (*)", options=options)

        if fileName:
            self.parseStepFile(fileName)

    def parseStepFile(self, filename):
        with open(filename, 'r') as file:
            step_content = file.readlines()

        self.tree_widget.clear()
        self.info_browser.clear()
        self.category_dict.clear()

        element_dict = {}

        for line in step_content:
            line = line.strip()

            if line.startswith('#'):
                parts = line.split('=')

                if len(parts) >= 2:
                    element_number = parts[0]
                    element_name = parts[1].split('(')[0].strip()
                    element_dict[element_number] = element_name

                    if element_name in self.category_dict:
                        self.category_dict[element_name].append(element_number)
                    else:
                        self.category_dict[element_name] = [element_number]

        sorted_categories = sorted(self.category_dict.keys())
        self.search_box.clear()
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(sorted_categories)
        self.category_combo.currentIndexChanged.connect(
            self.filterTreeByCategory)
        layout = self.central_widget.layout()
        layout.insertWidget(1, self.category_combo)

        root = QTreeWidgetItem(self.tree_widget)
        #set header
        self.tree_widget.setHeaderLabel(os.path.basename(filename).split('.')[0])
        root.setText(0, "Categories")
        root.setExpanded(True)

        for category in sorted_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(
                0, f"{category} ({len(self.category_dict[category])})")

            for element in sorted(self.category_dict[category], key=lambda x: element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)

        self.element_dict = element_dict
        self.step_content = step_content

    def filterTreeByCategory(self):
        selected_category = self.category_combo.currentText()

        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            for j in range(category_item.childCount()):
                element_item = category_item.child(j)
                if selected_category in element_item.text(0):
                    element_item.setHidden(False)
                else:
                    element_item.setHidden(True)

    def showElementInfo(self, item):
        element_number = item.text(0)
        element_name = self.element_dict.get(element_number, "")
        element_content = self.getElementContent(element_number)
        self.info_browser.clear()
        self.info_browser.append(f"Element Number: {element_number}")
        self.info_browser.append(f"Element Name: {element_name}")
        self.info_browser.append(f"Element Content:")
        self.info_browser.append(element_content)

        referenced_elements = self.getReferencedElements(element_number)
        self.ref_tree_widget.clear()
        self.ref_tree_widget.setHeaderLabels(["Referenced Elements"])
        for element in referenced_elements:
            element_name = self.element_dict.get(element, "")
            if not element_name:
                element_name = f"Element {element}"
            ref_item = QTreeWidgetItem(self.ref_tree_widget)
            ref_item.setText(0, f"{element_name}")

    def getElementContent(self, element_number):
        content = []
        found_element = False

        for line in self.step_content:
            line = line.strip()

            if line.startswith(element_number):
                found_element = True
            elif found_element and line.startswith('#'):
                break

            if found_element:
                content.append(line)

        formatted_content = []
        for line in content:
            parts = line.split('=')
            if len(parts) >= 2:
                parameters = parts[1].strip()
                formatted_parameters = self.formatParameters(parameters)
                formatted_content.append(f"{formatted_parameters}")

        return '\n'.join(formatted_content)

    def formatParameters(self, parameters):
        formatted_parameters = []
        parameter_tokens = re.split(r'([,;()])', parameters)
        for token in parameter_tokens:
            token = token.strip()
            if token.startswith('#'):
                referenced_name = self.element_dict.get(token, "")
                formatted_parameters.append(f"{referenced_name} ({token})")
            else:
                formatted_parameters.append(token)

        return ''.join(formatted_parameters)

    def getReferencedElements(self, element_number):
        referenced_elements = []
        content = self.getElementContent(element_number)
        tokens = re.split(r'([,;()])', content)
        for token in tokens:
            token = token.strip()
            if token.startswith('#'):
                element_details = self.getElementDetails(token)
                element_details = token + " - " + element_details
                referenced_elements.append(element_details)

        return referenced_elements

    def getElementDetails(self, element_number):
        content = self.getElementContent(element_number)
        formatted_content = []

        parameter_tokens = re.split(r'([,;()])', content)
        for token in parameter_tokens:
            token = token.strip()
            if token == element_number:
                referenced_name = self.element_dict.get(token, "")
                referenced_value = self.getElementContent(token)
                formatted_content.append(
                    f"{referenced_name} ({referenced_value})")
            else:
                formatted_content.append(token)

        return ''.join(formatted_content)

    def getElementValue(self, element_number):
        content = self.getElementContent(element_number)
        parameters = content.split('(')[1].split(')')[0]
        return parameters

    def searchElements(self, text):
        text = text.lower()
        matching_elements = []

        for element_number, element_name in self.element_dict.items():
            if text in element_number.lower() or text in element_name.lower():
                matching_elements.append(element_number)

        self.updateTreeWithSearchResults(matching_elements)

    def updateTreeWithSearchResults(self, matching_elements):
        self.tree_widget.clear()

        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "Categories")

        expanded_categories = set()

        for element_number in matching_elements:
            element_name = self.element_dict.get(element_number, "")
            category = element_name
            if not category:
                category = "Uncategorized"
            expanded_categories.add(category)

        for category in expanded_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(0, f"{category} ({len(self.category_dict[category])})")

            for element in sorted(self.category_dict[category], key=lambda x: self.element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)
        
        root.setExpanded(True)


def main():
    app = QApplication(sys.argv)
    viewer = StepFileViewer()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()