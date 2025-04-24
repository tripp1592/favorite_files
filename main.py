#!/usr/bin/env python3
"""
Favorite Files Manager

A PyQt6-based GUI application to manage your favorite files.
"""

import os
import json
import sys
import fnmatch
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
    QMenu,
    QProgressDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction


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

    def update_favorite_path(self, index, new_path):
        """Update the path of a favorite file."""
        if not self.favorites or index < 0 or index >= len(self.favorites):
            return False, "Invalid index."

        old_path = self.favorites[index]["path"]
        self.favorites[index]["path"] = os.path.normpath(new_path)
        self.favorites[index]["updated_on"] = datetime.now().isoformat()
        self._save_favorites()
        return True, f"Updated path from '{old_path}' to '{new_path}'."


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


class FindMovedFileDialog(QDialog):
    """Dialog for finding a moved file."""

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Find Moved File: {filename}")
        self.resize(600, 150)
        self.filename = filename

        layout = QVBoxLayout(self)

        # Instructions
        layout.addWidget(QLabel(f"Select a new location for: {filename}"))

        # Path input
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.search_button = QPushButton("Auto Search")

        self.browse_button.clicked.connect(self.browse_file)
        self.search_button.clicked.connect(self.auto_search)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        path_layout.addWidget(self.search_button)

        layout.addLayout(path_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Path")
        self.cancel_button = QPushButton("Cancel")

        self.update_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def browse_file(self):
        """Open file dialog to browse for the moved file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Locate {self.filename}", "", f"{self.filename};;All Files (*.*)"
        )
        if file_path:
            self.path_input.setText(file_path)

    def auto_search(self):
        """Automatically search for the moved file in common locations."""
        common_locations = []

        # Add system-specific common locations
        if sys.platform == "win32":
            # Windows common locations
            drives = [
                f"{d}:\\"
                for d in "CDEFGHIJKLMNOPQRSTUVWXYZ"
                if os.path.exists(f"{d}:\\")
            ]
            user_dirs = [
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Pictures"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Music"),
            ]
            common_locations.extend(drives)
            common_locations.extend(user_dirs)
        else:
            # Linux/macOS common locations
            common_locations = [
                "/",
                os.path.expanduser("~"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Pictures"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Music"),
            ]

        # Show progress dialog
        progress = QProgressDialog(
            "Searching for moved file...", "Cancel", 0, len(common_locations), self
        )
        progress.setWindowTitle("Searching...")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Track found files
        found_files = []

        # Search in common locations
        for i, location in enumerate(common_locations):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            progress.setLabelText(f"Searching in {location}...")

            try:
                for root, dirs, files in os.walk(location):
                    if progress.wasCanceled():
                        break

                    # Check if the filename matches
                    for file in fnmatch.filter(files, self.filename):
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)

                    # Limit search depth to prevent too deep recursion
                    if root.count(os.sep) - location.count(os.sep) > 5:
                        dirs.clear()  # Don't go deeper than 5 levels
            except (PermissionError, OSError):
                continue

        progress.setValue(len(common_locations))

        # Show results
        if found_files:
            if len(found_files) == 1:
                # Only one file found, use it directly
                self.path_input.setText(found_files[0])
            else:
                # Multiple files found, let user choose
                chosen_path, ok = QInputDialog.getItem(
                    self,
                    "Multiple Files Found",
                    "Select the correct file:",
                    found_files,
                    0,
                    False,
                )
                if ok:
                    self.path_input.setText(chosen_path)
        else:
            QMessageBox.information(self, "Search Complete", "No matching files found.")

    def get_new_path(self):
        """Return the new path for the moved file."""
        return self.path_input.text()


class CreateSymlinkDialog(QDialog):
    """Dialog for creating a symlink to a file."""

    def __init__(self, original_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Symbolic Link")
        self.resize(600, 180)
        self.original_path = original_path

        layout = QVBoxLayout(self)

        # Source file info
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        source_label = QLabel(original_path)
        source_label.setStyleSheet("font-weight: bold;")
        source_layout.addWidget(source_label)
        layout.addLayout(source_layout)

        # Target path
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target location:"))
        self.target_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_location)

        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.browse_button)
        layout.addLayout(target_layout)

        # Warning about permissions
        if sys.platform == "win32":
            warning = QLabel(
                "Note: Creating symlinks on Windows may require administrative privileges or Developer Mode."
            )
            warning.setStyleSheet("color: #990000;")
            layout.addWidget(warning)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Symlink")
        self.cancel_button = QPushButton("Cancel")

        self.create_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def browse_location(self):
        """Open file dialog to choose a location for the symlink."""
        file_name = os.path.basename(self.original_path)
        target_path, _ = QFileDialog.getSaveFileName(
            self, "Select Symlink Location", file_name, f"Symlinks (*)"
        )
        if target_path:
            self.target_input.setText(target_path)

    def get_target_path(self):
        """Return the target path for the symlink."""
        return self.target_input.text()


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
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

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

    def show_context_menu(self, position):
        """Show context menu for list items."""
        item = self.list_widget.itemAt(position)

        if not item:
            return

        row = self.list_widget.row(item)
        fav = self.manager.get_favorites()[row]
        path = fav["path"]
        exists = Path(path).exists()

        menu = QMenu(self)

        # Common actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_file(item))
        open_action.setEnabled(exists)

        remove_action = QAction("Remove from Favorites", self)
        remove_action.triggered.connect(lambda: self.remove_favorite(row))

        # Add actions for moved files
        if not exists:
            find_moved_action = QAction("Find Moved File...", self)
            find_moved_action.triggered.connect(lambda: self.find_moved_file(row))
            menu.addAction(find_moved_action)
        else:
            # Add symlink option for existing files
            create_symlink_action = QAction("Create Symlink...", self)
            create_symlink_action.triggered.connect(lambda: self.create_symlink(row))
            menu.addAction(create_symlink_action)

        menu.addAction(open_action)
        menu.addAction(remove_action)
        menu.exec(self.list_widget.mapToGlobal(position))

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

    def remove_favorite(self, index=None):
        """Remove the selected favorite."""
        if index is None:
            index = self.list_widget.currentRow()

        if index >= 0:
            success, message = self.manager.remove_favorite(index)
            self.show_message(message)
            if success:
                self.refresh_list()
        else:
            self.show_message("Please select a favorite to remove.")

    def find_moved_file(self, index):
        """Find a file that has been moved from its original location."""
        if index >= 0:
            fav = self.manager.get_favorites()[index]
            original_path = fav["path"]
            filename = os.path.basename(original_path)

            dialog = FindMovedFileDialog(filename, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_path = dialog.get_new_path()

                if new_path and new_path != original_path:
                    if not os.path.exists(new_path):
                        reply = QMessageBox.warning(
                            self,
                            "File Not Found",
                            f"The selected path '{new_path}' does not exist. Update anyway?",
                            QMessageBox.StandardButton.Yes
                            | QMessageBox.StandardButton.No,
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return

                    success, message = self.manager.update_favorite_path(
                        index, new_path
                    )
                    self.show_message(message)
                    if success:
                        self.refresh_list()
                else:
                    self.show_message("No new path selected or path is the same.")

    def create_symlink(self, index):
        """Create a symlink to the selected favorite file."""
        if index >= 0:
            fav = self.manager.get_favorites()[index]
            original_path = fav["path"]

            if not os.path.exists(original_path):
                self.show_message(
                    f"The file '{original_path}' does not exist. Cannot create a symlink."
                )
                return

            dialog = CreateSymlinkDialog(original_path, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                target_path = dialog.get_target_path()

                if not target_path:
                    self.show_message("No target location specified.")
                    return

                if os.path.exists(target_path):
                    reply = QMessageBox.question(
                        self,
                        "File Already Exists",
                        f"'{target_path}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
                    # Remove existing file or symlink if overwriting
                    try:
                        if os.path.isdir(target_path) and not os.path.islink(
                            target_path
                        ):
                            self.show_message(
                                f"Cannot overwrite directory '{target_path}' with a symlink."
                            )
                            return
                        os.remove(target_path)
                    except OSError as e:
                        self.show_message(f"Error removing existing file: {str(e)}")
                        return

                # Create the symlink
                try:
                    os.symlink(original_path, target_path)
                    self.show_message(
                        f"Successfully created symlink at '{target_path}'"
                    )
                except OSError as e:
                    if sys.platform == "win32" and e.winerror == 1314:
                        # Error code for privilege issues on Windows
                        self.show_message(
                            "Permission denied. On Windows, creating symlinks requires:\n"
                            "1. Administrative privileges, or\n"
                            "2. Developer Mode enabled in Windows settings"
                        )
                    else:
                        self.show_message(f"Error creating symlink: {str(e)}")

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
                reply = QMessageBox.question(
                    self,
                    "File Not Found",
                    f"The file '{path}' no longer exists at this location. Would you like to find where it was moved?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.find_moved_file(row)

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
