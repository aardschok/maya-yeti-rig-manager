from avalon.vendor.Qt import QtWidgets, QtCore

# TODO: expose this better in avalon core
from avalon.tools.projectmanager.widget import (
    preserve_selection,
    preserve_expanded_rows
)

from . import models, lib, views


NODEROLE = QtCore.Qt.UserRole + 1
MODELINDEX = QtCore.QModelIndex()


class AssetOutliner(QtWidgets.QWidget):

    refreshed = QtCore.Signal()
    selection_changed = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Rigs:")
        title.setAlignment(QtCore.Qt.AlignLeft)
        title.setStyleSheet("font-weight: bold; font-size: 12px")

        model = models.AssetModel()
        view = views.View()
        view.setModel(model)
        view.setSortingEnabled(False)
        view.setHeaderHidden(True)
        view.setMinimumHeight(180)
        view.setIndentation(10)

        layout.addWidget(title)
        layout.addWidget(view)

        selection_model = view.selectionModel()
        selection_model.selectionChanged.connect(self.selection_changed)

        self.view = view
        self.model = model
        self._selection_model = selection_model

        self.setLayout(layout)

    def clear(self):
        self.model.clear()

        # fix looks remaining visible when no items present after "refresh"
        # todo: figure out why this workaround is needed.
        self.selection_changed.emit()

    def clear_selection(self):
        flags = self._selection_model.Clear
        self._selection_model.select(QtCore.QModelIndex(), flags)

    def select_index(self, index, flags=None):
        flags = flags or self._selection_model.ClearAndSelect
        self._selection_model.select(index, flags)

    def add_items(self, items):
        """Add new items to the outliner"""

        self.model.add_items(items)
        self.refreshed.emit()

    def get_selection_model(self):
        return self.view.selectionModel()

    def get_selected_items(self):
        """Get current selected items from view

        Returns:
            list: list of dictionaries
        """

        selection_model = self.view.selectionModel()
        items = [row.data(NODEROLE) for row in selection_model.selectedRows(0)]

        return items

    def get_all_assets(self):
        """Add all items from the current scene"""

        with preserve_expanded_rows(self.view):
            with preserve_selection(self.view):
                self.clear()
                containers = lib.get_containers()
                items = lib.create_node(containers)
                self.add_items(items)

        return len(items) > 0

    def get_selected_assets(self):
        """Add all selected items from the current scene"""
        raise NotImplementedError

    def get_nodes(self, selection=False):
        """Find the nodes in the current scene per asset."""
        raise NotImplementedError

        items = self.get_selected_items()

        # Collect all nodes by hash (optimization)
        # if not selection:
        #     nodes = cmds.ls(dag=True,  long=True)
        # else:
        #     nodes = commands.get_selected_nodes()
        # id_nodes = commands.create_asset_id_hash(nodes)
        #
        # # Collect the asset item entries per asset
        # # and collect the namespaces we'd like to apply
        # assets = dict()
        # asset_namespaces = defaultdict(set)
        # for item in items:
        #     asset_id = str(item["asset"]["_id"])
        #     asset_name = item["asset"]["name"]
        #     asset_namespaces[asset_name].add(item.get("namespace"))
        #
        #     if asset_name in assets:
        #         continue
        #
        #     assets[asset_name] = item
        #     assets[asset_name]["nodes"] = id_nodes.get(asset_id, [])
        #
        # # Filter nodes to namespace (if only namespaces were selected)
        # for asset_name in assets:
        #     namespaces = asset_namespaces[asset_name]
        #
        #     # When None is present there should be no filtering
        #     if None in namespaces:
        #         continue
        #
        #     # Else only namespaces are selected and *not* the top entry so
        #     # we should filter to only those namespaces.
        #     nodes = assets[asset_name]["nodes"]
        #     nodes = [node for node in nodes if
        #              commands.get_namespace_from_node(node) in namespaces]
        #     assets[asset_name]["nodes"] = nodes
        #
        # return assets

    def select_asset_from_items(self):
        """Select nodes from listed asset"""

        # items = self.get_nodes(selection=False)
        # nodes = []
        # for item in items.values():
        #     nodes.extend(item["nodes"])
        #
        # commands.select(nodes)

        raise NotImplementedError


class MatchOutliner(QtWidgets.QWidget):

    selection_changed = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # look manager layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Looks from database
        title = QtWidgets.QLabel("Matches:")
        title.setAlignment(QtCore.Qt.AlignLeft)
        title.setStyleSheet("font-weight: bold; font-size: 12px")

        model = models.MatchModel()
        view = views.View()
        view.setModel(model)
        view.setSortingEnabled(False)
        view.setHeaderHidden(True)
        view.setMinimumHeight(180)
        view.setIndentation(10)

        layout.addWidget(title)
        layout.addWidget(view)

        selection_model = view.selectionModel()
        selection_model.selectionChanged.connect(self.selection_changed)

        self.view = view
        self.model = model
        self._selection_model = selection_model

    def clear(self):
        self.model.clear()

    def add_items(self, items):
        self.model.add_items(items)

    def clear_selection(self):
        flags = self._selection_model.Clear
        self._selection_model.select(QtCore.QModelIndex(), flags)

    def select_index(self, index, flags=None):
        flags = flags or self._selection_model.ClearAndSelect
        self._selection_model.select(index, flags)

    def get_selected_items(self):
        """Get current selected items from view

        Returns:
            list: list of dictionaries
        """

        datas = [i.data(NODEROLE) for i in self.view.get_indices()]
        items = [d for d in datas if d is not None]  # filter Nones

        return items
