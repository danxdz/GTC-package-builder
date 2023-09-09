import os
import sys
from PyQt5.QtWidgets import QCheckBox, QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog, QComboBox, QLineEdit, QTextBrowser

import re

class StepFileOps:
    def __init__(self, gui_instance):
        self.category_dict = {}
        self.element_dict = {}
        self.step_content = []
        self.gui_instance = gui_instance
        self.filename = ""

    def parseStepFile(self, filename):
        self.filename = filename
        with open(filename, 'r') as file:
            self.step_content = file.readlines()

        self.category_dict.clear()
        self.element_dict.clear()

        for line in self.step_content:
            line = line.strip()

            if line.startswith('#'):
                parts = line.split('=')

                if len(parts) >= 2:
                    element_number = parts[0]
                    element_name = parts[1].split('(')[0].strip()
                    self.element_dict[element_number] = element_name

                    if element_name in self.category_dict:
                        self.category_dict[element_name].append(element_number)
                    else:
                        self.category_dict[element_name] = [element_number]

    def formatParameters(self, parameters):
        formatted_parameters = []
        parameter_tokens = re.split(r'([,;()])', parameters)
        for token in parameter_tokens:
            token = token.strip()
            if token.startswith('#'):
                formatted_parameters.append(f"{token}")
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

    def getElementValue(self, element_number):
        content = self.getElementContent(element_number)
        parameters = ""
        if '(' in content and ')' in content:
            parameters = content.split('(')[1].split(')')[0]
        return parameters

    def searchElements(self, text):
        text = text.lower()
        matching_elements = []

        for element_number, element_name in self.element_dict.items():
            if text in element_number.lower() or text in element_name.lower():
                matching_elements.append(element_number)

        return matching_elements

class StepFileViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.category_dict = {}
        self.step_file_ops = None  # Inicialize como None
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.load_button = QPushButton('Open STEP File', self)
        self.load_button.clicked.connect(self.openFile)
        layout.addWidget(self.load_button)

        self.category_combo = QComboBox(self)
        self.category_combo.currentIndexChanged.connect(self.filterTreeByCategory)
        layout.addWidget(self.category_combo)
        
        # Adicione um widget de caixa de seleção para filtrar por nome
        self.name_filter_checkbox = QCheckBox("Mostrar Apenas com Nome", self)
        self.name_filter_checkbox.stateChanged.connect(self.filterByName)
        layout.addWidget(self.name_filter_checkbox)


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
        self.ref_tree_widget.itemClicked.connect(self.updateSelectedElement)
        layout.addWidget(self.ref_tree_widget)

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
            self.step_file_ops = StepFileOps(self)  # Crie a instância de StepFileOps aqui
            self.step_file_ops.parseStepFile(fileName)
            self.updateTreeWithCategories()

            sorted_categories = sorted(self.step_file_ops.category_dict.keys())
            self.category_combo.addItems(sorted_categories)

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
        element_name = self.step_file_ops.element_dict.get(element_number, "")
        element_content = self.step_file_ops.getElementContent(element_number)
        self.info_browser.clear()
        self.info_browser.append(f"Element Number: {element_number}")
        self.info_browser.append(f"Element Name: {element_name}")
        self.info_browser.append(f"Element Content:")
        self.info_browser.append(element_content)

        referenced_elements = self.step_file_ops.getReferencedElements(element_number)
        self.ref_tree_widget.clear()
        self.ref_tree_widget.setHeaderLabels(["Referenced Elements"])
        for element in referenced_elements:
            element_name = self.step_file_ops.element_dict.get(element, "")
            if not element_name:
                element_name = f"{element}"
            ref_item = QTreeWidgetItem(self.ref_tree_widget)
            ref_item.setText(0, f"{element_name}")

    def updateSelectedElement(self, item):
        element_number = item.text(0)
        match = re.match(r'#(\d+)', element_number)
        if element_number.startswith("#") and match:
            element_number = "#" + match.group(1)
            self.selectElementInTree(element_number)

    def selectElementInTree(self, element_number):
        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            for j in range(category_item.childCount()):
                element_item = category_item.child(j)
                if element_item.text(0) == element_number:
                    self.tree_widget.setCurrentItem(element_item)
                    return

    def searchElements(self, text):
        if hasattr(self, 'step_file_ops'):
            if text:
                matching_elements = self.step_file_ops.searchElements(text)
                self.updateTreeWithSearchResults(matching_elements)
            else:
                self.updateTreeWithCategories()
        else:
            print("Please open a STEP file before searching.")

    def updateTreeWithCategories(self):
        self.tree_widget.clear()
        root = QTreeWidgetItem(self.tree_widget)
        self.tree_widget.setHeaderLabel(os.path.basename(self.step_file_ops.filename).split('.')[0])
        root.setText(0, "Categories")
        root.setExpanded(True)

        sorted_categories = sorted(self.step_file_ops.category_dict.keys())

        for category in sorted_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(0, f"{category} ({len(self.step_file_ops.category_dict[category])})")

            for element in sorted(self.step_file_ops.category_dict[category], key=lambda x: self.step_file_ops.element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)

    def updateTreeWithSearchResults(self, matching_elements):
        self.tree_widget.clear()
        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "Categories")

        expanded_categories = set()

        for element_number in matching_elements:
            element_name = self.step_file_ops.element_dict.get(element_number, "")
            category = element_name
            if not category:
                category = "Uncategorized"
            expanded_categories.add(category)

        for category in expanded_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(0, f"{category} ({len(self.step_file_ops.category_dict[category])})")

            for element in sorted(self.step_file_ops.category_dict[category], key=lambda x: self.step_file_ops.element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)
        
        root.setExpanded(True)

    def filterByName(self):
        show_only_named = self.name_filter_checkbox.isChecked()
        name_to_search = self.search_box.text().strip()  # Get the name to search from the search box

        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            any_child_visible = False  # Flag to check if any child elements are visible in this category

            for j in range(category_item.childCount()):
                element_item = category_item.child(j)
                element_number = element_item.text(0)

                # Get the content of the element
                element_content = self.step_file_ops.getElementContent(element_number)

                # Extract the name within single quotes in the element content
                name_match = re.search(r"'(.*?)'", element_content)

                if name_match:
                    element_name = name_match.group(1)
                else:
                    element_name = element_number  # Use the element number as the name

                # Check if the element content or extracted name contains the name to search
                element_matches_search = (show_only_named and element_name and name_to_search.lower() in element_name.lower()) or \
                    (not show_only_named and name_to_search.lower() in element_content.lower())

                element_item.setHidden(not element_matches_search)

                # Update the flag if any child element is visible
                if not element_item.isHidden():
                    any_child_visible = True

                # Check if there are child elements
                if element_item.childCount() > 0:
                    print("Child elements found")
                    for k in range(element_item.childCount()):
                        child_element_item = element_item.child(k)
                        child_element_number = child_element_item.text(0)
                        child_element_content = self.step_file_ops.getElementContent(child_element_number)
                        # Extract the name within single quotes in the child element content
                        child_name_match = re.search(r"'(.*?)'", child_element_content)
                        print("child_name_match: ", child_name_match)

                        if child_name_match:
                            child_element_name = child_name_match.group(1)
                        else:
                            child_element_name = child_element_number  # Use the element number as the name

                        print("child_element_name: ", child_element_name)
                        # Check if the child element content or extracted name contains the name to search
                        child_element_matches_search = (show_only_named and child_element_name and name_to_search.lower() in child_element_name.lower()) or \
                            (not show_only_named and name_to_search.lower() in child_element_content.lower())

                        child_element_item.setHidden(not child_element_matches_search)

                        # Update the flag if any child element is visible
                        if not child_element_item.isHidden():
                            any_child_visible = True

                        # Print statements for debugging
                        print(child_element_number, " - ", child_element_name, " - ", child_element_content)

            # Check if all child elements are hidden, and if so, hide the category name
            category_item.setHidden(not any_child_visible)

    def isCategoryEmpty(self, category_name):
        if category_name in self.step_file_ops.category_dict:
            for element_number in self.step_file_ops.category_dict[category_name]:
                element_item = self.tree_widget.findItems(element_number, Qt.MatchRecursive)
                if not element_item or element_item[0].isHidden() == False:
                    return False
        return True



def main():
    app = QApplication(sys.argv)
    viewer = StepFileViewer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
