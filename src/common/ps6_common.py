import loguru as logger
from PySide6.QtWidgets import QFileDialog

# -----------------------------------------------------------------------------
def open_file_dialog(parent_obj: object, start_path: str, file_filter: str="") -> str:
    logger.debug("Open File Dialog!")
    if file_filter == "":
        file_filter = "All Files (*.*)"
    # file_filter = f"OSCAL Files (*.xml *.json *.yaml *{OSCAL_PROJECT_EXTENSION});; All Files (*.*)"

    file = QFileDialog.getOpenFileName(
        parent=parent_obj,
        caption="Open OSCAL Project",
        # directory=os.getcwd(),
        dir=start_path,
        filter=file_filter
    )

    logger.debug(f"File selected: {file[0]}")
    return file[0]
# -----------------------------------------------------------------------------


# =============================================================================
#  --- MAIN: Only runs if the module is executed stand-alone. ---
# =============================================================================
if __name__ == '__main__':
    print("PySide6 Common Library. Not intended to be run as a stand-alone file.")

