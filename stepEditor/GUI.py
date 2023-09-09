import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog, QComboBox, QLineEdit, QTextBrowser

from step_file_ops import StepFileOps  # Importe a classe StepFileOps

class StepFileViewer(QMainWindow):
    def __init__(self, step_file_ops):
        super().__init__()

        self.step_file_ops = step_file_ops  # Crie a instância de StepFileOps
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
            self.step_file_ops.parseStepFile(fileName)  # Use a instância de StepFileOps para analisar o arquivo
            self.updateTreeWithCategories()

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
                element_name = f"Element {element}"
            ref_item = QTreeWidgetItem(self.ref_tree_widget)
            ref_item.setText(0, f"{element_name}")

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
        self.tree_widget.setHeaderLabel(
            os.path.basename(self.step_file_ops.filename).split('.')[0])
        root.setText(0, "Categories")
        root.setExpanded(True)

        sorted_categories = sorted(self.step_file_ops.category_dict.keys())

        for category in sorted_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(
                0, f"{category} ({len(self.step_file_ops.category_dict[category])})")

            for element in sorted(self.step_file_ops.category_dict[category], key=lambda x: self.step_file_ops.element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)

    def updateTreeWithSearchResults(self, matching_elements):
        self.tree_widget.clear()

        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "Categories")

        expanded_categories = set()

        for element_number in matching_elements:
            element_name = self.step_file_ops.element_dict.get(
                element_number, "")
            category = element_name
            if not category:
                category = "Uncategorized"
            expanded_categories.add(category)

        for category in expanded_categories:
            category_item = QTreeWidgetItem(root)
            category_item.setText(
                0, f"{category} ({len(self.step_file_ops.category_dict[category])})")

            for element in sorted(self.step_file_ops.category_dict[category], key=lambda x: self.step_file_ops.element_dict[x]):
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)

        root.setExpanded(True)


def main():
    app = QApplication(sys.argv)
    step_file_ops = StepFileOps()  # Crie uma instância de StepFileOps
    viewer = StepFileViewer(step_file_ops)  # Passe a instância para o visualizador
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
