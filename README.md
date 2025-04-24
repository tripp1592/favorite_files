# Favorite Files Manager

A PyQt6 GUI application that lets you bookmark files and **automatically updates their paths** when you move them—no manual refresh needed.

## Description

- **Add** any file to your favorites list.
- **Open** favorites directly from the app.
- **Detect** file moves in real time (via watchdog) and **auto–update** paths.
- **Remove** favorites you no longer need.

## Features

- **Real-time move detection** with [watchdog](https://pypi.org/project/watchdog/).  
- **Minimal UI**: just Add & Remove buttons—no manual “Refresh.”  
- **Single JSON store** (`favorites.json`) for persistence.

## Prerequisites

- Python 3.7+  
- [PyQt6](https://pypi.org/project/PyQt6/)  
- [watchdog](https://pypi.org/project/watchdog/)  

## Installation

```powershell
git clone https://github.com/yourusername/favorite-files.git
cd favorite-files
uv venv
uv pip install PyQt6 watchdog
```

## Running

```powershell
uv run main.py
```

## Usage

1. **Add** a file: click **Add**, select a file, optionally enter a description.  
2. **Open** a favorite: right-click and choose **Open** (if it still exists).  
3. **Locate** moved files: if a favorite shows ✗, right-click **Locate…** and select its new location.  
4. **Remove** a favorite: right-click and choose **Remove**, or select it and click **Remove**.

The app will **automatically refresh** whenever it sees a watched file move.

## Project Structure

```
├─ main.py
├─ README.md
├─ favorites.json      ← your stored favorites
└─ changes.log         ← development changelog
```
