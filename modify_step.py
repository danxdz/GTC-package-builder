import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog
from collections import defaultdict

class StepFileViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.tree_widget = QTreeWidget(self)
        layout.addWidget(self.tree_widget)

        self.load_button = QPushButton('Open STEP File', self)
        self.load_button.clicked.connect(self.openFile)
        layout.addWidget(self.load_button)

        self.central_widget.setLayout(layout)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('STEP File Viewer')
        self.show()

    def openFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "Open STEP File", "", "STEP Files (*.stp *.step);;All Files (*)", options=options)

        if fileName:
            self.parseStepFile(fileName)

    def parseStepFile(self, filename):
        with open(filename, 'r') as file:
            step_content = file.readlines()

        # Clear the previous tree
        self.tree_widget.clear()

        # Create a dictionary to store categories and their elements
        category_dict = defaultdict(list)
        current_category = None

        for line in step_content:
            line = line.strip()

            if line.startswith('#'):
                # Extract the name of the element from #number=ELEMENT_NAME(PARAMETERS)
                element_name = line.split('=')[1].split('(')[0].strip()

                # Check if the category already exists in the dictionary
                if element_name in category_dict:
                    category_dict[element_name].append(line)
                else:
                    category_dict[element_name] = [line]

        # Populate the tree widget with categories and elements
        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "Categories")

        for category, elements in category_dict.items():
            category_item = QTreeWidgetItem(root)
            category_item.setText(0, category)

            for element in elements:
                element_item = QTreeWidgetItem(category_item)
                element_item.setText(0, element)

def main():
    app = QApplication(sys.argv)
    viewer = StepFileViewer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
