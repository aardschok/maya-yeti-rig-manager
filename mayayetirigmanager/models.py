from avalon.tools.cbsceneinventory import model

from avalon.vendor.Qt import QtCore, QtWidgets, QtGui
from avalon.vendor import qtawesome
from avalon.style import colors

CONNECTED_ROLE = QtCore.Qt.UserRole + 2


class AssetModel(model.TreeModel):

    COLUMNS = ["label"]

    def add_items(self, items):
        """
        Add items to model with needed data
        Args:
            items(list): collection of item data

        Returns:
            None
        """

        self.beginResetModel()

        # Add the items sorted by label
        sorter = lambda x: x["label"]

        for item in sorted(items, key=sorter):

            asset_item = model.Node(data={"icon": "scissors"})
            asset_item.update(item)

            self.add_child(asset_item)

        self.endResetModel()

    def data(self, index, role):

        if not index.isValid():
            return

        if role == model.TreeModel.NodeRole:
            node = index.internalPointer()
            return node

        # Add icon
        if role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                node = index.internalPointer()
                icon = node.get("icon")
                if icon:
                    return qtawesome.icon("fa.{0}".format(icon),
                                          color=colors.default)

        return super(AssetModel, self).data(index, role)

    def get_indexes(self):
        indexes = []
        row_count = self.rowCount(QtCore.QModelIndex())
        for row in range(row_count):
            idx = self.index(row, 0, QtCore.QModelIndex())
            indexes.append(idx)

        return indexes


class MatchModel(AssetModel):
    """Model displaying a list of looks and matches for assets"""

    COLUMNS = ["label"]

    def __init__(self, parent=None):
        AssetModel.__init__(self, parent=parent)
        self._linked_index = None

    def set_linked_index(self, index):
        self._linked_index = index

    def add_items(self, items):
        """Add items to model with needed data

        An item exists of:
            {
                "subset": 'name of subset',
                "asset": asset_document
            }

        Args:
            items(list): collection of item data

        Returns:
            None
        """

        self.beginResetModel()

        for item in items:

            node = model.Node(data={"icon": "cube"})
            node.update(item)

            self.add_child(node)

        self.endResetModel()

    def data(self, index, role):

        # Set the connected item in italics
        if role == QtCore.Qt.FontRole:
            font = QtGui.QFont()
            node = index.internalPointer()
            if not self._linked_index:
                return font

            is_connected = self._linked_index in node.get("linkedIndex", [])
            if is_connected:
                font.setItalic(True)
                font.setBold(True)
            return font

        return super(MatchModel, self).data(index, role)
