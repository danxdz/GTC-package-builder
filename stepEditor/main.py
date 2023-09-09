import sys
from PyQt5.QtWidgets import QApplication
from GUI import StepFileViewer

def main():
    app = QApplication(sys.argv)
    viewer = StepFileViewer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
