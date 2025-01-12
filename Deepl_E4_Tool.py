import sys
import deepl
import json
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QTextEdit, QPushButton, QComboBox, QProgressBar, QLabel, QCheckBox, QButtonGroup


with open('config.json', 'r') as f:
    config = json.load(f)
    api_keys = config.get('api_keys', [])
    src_langs = config.get('src_langs', [])
    target_langs = config.get('target_langs', [])
    e4_tool_key = config.get('e4_tool_key')

used_api = 'used_api.json'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E4_Tool")
        self.setGeometry(100, 100, 500, 500)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.tab_widget.addTab(self.tab1, "E4 text")
        self.tab_widget.addTab(self.tab2, "Translator")
        self.tab_widget.addTab(self.tab3, "Using keys")

        self.create_excel_like_columns(self.tab1)
        self.create_text_column(self.tab1)
        self.create_buttons(self.tab1)

        self.create_translator_tab(self.tab2)
        self.create_usage_tab(self.tab3)

        self.load_settings()

    def create_excel_like_columns(self, parent):
        layout = QVBoxLayout()
        self.table = QTableWidget(10, 3)  # Create a table with 5 rows and 3 columns
        self.table.setHorizontalHeaderLabels(["Key", "Value", "Translation"])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)

        layout.addWidget(self.table)
        parent.setLayout(layout)

    def create_text_column(self, parent):
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setAcceptRichText(False)
        
        layout.addWidget(text_edit)
        parent.setLayout(layout)

    def create_buttons(self, parent):
        layout = parent.layout()
        button_layout = QHBoxLayout()

        insert_button = QPushButton("Вставити текст")
        insert_button.clicked.connect(self.insert_text)
        button_layout.addWidget(insert_button)

        copy_button = QPushButton("Копіювати текст")
        copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(copy_button)

        layout.addLayout(button_layout)

    def create_translator_tab(self, parent):
        layout = QVBoxLayout()

        self.source_text_edit = QTextEdit()
        self.source_text_edit.setAcceptRichText(False)
        layout.addWidget(self.source_text_edit)

        self.target_text_edit = QTextEdit()
        self.target_text_edit.setAcceptRichText(False)
        layout.addWidget(self.target_text_edit)

        language_layout = QHBoxLayout()

        self.source_language_combo = QComboBox()
        self.source_language_combo.addItems(src_langs)
        language_layout.addWidget(self.source_language_combo)

        self.target_language_combo = QComboBox()
        self.target_language_combo.addItems(target_langs)
        language_layout.addWidget(self.target_language_combo)

        layout.addLayout(language_layout)

        translate_button = QPushButton("Перекласти")
        translate_button.clicked.connect(self.translate_text)
        layout.addWidget(translate_button)

        parent.setLayout(layout)

    def create_usage_tab(self, parent):
        layout = QVBoxLayout()

        self.api_checkboxes = []
        self.usage_labels = []
        self.usage_bars = []
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        for api_key in api_keys:
            checkbox = QCheckBox(api_key)
            self.button_group.addButton(checkbox)
            checkbox.stateChanged.connect(self.update_translator)
            layout.addWidget(checkbox)
            self.api_checkboxes.append(checkbox)

            label = QLabel(f"API Key: {api_key}")
            layout.addWidget(label)
            self.usage_labels.append(label)

            progress_bar = QProgressBar()
            layout.addWidget(progress_bar)
            self.usage_bars.append(progress_bar)

        self.update_usage()

        parent.setLayout(layout)

    def update_usage(self):
        for i, api_key in enumerate(api_keys):
            try:
                translator = deepl.Translator(api_key)
                usage = translator.get_usage()
                character_limit = usage.character.limit
                character_count = usage.character.count
                remaining = character_limit - character_count

                self.usage_labels[i].setText(f"API Key: {api_key} - {remaining} characters remaining out of {character_limit}")
                self.usage_bars[i].setMaximum(character_limit)
                self.usage_bars[i].setValue(character_count)
            except Exception as e:
                self.usage_labels[i].setText(f"API Key: {api_key} - Error: {str(e)}")

    def update_translator(self):
        for checkbox in self.api_checkboxes:
            if checkbox.isChecked():
                api_key = checkbox.text()
                global translator
                translator = deepl.Translator(api_key)
                self.save_settings(api_key)
                break

    def save_settings(self, api_key):
        settings = {'selected_api_key': api_key}
        with open(used_api, 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(used_api, 'r') as f:
                settings = json.load(f)
                selected_api_key = settings.get('selected_api_key', api_keys[0])
                for checkbox in self.api_checkboxes:
                    if checkbox.text() == selected_api_key:
                        checkbox.setChecked(True)
                        break
        except FileNotFoundError:
            self.api_checkboxes[0].setChecked(True)

    def insert_text(self):
        # Очистити таблицю перед вставкою нового тексту
        self.table.clearContents()
        self.table.setRowCount(0)

        clipboard = QtWidgets.QApplication.clipboard()
        text = clipboard.text()

        # Розбиваємо текст з буфера обміну на рядки та стовпці
        rows = text.strip().split('\n')
        
        # Вставляємо рядки в таблицю
        for row_idx, row in enumerate(rows):
            columns = row.split('\t')
            self.table.insertRow(row_idx)
            for col_idx, column in enumerate(columns):
                self.table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(column))
        
        # Викликаємо функцію перекладу після вставки тексту
        self.translate()


    def copy_text(self):
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        clipboard = QtWidgets.QApplication.clipboard()
        text = '\n'.join(['\t'.join([self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(col_count)])
                          for row in range(row_count)])
        clipboard.setText(text)


    def keyPressEvent(self, event):
        """Перехоплюємо комбінації клавіш для вставки та копіювання тексту."""
        if event.matches(QtGui.QKeySequence.Paste):  # Ctrl + V
            self.insert_text()
            event.accept()
            self.translate()
        elif event.matches(QtGui.QKeySequence.Copy):  # Ctrl + C
            self.copy_selected_cells()
            event.accept()
        else:
            super().keyPressEvent(event)

    def copy_selected_cells(self):
        """Копіюємо виділені клітинки таблиці у буфер обміну."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        copied_text = ""
        for selection_range in selected_ranges:
            for row in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                row_text = []
                for col in range(selection_range.leftColumn(), selection_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    row_text.append(item.text() if item else "")
                copied_text += "\t".join(row_text) + "\n"

        # Копіюємо текст у буфер обміну
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(copied_text.strip())


    def translate(self):
        row_count = self.table.rowCount()
        for row in range(row_count):
            col1_text = self.table.item(row, 0)
            col2_text = self.table.item(row, 1)
            # if col1_text and col2_text and col1_text.text().strip() == e4_tool_key:
            if col1_text and col2_text and (e4_tool_key is None or col1_text.text().strip() == e4_tool_key):

                try:
                    translated_result = translator.translate_text(col2_text.text(), target_lang="UK")
                    translated_text = translated_result.text if hasattr(translated_result, 'text') else "Error: No translation result"
                    self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(translated_text)) 
                except Exception as e:
                    self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"Error: {str(e)}"))

    def translate_text(self):
        source_text = self.source_text_edit.toPlainText()
        source_lang = self.source_language_combo.currentText()
        target_lang = self.target_language_combo.currentText()
        try:
            translated_result = translator.translate_text(source_text, source_lang=source_lang, target_lang=target_lang)
            translated_text = translated_result.text if hasattr(translated_result, 'text') else "Error: No translation result"
            self.target_text_edit.setPlainText(translated_text)
        except Exception as e:
            self.target_text_edit.setPlainText(f"Error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
