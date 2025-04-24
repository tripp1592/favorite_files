# instructions
## Project Tools
- this project is to use python and the python UV packaging manager
- terminal commands should be in powershell format
- only use uv commands, for example:
  - instead of python main.py, we would use uv run main.py
  - even making virtual environments is done through using uv venv
## GUI
- use pyqt6 as the framework for the GUI 

## Code Generation
- always use main.py as an entry point with the:
    ```
    if __name__ == "__main__:
        main()
    ```
    code block
- put summaries of changes into a file in root project folder in changes.log
  - please insert date in iso format and append a time for each change
