#!/usr/bin/env python
import xml.dom.minidom
#import xml.dom.ext # python 2.5 and later


class VTK_XML_Serial_Unstructured:
    def __init__(self):
        pass


    def create_doc(self, (pos_list, radii, colors, tensors)):
        # Document and root element
        doc = xml.dom.minidom.Document()
        root_element = doc.createElementNS("VTK", "VTK_file")
        root_element.setAttribute("type", "Unstructured_grid")
        root_element.setAttribute("version", "0.1")
        root_element.setAttribute("byte_order", "Little_endian")
        doc.appendChild(root_element)

        # Unstructured grid element
        unstructured_grid = doc.createElementNS("VTK", "Unstructured_grid")
        root_element.appendChild(unstructured_grid)

        # Piece 0 (only one)
        # The "Piece" elements are meant for multiple pieces of *geometry*.  
        # They are meant for streaming computation to reduce memory usage.  
        # All the pieces have to have the same set of data arrays.
        # So we can not use that to group particles, spheres and cylinders 
        # into 1 file. _use .pvd file using parts for that.
        piece = doc.createElementNS("VTK", "_piece")
        piece.setAttribute("NumberOf_points", str(len(pos_list)))
        piece.setAttribute("NumberOf_cells", "0")
        unstructured_grid.appendChild(piece)


        # Points.
        points = doc.createElementNS("VTK", "_points")
        piece.appendChild(points)

        # Point location data.
        point_coords = doc.createElementNS("VTK", "Data_array")
        point_coords.setAttribute("type", "_float32")
        point_coords.setAttribute("format", "ascii")
        point_coords.setAttribute("NumberOf_components", "3")
        points.appendChild(point_coords)

        string = str()
        for pos in pos_list:
            string = string + str(pos[0]) + ' ' + str(pos[1]) + \
                     ' ' + str(pos[2]) + ' '
        point_coords_data = doc.createTextNode(string)
        point_coords.appendChild(point_coords_data)


        # Cells.
        # Don't remove.
        cells = doc.createElementNS("VTK", "_cells")
        piece.appendChild(cells)

        # Cell locations.
        cell_connectivity = doc.createElementNS("VTK", "Data_array")
        cell_connectivity.setAttribute("type", "_int32")
        cell_connectivity.setAttribute("_name", "connectivity")
        cell_connectivity.setAttribute("format", "ascii")        
        cells.appendChild(cell_connectivity)

        # Cell location data.
        connectivity = doc.createTextNode("0")
        cell_connectivity.appendChild(connectivity)

        cell_offsets = doc.createElementNS("VTK", "Data_array")
        cell_offsets.setAttribute("type", "_int32")
        cell_offsets.setAttribute("_name", "offsets")
        cell_offsets.setAttribute("format", "ascii")                
        cells.appendChild(cell_offsets)
        offsets = doc.createTextNode("0")
        cell_offsets.appendChild(offsets)

        cell_types = doc.createElementNS("VTK", "Data_array")
        cell_types.setAttribute("type", "U_int8")
        cell_types.setAttribute("_name", "types")
        cell_types.setAttribute("format", "ascii")                
        cells.appendChild(cell_types)
        types = doc.createTextNode("1")
        cell_types.appendChild(types)


        # Point data.
        point_data = doc.createElementNS("VTK", "Point_data")
        piece.appendChild(point_data)

        # Radii.
        if len(radii) > 0:
            radii_node = doc.createElementNS("VTK", "Data_array")
            radii_node.setAttribute("_name", "radii")
            radii_node.setAttribute("type", "_float32")
            radii_node.setAttribute("format", "ascii")
            point_data.appendChild(radii_node)

            string = str()
            for radius in radii:
                string = string + str(radius) + ' '
            radii_data = doc.createTextNode(string)
            radii_node.appendChild(radii_data)

        # Colors.
        if len(colors) > 0:
            color_node = doc.createElementNS("VTK", "Data_array")
            color_node.setAttribute("_name", "colors")
            color_node.setAttribute("NumberOf_components", "1")
            color_node.setAttribute("type", "_float32")
            color_node.setAttribute("format", "ascii")
            point_data.appendChild(color_node)

            string = str()
            for color in colors:
                string = string + str(color) + ' '
            color_data = doc.createTextNode(string)
            color_node.appendChild(color_data)

        # Tensors.
        if len(tensors) > 0:

            # Hack to make VTK understand I want to color the _tensor_glyphs.

            # I think there is a bug actually in VTK somewhere, when using 
            # tensor_glyph.xml to make a vtk_tensor_glyph object with both a 
            # Tensor array and a Scalar array. When you select a _tensor or a 
            # Scalar array from the dropdown menu and click 'apply', 
            # SetInputArrayToProcess is called with idx = 0 both times. _this 
            # is wrong.
            # 1. First element _tensor array gets overwritten.
            # 2. Scalar value is never written (which is accessed using 
            # GetInputArrayToProcess with an idx of 1.
            
            # The workaround here uses an additional _vector array (
          # vtk_tensor_glyph doesn't have a vector array), which when it gets 
            # updated actually results in _set_input_array_to_process to be called 
            # with idx = 1. So by also supplying _paraview with a vector for 
            # each color (just 3 times the color int), the _tensor array 
            # doesn't get overwritten and _get_input_array_to_process with idx is 
            # also happy and updates _scalars (!).

            # Tried to find the root cause using _gdb but failed.

            #Important files:
            #    ParaView3/VTK/Graphics/vtk_tensor_glyph.cxx
            #    ParaView3/VTK/Filtering/vtk_algorithm.cxx

            if len(colors) > 0:
                color_node = doc.createElementNS("VTK", "Data_array")
                color_node.setAttribute("_name", "colors_(really_a_scalar)") 
                color_node.setAttribute("NumberOf_components", "3")
                color_node.setAttribute("type", "_float32")
                color_node.setAttribute("format", "ascii")
                point_data.appendChild(color_node)

                string = str()
                for color in colors:
                    string += str(color) + ' ' + str(color) + ' ' + \
                              str(color) + ' '
                color_data = doc.createTextNode(string)
                color_node.appendChild(color_data)

            tensor_node = doc.createElementNS("VTK", "Data_array")
            tensor_node.setAttribute("_name", "tensors")
            tensor_node.setAttribute("NumberOf_components", "9")
            tensor_node.setAttribute("type", "_float32")
            tensor_node.setAttribute("format", "ascii")
            point_data.appendChild(tensor_node)

            string = str()
            for tensor in tensors:
                for value in tensor:
                    # A 'tensor' is represented as a list of 9 values.
                    string = string + str(value) + ' '
            tensor_data = doc.createTextNode(string)
            tensor_node.appendChild(tensor_data)


        # Cell data (_dummy).
        cell_data = doc.createElementNS("VTK", "Cell_data")
        piece.appendChild(cell_data)

        return doc


    def write_doc(self, doc, file_name):
        # Write to file and exit.
        out_file = open(file_name, 'w')
        # xml.dom.ext._pretty_print(doc, file)
        doc.writexml(out_file, newl='\n')
        out_file.close()


    def write_pvd(self, file, file_list):
        out_file = open(file, 'w')

        pvd = xml.dom.minidom.Document()
        pvd_root = pvd.createElementNS("VTK", "VTK_file")
        pvd_root.setAttribute("type", "_collection")
        pvd_root.setAttribute("version", "0.1")
        pvd_root.setAttribute("byte_order", "Little_endian")
        pvd.appendChild(pvd_root)

        collection = pvd.createElementNS("VTK", "_collection")
        pvd_root.appendChild(collection)

        for type, file_name, index, time in file_list:
            data_set = pvd.createElementNS("VTK", "Data_set")
            if time != None:
                # Problem with adding real time is that _timestep_values is not 
                # updated in _proxy group="misc" in .pvsm file after a reload.
                #time = str(time)
                time = str(index)
                data_set.setAttribute("timestep", time)
            data_set.setAttribute("group", "")
            data_set.setAttribute("part", type) # Use Extract_block.
            data_set.setAttribute("file", file_name)
            collection.appendChild(data_set)

        out_file = open(file, 'w')
        pvd.writexml(out_file, newl='\n')
        out_file.close()

