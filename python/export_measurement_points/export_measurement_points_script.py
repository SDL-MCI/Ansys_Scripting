#SPDX-FileCopyrightText: 2025 Matthias Panny <matthias.panny@mci.edu>
#SPDX-License-Identifier: MIT

"""
Python Code object that needs to be added to the main "Model" in Ansys Mechanical
It requires the "Target Callback" setting to be "After Object Changed"

Tracks all changes to a Named Selection of a certain name (default: "measurePoints") and exports the coordinates of the nodes in this selection after every change to a *.txt-file (default: "coordsMP.txt")
"""

def after_object_changed(this, object_changed, property_name):
    """
    Called after an object is changed.
    Keyword Arguments :
    this -- this python object
    object_changed -- The object that was changed
    property_name -- The property that was changed
    """

    def send_message(message, severity = MessageSeverityType.Info):
        """
        Helper that allows sending a debug message through the Ansys messages system
        Parameter `message` must be castable to `str`
        """
        msg_obj = Ansys.Mechanical.Application.Message(str(message), severity)
        ExtAPI.Application.Messages.Add(msg_obj)

    import Ansys.ACT.Automation.Mechanical.NamedSelection as named_selection

    # Exit if changed object was not a NamedSelection
    if(object_changed.GetType() != named_selection):
        return

    ns = object_changed
    observed_ns_name = this.GetCustomPropertyByPath("Export Settings/Named selection to export").Value

    # Exit if the changed NamedSelection was not the one under observation
    if ns.Name.ToUpper() != observed_ns_name.ToUpper():
        return

    # Retrieve debug property and cast to boolean --> 0 = False, 1 = True
    DEBUG = bool(this.GetCustomPropertyByPath("Debug Settings/Debug printing").Value)

    def write_node_coords_to_file(mesh, nodes, file_path):
        """
        Writes node coordinates to given file.
        
        Parameters
        ----------
        mesh : Ans.DataProcessing.Model().Mesh
        Analysis mesh
        nodes : Ansys.ACT.Interfaces.Common.ISelectionInfo
        Nodes of the named selection to export
        file_path : System.IO.Path
        Path of export file
        """

        # Can only directly retrieve node coods if the geometry in the named selection is a mesh node
        if nodes.SelectionType != Ansys.ACT.Interfaces.Common.SelectionTypeEnum.MeshNodes:
            raise Exception("Error: Named selection location is of type \"{}\" but should be \"MeshNodes\"".format(str(nodes.SelectionType)))

        file_content = []
        for num, id in enumerate(nodes.Ids):
            node = mesh.NodeById(id)
            file_content.append("{:20.5f}{:20.5f}{:20.5f}".format(node.X, node.Y, node.Z))
        
        with open(file_path, "w") as f:
            file_string = "\n".join(file_content)
            f.write(file_string)
        
        if DEBUG:
            send_message("Exported {} nodes as measurement points".format(len(nodes.Ids)))

    import mech_dpf
    import Ans.DataProcessing as dpf
    from System.IO import Path
    
    dataSource = mech_dpf.GetDataSources()
    model = dpf.Model(dataSource.ResultFilePath)
    user_files_path = Path.GetFullPath(Path.Combine(dataSource.ResultFilePath, "..\\..\\..\\..\\user_files"))
    
    if DEBUG:
        send_message("Exporting to user files path: " + str(user_files_path))
    
    file_name = this.GetCustomPropertyByPath("Export Settings/File name for export").Value
    output_path = Path.Combine(user_files_path, file_name)
    
    write_node_coords_to_file(model.Mesh, ns.Location, output_path)



