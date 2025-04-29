import sys

from PyQt5.QtWidgets import QApplication

from model import BikeRentalModel
from view import MainWindow
from controller import BikeRentalController

def main():
    app = QApplication(sys.argv)
    model = BikeRentalModel("bike_rental.db")
    view = MainWindow()
    controller = BikeRentalController(model, view)
    view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
