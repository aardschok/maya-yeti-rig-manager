import os
import json
import logging
from collections import defaultdict

from maya import cmds

from avalon import io, api

import colorbleed.maya.lib as cb

log = logging.getLogger(__name__)


def get_workfile():
    """Get work file name

    Returns:
        str

    """
    path = cmds.file(query=True, sceneName=True) or "untitled"
    return os.path.basename(path)


def create_id_hash(nodes):
    """Create a hash based on cbId attribute value
    Args:
        nodes (list): a list of nodes

    Returns:
        dict
    """
    node_id_hash = defaultdict(list)
    for node in nodes:
        value = cb.get_id(node)
        if value is None:
            continue

        node_id_hash[value].append(node)

    return dict(node_id_hash)


def get_containers():
    """Collect all containers in the scene and collect all their nodes

    Returns:
        generator object

    """
    host = api.registered_host()

    for container in host.ls():
        nodes = cmds.sets(container["objectName"], query=True, nodesOnly=True)
        nodes = cmds.ls(nodes, long=True)

        # Update container
        container.update({"nodes": create_id_hash(nodes)})

        yield container


def create_node(container):
    """Create a simplified node for the tool

    Args:
        container(dict):

    Returns:
        dict

    """
    label = "%s - %s" % (container["namespace"], container["name"])
    return {"label": label,
            "nodes": container.get("nodes", []),
            "representation": container["representation"],
            "loader": container["loader"]
            }


def create_nodes(containers):
    return [create_node(container) for container in containers]


def get_source_ids(connections):
    """Return a list of unique source Ids

    Args:
        connections(dict): connection data

    Returns:
        list

    """
    return list(set(c["sourceID"] for c in connections))


def get_matches(rig_items, other_items):
    """Yields each item which matches for a Yeti rig

    The matching is based on the unique ID which is stored per
    unique connection in the connection data of the rig.

    Example of connection data:
        {
            "connections": ["worldMesh", "inMesh"],
            "sourceID": "123456789012345:098765",
            "destinationID: "098765432112345:123456"
         }

    Args:
        rig_items (list): list of Yeti rig nodes, list of dicts
        other_items (list): other items from scene, list of dicts

    Returns:
        generator object

    """

    # Get connection data per node
    for node in rig_items:
        metadata = get_connections(node["representation"])
        connections = metadata["inputs"]

        # Get the ids of the sources
        source_ids = get_source_ids(connections)

        # Get matches based on the ids
        for other in other_items:
            node_data = other["nodes"]
            if any(_id for _id in source_ids if _id in node_data):
                yield other


def get_connections(representation_id):
    """Get the metadata file from the data base

    Args:
        representation_id(str): representation ID

    Returns:
        dict
    """

    representation = io.find_one({"_id": io.ObjectId(representation_id)})

    path = api.get_representation_path(representation)
    path = path.replace("\\", "/")

    # Get metadata
    path, ext = os.path.splitext(path)
    data_path = "{}.rigsettings".format(path)

    with open(data_path, "r") as fp:
        metadata = json.load(fp)

    return metadata


def are_items_connected(rig_members_by_id, input_members_by_id, connections):
    """Check if the rig members are connected to the input members based
    on the connections from the metadata

    Args:
        rig_members_by_id(dict):  node hash based on cbId
        input_members_by_id(dict): node hash based on cbId
        connections(dict): metadata from the meta data file

    Returns:
        BOOL

    """

    for input in connections.get("inputs", []):

        input_nodes = input_members_by_id.get(input["sourceID"])
        input_node = input_nodes[0]

        rig_nodes = rig_members_by_id.get(input["destinationID"])
        rig_node = rig_nodes[0]

        connections = input["connections"]
        input_attr = "%s.%s" % (input_node, connections[0])
        rig_attr = "%s.%s" % (rig_node, connections[1])

        if cmds.isConnected(input_attr, rig_attr):
            return True

    return False


def connect(rig_members_by_id, input_members_by_id, connections, force=True):
    """Create a connection between source and input based on the meta data

    Args:
        rig_members_by_id(dict):  source data from the source item
        input_members_by_id(dict): input data from the input item
        connections(dict): metadata from the meta data file

        force(bool): Force connections between nodes, default is True

    Returns:
        None

    """

    for input in connections.get("inputs", []):

        input_nodes = input_members_by_id.get(input["sourceID"])
        input_node = input_nodes[0]

        rig_nodes = rig_members_by_id.get(input["destinationID"])
        rig_node = rig_nodes[0]

        connections = input["connections"]
        input_attr = "%s.%s" % (input_node, connections[0])
        rig_attr = "%s.%s" % (rig_node, connections[1])

        # Create easy to read attribute for messages
        src = input_attr.rsplit("|", 1)[-1]
        dest = rig_attr.rsplit("|", 1)[-1]

        if cmds.isConnected(input_attr, rig_attr):
            log.error("Source already connected to destination: %s -> %s" %
                      (src, dest))
            continue

        log.info("Connecting: %s -> %s" % (src, dest))

        cmds.connectAttr(input_attr, rig_attr, force=force)


def disconnect(rig_members_by_id, input_members_by_id, connections):
    """Break all connections between source and input nodes

    Args:
        rig_members_by_id(dict):  node hash based on cbId
        input_members_by_id(dict): node hash based on cbId
        connections(dict): metadata from the meta data file

    Returns:
        None

    """

    for connection in connections.get("inputs", []):

        input_nodes = input_members_by_id.get(connection["sourceID"])
        input_node = input_nodes[0]

        rig_nodes = rig_members_by_id.get(connection["destinationID"])
        rig_node = rig_nodes[0]

        connections = connection["connections"]
        input_attr = "%s.%s" % (input_node, connections[0])
        rig_attr = "%s.%s" % (rig_node, connections[1])

        # Create easy to read attribute for messages
        src = input_attr.rsplit("|", 1)[-1]
        dest = rig_attr.rsplit("|", 1)[-1]

        if not cmds.isConnected(input_attr, rig_attr):
            log.error("Source already disconnected from destination: %s -/- %s"
                      % (src, dest))
            continue

        log.info("Disconnecting: %s -> %s" % (src, dest))

        cmds.disconnectAttr(input_attr, rig_attr)
