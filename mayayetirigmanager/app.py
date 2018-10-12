import logging
import sys

from avalon import style
from avalon.tools import lib as toolslib

from avalon.vendor import qtawesome as qta
from avalon.vendor.Qt import QtWidgets, QtCore, QtGui

from . import lib
from .widgets import AssetOutliner, MatchOutliner

module = sys.modules[__name__]
module.window = None


class Window(QtWidgets.QWidget):
    UserRole = QtCore.Qt.UserRole

    connected = QtCore.Signal(list)
    disconnected = QtCore.Signal(list)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        title = "Yeti Rig Manager 1.1.0 - [%s]" % lib.get_workfile()
        geometry = (800, 400)

        self.log = logging.getLogger("Yeti Rig Manager")

        self.setObjectName("yetiRigManager")
        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setParent(parent)

        layout = QtWidgets.QVBoxLayout()

        # Control layout
        control_layout = QtWidgets.QHBoxLayout()

        force_checkbox = QtWidgets.QCheckBox("Force")
        force_checkbox.setChecked(True)

        refresh_button = QtWidgets.QPushButton()
        refresh_icon = qta.icon("fa.refresh", color="white")

        refresh_button.setIcon(refresh_icon)
        refresh_button.setFixedWidth(28)
        refresh_button.setFixedHeight(28)

        control_layout.addWidget(force_checkbox)
        control_layout.addStretch(True)
        control_layout.addWidget(refresh_button)

        view_layout = QtWidgets.QHBoxLayout()

        rig_view = AssetOutliner()
        match_view = MatchOutliner()

        view_layout.addWidget(rig_view)
        view_layout.addWidget(match_view)

        # Default action buttons
        action_button_layout = QtWidgets.QHBoxLayout()
        connect_button = QtWidgets.QPushButton("Connect")
        disconnect_button = QtWidgets.QPushButton("Disconnect")

        action_button_layout.addWidget(connect_button)
        action_button_layout.addWidget(disconnect_button)

        layout.addLayout(control_layout)
        layout.addLayout(view_layout)
        layout.addLayout(action_button_layout)

        self.setLayout(layout)

        self.force_checkbox = force_checkbox
        self.refresh_button = refresh_button
        self.connect_button = connect_button
        self.disconnect_button = disconnect_button

        self.rig_view = rig_view
        self.match_view = match_view

        self.resize(*geometry)

        self.connections()

    def connections(self):

        self.rig_view.selection_changed.connect(self.on_rig_selection_changed)

        self.refresh_button.clicked.connect(self.refresh)
        self.connect_button.clicked.connect(self.connect_container_nodes)
        self.disconnect_button.clicked.connect(self.disconnect_container_nodes)

    def on_rig_selection_changed(self):
        selection_model = self.rig_view.get_selection_model()
        indices = selection_model.selectedIndexes()
        if len(indices) != 1:
            return
        index = indices[0]

        self.match_view.model.set_linked_index(index)

        # The font will only update the widget gets focus
        self.match_view.setFocus()
        self.rig_view.setFocus()

    def refresh(self):

        self.rig_view.clear()
        self.match_view.clear()

        rig_items = []
        other_items = []

        # Separate based on loader
        for container in lib.get_containers():
            node = lib.create_node(container)
            if node["loader"] == "YetiRigLoader":
                rig_items.append(node)
            else:
                other_items.append(node)

        match_items = lib.get_matches(rig_items, other_items)
        print(match_items)

        self.rig_view.add_items(rig_items)
        self.match_view.add_items(match_items)

        self.log.info("Refreshed ..")

        self._link_connected()

    def connect_container_nodes(self):

        force = self.force_checkbox.isChecked()

        rig_node = self._get_rig_node()
        match_node = self._get_match_node()

        # Get needs information
        connections = lib.get_connections(rig_node["representation"])
        rig_members_by_id = rig_node["nodes"]
        input_members_by_id = match_node["nodes"]

        lib.connect(rig_members_by_id, input_members_by_id, connections, force)

        self.refresh()

    def disconnect_container_nodes(self):

        rig_node = self._get_rig_node()
        if not rig_node:
            self.log.error("Please select one rig item")

        match_node = self._get_match_node()
        if not match_node:
            self.log.error("Please select one match item")

        connections = lib.get_connections(rig_node["representation"])

        rig_members_by_id = rig_node["nodes"]
        input_members_by_id = match_node["nodes"]

        lib.disconnect(rig_members_by_id, input_members_by_id, connections)

        self.refresh()

    def _get_rig_node(self):
        items = self.rig_view.get_selected_items()
        if len(items) != 1:
            return

        item = items[0]
        return item

    def _get_match_node(self):
        items = self.match_view.get_selected_items()
        if len(items) != 1:
            return

        item = items[0]
        return item

    def _link_connected(self):

        rig_model = self.rig_view.model
        rig_indexes = rig_model.get_indexes()

        match_model = self.match_view.model
        match_indexes = match_model.get_indexes()

        node_role = rig_model.NodeRole

        for rig_index in rig_indexes:
            if not rig_index.isValid():
                continue

            rig_node = rig_model.data(rig_index, node_role)
            rig_members_by_id = rig_node["nodes"]
            connections = lib.get_connections(rig_node["representation"])

            for match_index in match_indexes:
                if not match_index.isValid():
                    continue
                match_node = match_model.data(match_index, node_role)
                match_members_by_id = match_node["nodes"]

                if not lib.are_items_connected(rig_members_by_id,
                                               match_members_by_id,
                                               connections):
                    continue
                self.log.info("Found connected items..")

                match_node.update({"linkedIndex": [rig_index]})
                break

    def _find_rig_node_index(self, label):

        model = self.rig_view.model

        indexes = model.get_indexes()
        for idx in indexes:
            if not idx.isValid():
                continue

            node = model.data(idx, model.NodeRole)
            if node["label"] == label:
                return idx

    def _find_match_node_index(self, label):

        model = self.match_view.model

        indexes = model.get_indexes()
        for idx in indexes:
            if not idx.isValid():
                continue

            node = model.data(idx, model.NodeRole)
            if node["label"] == label:
                return idx


def show(parent=None):
    """Display Loader GUI

    """

    try:
        module.window.close()
        del module.window
    except (RuntimeError, AttributeError):
        pass

    if parent is None:
        # Get Maya main window
        top_level_widgets = QtWidgets.QApplication.topLevelWidgets()
        parent = next(widget for widget in top_level_widgets
                      if widget.objectName() == "MayaWindow")

    with toolslib.application():
        window = Window(parent=parent)
        window.setStyleSheet(style.load_stylesheet())
        window.show()
        window.refresh()

        module.window = window
