#!/usr/bin/env python3
"""
Favorite Files Manager

A PyQt6-based GUI application to manage your favorite files.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QDialog,
    QFormLayout,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon


class FavoriteFilesManager:
    """Manages a collection of favorite file paths."""

    def __init__(self, storage_path="favorites.json"):
        """Initialize the manager with a storage file path."""
        self.storage_path = storage_path
        self.favorites = self._load_favorites()

    def _load_favorites(self):
        """Load favorites from the storage file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(
                    f"Error: Could not decode {self.storage_path}. Using empty favorites list."
                )
                return []
        return []

    def _save_favorites(self):
        """Save favorites to the storage file."""
        with open(self.storage_path, "w") as f:
            json.dump(self.favorites, f, indent=2)

    def get_favorites(self):
        """Return the list of favorites."""
        return self.favorites

    def add_favorite(self, path, description=""):
        """Add a new favorite file."""
        # Normalize the path
        normalized_path = os.path.normpath(path)

        # Check if the file already exists in favorites
        for fav in self.favorites:
            if fav["path"] == normalized_path:
                return False, f"'{normalized_path}' is already in your favorites."

        # Add the file to favorites
        self.favorites.append(
            {
                "path": normalized_path,
                "description": description,
                "added_on": datetime.now().isoformat(),
            }
        )
        self._save_favorites()
        return True, f"Added '{normalized_path}' to favorites."

    def remove_favorite(self, index):
        """Remove a favorite file by index."""
        if not self.favorites or index < 0 or index >= len(self.favorites):
            return False, "Invalid index."

        removed = self.favorites.pop(index)
        self._save_favorites()
        return True, f"Removed '{removed['path']}' from favorites."


class AddFavoriteDialog(QDialog):
    """Dialog for adding a new favorite file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Favorite")
        self.resize(500, 150)

        layout = QFormLayout(self)

        self.path_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)

        self.description_input = QLineEdit()

        layout.addRow("File Path:", path_layout)
        layout.addRow("Description:", self.description_input)

        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addRow("", buttons_layout)

    def browse_file(self):
        """Open file dialog to browse for a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "All Files (*.*)"
        )
        if file_path:
            self.path_input.setText(file_path)

    def get_inputs(self):
        """Return the path and description inputs."""
        return self.path_input.text(), self.description_input.text()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Favorite Files Manager")
        self.resize(800, 600)

        self.manager = FavoriteFilesManager()

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create the favorites list
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemDoubleClicked.connect(self.open_file)

        # Create buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Favorite")
        self.remove_button = QPushButton("Remove Selected")
        self.refresh_button = QPushButton("Refresh List")

        self.add_button.clicked.connect(self.add_favorite)
        self.remove_button.clicked.connect(self.remove_favorite)
        self.refresh_button.clicked.connect(self.refresh_list)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.refresh_button)

        # Add widgets to main layout
        main_layout.addWidget(QLabel("Your Favorite Files:"))
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(button_layout)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Initial list refresh
        self.refresh_list()

    def refresh_list(self):
        """Refresh the favorites list."""
        self.list_widget.clear()

        for i, fav in enumerate(self.manager.get_favorites()):
            path = fav["path"]
            desc = fav.get("description", "No description")
            exists = Path(path).exists()

            item = QListWidgetItem()
            status = "✓" if exists else "✗"
            item.setText(f"[{status}] {path} - {desc}")
            item.setToolTip(
                f"Path: {path}\nDescription: {desc}\nExists: {'Yes' if exists else 'No'}"
            )

            self.list_widget.addItem(item)

    def add_favorite(self):
        """Show dialog to add a new favorite file."""
        dialog = AddFavoriteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, description = dialog.get_inputs()
            if path:
                # Check if file exists
                if not os.path.exists(path):
                    reply = QMessageBox.question(
                        self,
                        "File Not Found",
                        f"'{path}' does not exist. Add anyway?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return

                success, message = self.manager.add_favorite(path, description)
                self.show_message(message)
                if success:
                    self.refresh_list()
            else:
                self.show_message("Please enter a file path.")

    def remove_favorite(self):
        """Remove the selected favorite."""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            success, message = self.manager.remove_favorite(current_row)
            self.show_message(message)
            if success:
                self.refresh_list()
        else:
            self.show_message("Please select a favorite to remove.")

    def open_file(self, item):
        """Attempt to open the selected file."""
        row = self.list_widget.row(item)
        if row >= 0:
            path = self.manager.get_favorites()[row]["path"]
            if os.path.exists(path):
                try:
                    if sys.platform == "win32":
                        os.startfile(path)
                    else:
                        # For Linux and macOS
                        import subprocess

                        (
                            subprocess.call(("xdg-open", path))
                            if sys.platform == "linux"
                            else subprocess.call(("open", path))
                        )
                except Exception as e:
                    self.show_message(f"Error opening file: {str(e)}")
            else:
                self.show_message(f"File does not exist: {path}")

    def show_message(self, message):
        """Show an information message box."""
        QMessageBox.information(self, "Information", message)


def main():
    """Main entry point for the Favorite Files Manager application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
