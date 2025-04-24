#!/usr/bin/env python3
"""
main.py

Favorite Files Manager without symlink support.
Uses watchdog to auto-update favorite paths on move.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
)
from PyQt6.QtCore import Qt

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FavoriteFilesManager:
    """Manages favorites and persists to JSON."""

    def __init__(self, storage_path="favorites.json"):
        self.storage_path = storage_path
        self.favorites = self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                return json.load(open(self.storage_path))
            except json.JSONDecodeError:
                print(f"Warning: corrupted {self.storage_path}, starting fresh.")
        return []

    def _save(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.favorites, f, indent=2)

    def get_favorites(self):
        return self.favorites

    def add_favorite(self, path, description=""):
        norm = os.path.normpath(path)
        if any(f["path"] == norm for f in self.favorites):
            return False, "Already in favorites."
        self.favorites.append(
            {
                "path": norm,
                "description": description,
                "added_on": datetime.now().isoformat(),
            }
        )
        self._save()
        return True, f"Added: {norm}"

    def remove_favorite(self, index):
        if 0 <= index < len(self.favorites):
            removed = self.favorites.pop(index)
            self._save()
            return True, f"Removed: {removed['path']}"
        return False, "Invalid selection."

    def update_favorite_path(self, index, new_path):
        old = self.favorites[index]["path"]
        new = os.path.normpath(new_path)
        self.favorites[index]["path"] = new
        self.favorites[index]["updated_on"] = datetime.now().isoformat()
        self._save()
        return True, f"Moved: {old} → {new}"


class MoveEventHandler(FileSystemEventHandler):
    """Handles on_moved for favorites only."""

    def __init__(self, manager, notify):
        super().__init__()
        self.manager = manager
        self.notify = notify

    def on_moved(self, event):
        src = os.path.normpath(event.src_path)
        dest = os.path.normpath(event.dest_path)
        for idx, fav in enumerate(self.manager.get_favorites()):
            if fav["path"] == src:
                ok, msg = self.manager.update_favorite_path(idx, dest)
                self.notify(msg)


class WatchdogMonitor:
    """Watches each favorite's parent folder for move events."""

    def __init__(self, manager, notify):
        self.manager = manager
        self.handler = MoveEventHandler(manager, notify)
        self.observer = Observer()

    def start(self):
        parents = {Path(f["path"]).parent for f in self.manager.get_favorites()}
        for p in parents:
            if p.is_dir():
                self.observer.schedule(self.handler, str(p), recursive=False)
        # Observer.start() runs in its own thread
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Favorite Files Manager")
        self.resize(700, 500)

        self.manager = FavoriteFilesManager()
        self.monitor = WatchdogMonitor(self.manager, self._show_message)
        self.monitor.start()

        central = QWidget()
        vbox = QVBoxLayout(central)

        vbox.addWidget(QLabel("Your Favorites:"))
        self.list = QListWidget()
        vbox.addWidget(self.list)
        self._refresh_list()

        hbox = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._add_favorite)
        btn_rem = QPushButton("Remove")
        btn_rem.clicked.connect(self._remove_favorite)
        hbox.addWidget(btn_add)
        hbox.addWidget(btn_rem)
        vbox.addLayout(hbox)

        self.setCentralWidget(central)

        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)

    def closeEvent(self, event):
        self.monitor.stop()
        super().closeEvent(event)

    def _refresh_list(self):
        self.list.clear()
        for fav in self.manager.get_favorites():
            exists = Path(fav["path"]).exists()
            status = "✓" if exists else "✗"
            desc = fav.get("description", "")
            item = QListWidgetItem(f"[{status}] {fav['path']}  –  {desc}")
            self.list.addItem(item)

    def _add_favorite(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if not path:
            return
        desc, ok = QInputDialog.getText(self, "Description", "Optional:")
        success, msg = self.manager.add_favorite(path, desc if ok else "")
        self._show_message(msg)

    def _remove_favorite(self):
        idx = self.list.currentRow()
        success, msg = self.manager.remove_favorite(idx)
        self._show_message(msg)

    def _show_context_menu(self, pos):
        idx = self.list.currentRow()
        if idx < 0:
            return
        fav = self.manager.get_favorites()[idx]
        path = fav["path"]
        menu = QMenu(self)
        if Path(path).exists():
            menu.addAction(
                "Open",
                lambda: (
                    os.startfile(path)
                    if sys.platform == "win32"
                    else os.system(f"xdg-open '{path}'")
                ),
            )
        else:
            menu.addAction("Locate…", lambda: self._locate_moved(idx))
        menu.addAction("Remove", self._remove_favorite)
        menu.exec(self.list.viewport().mapToGlobal(pos))

    def _locate_moved(self, idx):
        fav = self.manager.get_favorites()[idx]
        name = Path(fav["path"]).name
        new, _ = QFileDialog.getOpenFileName(self, f"Locate {name}")
        if new:
            success, msg = self.manager.update_favorite_path(idx, new)
            self._show_message(msg)

    def _show_message(self, msg):
        # automatically refresh the list on any update
        self._refresh_list()
        QMessageBox.information(self, "Info", msg)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
