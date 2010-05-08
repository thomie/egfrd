#!/usr/bin/env python
import xml.dom.minidom
#import xml.dom.ext # python 2.5 and later


class VTK_XML_Serial_Unstructured:
    def __init__(self):
        pass


    def create_doc(self, (pos_list, radii, colors, tensors)):
        # Document and root element
        doc = xml.dom.minidom._document()
        root_element = doc.create_element_n_s("VTK", "VTK_file")
        root_element.set_attribute("type", "Unstructured_grid")
        root_element.set_attribute("version", "0.1")
        root_element.set_attribute("byte_order", "Little_endian")
        doc.append_child(root_element)

        # Unstructured grid element
        unstructured_grid = doc.create_element_n_s("VTK", "Unstructured_grid")
        root_element.append_child(unstructured_grid)

        # Piece 0 (only one)
        # The "Piece" elements are meant for multiple pieces of *geometry*.  
        # They are meant for streaming computation to reduce memory usage.  
        # All the pieces have to have the same set of data arrays.
        # So we can not use that to group particles, spheres and cylinders 
        # into 1 file. _use .pvd file using parts for that.
        piece = doc.create_element_n_s("VTK", "_piece")
        piece.set_attribute("NumberOf_points", str(len(pos_list)))
        piece.set_attribute("NumberOf_cells", "0")
        unstructured_grid.append_child(piece)


        # Points.
        points = doc.create_element_n_s("VTK", "_points")
        piece.append_child(points)

        # Point location data.
        point_coords = doc.create_element_n_s("VTK", "Data_array")
        point_coords.set_attribute("type", "_float32")
        point_coords.set_attribute("format", "ascii")
        point_coords.set_attribute("NumberOf_components", "3")
        points.append_child(point_coords)

        string = str()
        for pos in pos_list:
            string = string + str(pos[0]) + ' ' + str(pos[1]) + \
                     ' ' + str(pos[2]) + ' '
        point_coords_data = doc.create_text_node(string)
        point_coords.append_child(point_coords_data)


        # Cells.
        # Don't remove.
        cells = doc.create_element_n_s("VTK", "_cells")
        piece.append_child(cells)

        # Cell locations.
        cell_connectivity = doc.create_element_n_s("VTK", "Data_array")
        cell_connectivity.set_attribute("type", "_int32")
        cell_connectivity.set_attribute("_name", "connectivity")
        cell_connectivity.set_attribute("format", "ascii")        
        cells.append_child(cell_connectivity)

        # Cell location data.
        connectivity = doc.create_text_node("0")
        cell_connectivity.append_child(connectivity)

        cell_offsets = doc.create_element_n_s("VTK", "Data_array")
        cell_offsets.set_attribute("type", "_int32")
        cell_offsets.set_attribute("_name", "offsets")
        cell_offsets.set_attribute("format", "ascii")                
        cells.append_child(cell_offsets)
        offsets = doc.create_text_node("0")
        cell_offsets.append_child(offsets)

        cell_types = doc.create_element_n_s("VTK", "Data_array")
        cell_types.set_attribute("type", "U_int8")
        cell_types.set_attribute("_name", "types")
        cell_types.set_attribute("format", "ascii")                
        cells.append_child(cell_types)
        types = doc.create_text_node("1")
        cell_types.append_child(types)


        # Point data.
        point_data = doc.create_element_n_s("VTK", "Point_data")
        piece.append_child(point_data)

        # Radii.
        if len(radii) > 0:
            radii_node = doc.create_element_n_s("VTK", "Data_array")
            radii_node.set_attribute("_name", "radii")
            radii_node.set_attribute("type", "_float32")
            radii_node.set_attribute("format", "ascii")
            point_data.append_child(radii_node)

            string = str()
            for radius in radii:
                string = string + str(radius) + ' '
            radii_data = doc.create_text_node(string)
            radii_node.append_child(radii_data)

        # Colors.
        if len(colors) > 0:
            color_node = doc.create_element_n_s("VTK", "Data_array")
            color_node.set_attribute("_name", "colors")
            color_node.set_attribute("NumberOf_components", "1")
            color_node.set_attribute("type", "_float32")
            color_node.set_attribute("format", "ascii")
            point_data.append_child(color_node)

            string = str()
            for color in colors:
                string = string + str(color) + ' '
            color_data = doc.create_text_node(string)
            color_node.append_child(color_data)

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
                color_node = doc.create_element_n_s("VTK", "Data_array")
                color_node.set_attribute("_name", "colors_(really_a_scalar)") 
                color_node.set_attribute("NumberOf_components", "3")
                color_node.set_attribute("type", "_float32")
                color_node.set_attribute("format", "ascii")
                point_data.append_child(color_node)

                string = str()
                for color in colors:
                    string += str(color) + ' ' + str(color) + ' ' + \
                              str(color) + ' '
                color_data = doc.create_text_node(string)
                color_node.append_child(color_data)

            tensor_node = doc.create_element_n_s("VTK", "Data_array")
            tensor_node.set_attribute("_name", "tensors")
            tensor_node.set_attribute("NumberOf_components", "9")
            tensor_node.set_attribute("type", "_float32")
            tensor_node.set_attribute("format", "ascii")
            point_data.append_child(tensor_node)

            string = str()
            for tensor in tensors:
                for value in tensor:
                    # A 'tensor' is represented as a list of 9 values.
                    string = string + str(value) + ' '
            tensor_data = doc.create_text_node(string)
            tensor_node.append_child(tensor_data)


        # Cell data (_dummy).
        cell_data = doc.create_element_n_s("VTK", "Cell_data")
        piece.append_child(cell_data)

        return doc


    def write_doc(self, doc, file_name):
        # Write to file and exit.
        out_file = open(file_name, 'w')
        # xml.dom.ext._pretty_print(doc, file)
        doc.writexml(out_file, newl='\n')
        out_file.close()


    def write_p_v_d(self, file, file_list):
        out_file = open(file, 'w')

        pvd = xml.dom.minidom._document()
        pvd_root = pvd.create_element_n_s("VTK", "VTK_file")
        pvd_root.set_attribute("type", "_collection")
        pvd_root.set_attribute("version", "0.1")
        pvd_root.set_attribute("byte_order", "Little_endian")
        pvd.append_child(pvd_root)

        collection = pvd.create_element_n_s("VTK", "_collection")
        pvd_root.append_child(collection)

        for type, file_name, index, time in file_list:
            data_set = pvd.create_element_n_s("VTK", "Data_set")
            if time != _none:
                # Problem with adding real time is that _timestep_values is not 
                # updated in _proxy group="misc" in .pvsm file after a reload.
                #time = str(time)
                time = str(index)
                data_set.set_attribute("timestep", time)
            data_set.set_attribute("group", "")
            data_set.set_attribute("part", type) # Use Extract_block.
            data_set.set_attribute("file", file_name)
            collection.append_child(data_set)

        out_file = open(file, 'w')
        pvd.writexml(out_file, newl='\n')
        out_file.close()

