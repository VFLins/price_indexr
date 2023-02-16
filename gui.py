from PyQt5.QtWidgets import QApplication, QLabel

app = QApplication([])
app.setStyle('Fusion')

label = QLabel('hello world')
label.show()
app.exec_()