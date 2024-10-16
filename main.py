import sys
from PyQt5.QtWidgets import QApplication
from gui_components import PDFSplitterApp

class SecureRestorableStateApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
    
    def event(self, event):
        if event.type() == 215:  # NSApplicationDelegate.applicationSupportsSecureRestorableState:
            return True
        return super().event(event)

if __name__ == '__main__':
    app = SecureRestorableStateApp(sys.argv)
    ex = PDFSplitterApp()
    sys.exit(app.exec_())
