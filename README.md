## Yeti Rig Manager for Maya

The goal of this tool is to eliminate the redundant tasks which are required
to connect animated or static meshes to the Yeti rigs in order to position it.

[![Image from Gyazo](https://i.gyazo.com/d58d91ac1916bf46a423984642805f7c.png)](https://gyazo.com/d58d91ac1916bf46a423984642805f7c)

The artist will be have a clear overview of the loaded Yeti rigs and possible 
matching content. By selecting a single item from both views the user is able
to connect or disconnect the items.


The matching are based on the unique ID which is stored per unique connection in the connection data of the rig.

    Example of connection data:
        {
            "connections": ["worldMesh", "inMesh"],
            "sourceID": "123456789012345:098765",
            "destinationID: "098765432112345:123456"
         }


### Dependencies
* [Avalon](https://github.com/getavalon)
* [Colorbleed Config](https://github.com/Colorbleed/colorbleed-config)
* Autodesk Maya