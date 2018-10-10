from avalon.vendor.Qt import QtWidgets, QtCore


DEFAULT_COLOR = "#fb9c15"


class View(QtWidgets.QTreeView):
    data_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(View, self).__init__(parent=parent)

        # view settings
        self.setAlternatingRowColors(False)
        self.setSortingEnabled(True)
        self.setSelectionMode(self.SingleSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def get_indices(self):
        """Get the selected rows"""
        selection_model = self.selectionModel()
        return selection_model.selectedRows()
