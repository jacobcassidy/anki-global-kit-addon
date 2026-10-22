"""Choose several existing note types for one confirmed settings action."""

from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)


def select_note_types(parent: QWidget, names: list[str]) -> tuple[str, ...]:
    """Return checked note type names, or no names when the dialog is canceled."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Add Syntax Styles")
    dialog.resize(440, 420)
    layout = QVBoxLayout(dialog)
    description = QLabel(
        "Choose note types to use your syntax themes during card review.\n"
        "Note types that already include the stylesheet are omitted.",
        dialog,
    )
    description.setWordWrap(True)
    layout.addWidget(description)
    checklist = QListWidget(dialog)
    for name in names:
        item = QListWidgetItem(name, checklist)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
    layout.addWidget(checklist)
    selection_row = QHBoxLayout()
    select_all = QPushButton("Select All", dialog)
    clear_selection = QPushButton("Clear Selection", dialog)
    for button in (select_all, clear_selection):
        button.setAutoDefault(False)
        selection_row.addWidget(button)
    selection_row.addStretch()
    layout.addLayout(selection_row)
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        dialog,
    )
    continue_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert continue_button is not None
    continue_button.setText("Continue")
    continue_button.setEnabled(False)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    def selected_names() -> tuple[str, ...]:
        return tuple(
            checklist.item(index).text()
            for index in range(checklist.count())
            if checklist.item(index).checkState() == Qt.CheckState.Checked
        )

    def set_checked(state: Qt.CheckState) -> None:
        for index in range(checklist.count()):
            checklist.item(index).setCheckState(state)

    checklist.itemChanged.connect(
        lambda _item: continue_button.setEnabled(bool(selected_names()))
    )
    select_all.clicked.connect(lambda: set_checked(Qt.CheckState.Checked))
    clear_selection.clicked.connect(lambda: set_checked(Qt.CheckState.Unchecked))
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    selected = selected_names() if accepted else ()
    dialog.deleteLater()
    return selected
