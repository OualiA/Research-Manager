import sys
import traceback
from PySide6.QtWidgets import QApplication
from controllers.main_controller import MainWindow



def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

    except Exception as e:
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main()
