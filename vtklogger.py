
import os
import shutil
#import re
#import logging
import numpy
from vtk_xml_serial_unstructured import *
#from bd import BD_simulator
from _gfrd import Sphere, Cylinder, Box
from multi import Multi


# Temporary.
'''
class _sphere_temp(_shape):
    def __init__(self, position, radius):
        Shape.__init__(self) 
        self.position = numpy.array(position)
        self.radius = radius

    def signed_distance_to(self, pos):
        """Note: cyclic_transpose 'pos' before you use this.
         
        """
        return length(pos - self.position) - self.radius
'''


class VTKLogger:
    """Logger that can be used to visualize data with _kitware _para_view.


    * Setup. Specify buffer_size to only write last 'buffer_size' simulation 
      steps to file:
        vtklogger = VTK_logger(sim=s, name='run')
        or
        vtklogger = VTK_logger(sim=s, name='run', buffer_size=100)

    * Each step, to write .vtk files:
        vtklogger.log()

    * Finalize, to write .pvd file:
        vtklogger.stop()


    Inner workings:
        log():
            (get......._data = create_doc() + add_piece()) + write_doc()
        stop():
            write_pvd(name.pvd)


    === Cylinders
    To visualize the cylinders a workaround using tensors is used, as 
    explained here: 
        http://www.paraview.org/pipermail/paraview/2009-_march/011256.html.
    The mentioned tensor_glyph.xml should be supplied with this package.

    As explainded in the above link, to give cylinders the right color, there 
    are 2 options.

    1. Build Paraview from source, after adding in file
    Paraview3/VTK/Graphics/vtk_tensor_glyph.cxx after
        new_scalars = vtk_float_array::_new();
    a new line:
        new_scalars->Set_name("colors");
    2. Do that _python script thing.

    Another hack was needed to get the coloring to work. This makes VTK_logger 
    write a vector instead of a scalar value for each color to the .vtu files. 
    But you shouldn't have to worry about that, just select 'colors' to color 
    the _glyph.

    When doing _brownian _dynamics, don't show shells.

    extra_particle_step=True means that for each timestep an extra step is  
    recorded where only the active particle has been updated (it's shell
  stays unchanged).

    """
    def __init__(self, sim, name='vtkdata', buffer_size=None, no_shells=False, 
                extra_particle_step=True, color_dict=None):
        self.sim = sim
        self.no_shells = no_shells
        self.extra_particle_step = extra_particle_step
        self.color_dict = color_dict

        self.vtk_writer = VTK_XML_Serial_Unstructured()
        self.buffer_size = buffer_size
        self.buffer = []

        # Filename stuff.
        assert len(name) > 0
        self.name = name

        files_directory = self.name + '/files'
        if os.path.exists(files_directory):
            shutil.rmtree(files_directory)
        os.makedirs(files_directory) 

        self.file_list = []
        self.static_list = []

        self.i = 0          # _step counter.
        self.delta_t = 1e-11 # Needed for hack. _note: don't make too small, 
                            # should be relative to max time.
        self.last_time = 0   # _needed for hack.

    def log(self):
        time = self.sim.t
        if (abs(time - self.last_time) < 1e-9) and not self.no_shells:
            # Hack to make _paraview understand this is a different simulator 
            # step but with the same time.
            # 1. During multi global time is not updated.
            # 2. During initialization time is 0.
            # 3. Sometimes shells have mobility_radius = 0 --> dt = 0.
            # And I want every step recorded, so I can find out what happened 
            # in which step (divide by 2 actually).
            #
            # Now Paraview should perceive a state change.
            # When doing _brownian _dynamics, this is not needed.
            time = self.last_time + self.delta_t

        # Get data.
        particles = self.get_particle_data()
        spheres, cylinders = self.get_shell_data_from_scheduler()

        # Write to buffer or file.
        if self.buffer_size:
            # Store in buffer, instead of writing to file directly.
            self.buffer.append((time, self.i, particles, spheres, 
                                cylinders))

            if self.i >= self.buffer_size:
                # FIFO.
                del self.buffer[0]
        else:
            # Write normal log.
            self.writelog(time, self.i, (particles, spheres, cylinders))

        self.i += 1
        self.last_time = time

    def writelog(self, time, index, (particles, spheres, cylinders)):
        if index == 0:
            self.previous_spheres = spheres
            self.previous_cylinders = cylinders

        if not self.no_shells and self.extra_particle_step:
            # Show step where only particles have been updated.
            index *= 2;
            self.make_snapshot('particles', particles, index, time)
            self.make_snapshot('spheres', self.previous_spheres, index, time)
            self.make_snapshot('cylinders', self.previous_cylinders, index, time)

            time += self.delta_t
            index += 1

        self.make_snapshot('particles', particles, index, time)
        self.make_snapshot('spheres', spheres, index, time)
        self.make_snapshot('cylinders', cylinders, index, time)

        self.previous_spheres = spheres
        self.previous_cylinders = cylinders

    def make_snapshot(self, type, data, index='', time=None):
        """Write data to file.

        """
        doc = self.vtk_writer.create_doc(data)
        file_name = 'files/' + type + str(index) + '.vtu'
        self.vtk_writer.write_doc(doc, self.name + '/' + file_name)

        # Store filename and time in file_list, used by vtk_wrtie.write_pvd().
        if time == None:
            self.static_list.append((type, file_name, None, None))
        else:
            self.file_list.append((type, file_name, index, time))

    def stop(self):
        self.log()

        # Write contents of buffer.
        for index, entry in enumerate(self.buffer):
            if index % 10 == 0:
                print 'vtklogger writing step %s from buffer' % index
            self.writelog(entry[0], index, entry[2:])

        # Surfaces.
        self.make_snapshot('cylindrical_surfaces', 
                         self.get_cylindrical_surface_data())
        self.make_snapshot('planar_surfaces', self.get_planar_surface_data())
        self.make_snapshot('cuboidal_surfaces', self.get_cuboidal_surface_data())

        # Finally, write PVD files.
        self.vtk_writer.write_pvd(self.name + '/' + 'files.pvd', 
                                self.file_list)

        self.vtk_writer.write_pvd(self.name + '/' + 'static.pvd', 
                                self.static_list)

    def get_particle_data(self):
        particles, particle_color_list = [], []

        for species in self.sim.world.species:
            for particle_id in self.sim.world.get_particle_ids(species):
                particle = self.sim.world.get_particle(particle_id)[1]
                particles.append(particle)
                try:
                    color = self.color_dict[species.id.serial]
                except:
                    color = species.id.serial
                particle_color_list.append(color)

        species_id_serial_max = species.id.serial

        if self.i == 0:
            # Add dummy particle with color 1 (species.id.serial starts at 1).
            particles.append(self.get_dummy_sphere())
            particle_color_list.append(1)
            # Add dummy particle with color is highest species index.
            particles.append(self.get_dummy_sphere())
            try:
                max_color = max(self.color_dict.values())
            except:
                max_color = species_id_serial_max
            particle_color_list.append(max_color)

        return self.process_spheres(particles, particle_color_list)

    def get_shell_data_from_scheduler(self):
        shells, shell_color_list = [], []
        cylinders, cylinder_color_list = [], []

        if self.no_shells == True:
            number_of_shells = 0
        else:
            number_of_shells = self.sim.scheduler.getSize()

        if number_of_shells > 0:
            top_event = self.sim.scheduler.getTopEvent()

        if self.i == 0:
            # Add dummy sphere with color is 0.
            shells.append(self.get_dummy_sphere())
            shell_color_list.append(0)
            # Add dummy sphere with color is 3.
            shells.append(self.get_dummy_sphere())
            shell_color_list.append(3)
            # Add dummy cylinder with color is 0.
            cylinders.append(self.get_dummy_cylinder())
            cylinder_color_list.append(0)
            # Add dummy cylinder with color is 3.
            cylinders.append(self.get_dummy_cylinder())
            cylinder_color_list.append(3)

        for event_index in range(number_of_shells):
            # Get event
            event = self.sim.scheduler.getEventByIndex(event_index)
            object = event.getArg()

            # Single and pairs.
            color = object.multiplicity

            # Highlight top_event for singles and pairs.
            if event.getArg() == top_event.getArg():
                color = 0

            # Multi.
            if isinstance(type(object), Multi):
                color = 3

            try:
                shell = object.shell_list[0][1]
                # Only cylinders have size.
                shell.shape.size
                cylinders.append(shell)
                cylinder_color_list.append(color)
            except:
                # Spheres: single, pair or multi.
                for _, shell in object.shell_list:
                    shells.append(shell)
                    shell_color_list.append(color)

        return self.process_spheres(shells, shell_color_list), \
               self.process_cylinders(cylinders, cylinder_color_list)

    def get_cuboidal_surface_data(self):
        try:
            boxes = [self.sim.model.default_surface.shape]
        except:
            boxes = []

        return self.process_boxes(boxes)

    def get_planar_surface_data(self):
        boxes = [surface.shape for surface
                               in self.sim.world.structures
                               if isinstance(surface.shape, Box)]
    
        return self.process_boxes(boxes)

    def get_cylindrical_surface_data(self):
        # Todo. Make DNA blink when reaction takes place.
        cylinders = [surface for surface
                             in self.sim.world.structures
                             if isinstance(surface.shape, Cylinder)]
        return self.process_cylinders(cylinders)

    def process_spheres(self, spheres=[], color_list=[]):
        pos_list, radius_list = [], []
        if len(spheres) == 0:
            # Add dummy sphere to stop _paraview from complaining.
            spheres = [self.get_dummy_sphere()]
            color_list = [0]

        for sphere in spheres:
            # Todo.
            try:
                position = sphere.position
                radius = sphere.radius
            except:
                position = sphere.shape.position
                radius = sphere.shape.radius
            self.append_lists(pos_list, position, radius_list, radius)

        return (pos_list, radius_list, color_list, [])

    def process_cylinders(self, cylinders=[], color_list=[]):
        pos_list, tensor_list = [], []

        if len(cylinders) == 0:
            # Add dummy cylinder to stop tensor_glyph from complaining.
            cylinders = [self.get_dummy_cylinder()]
            color_list = [0]

        for cylinder in cylinders:
            # Todo.
            try:
                position = cylinder.position
                radius = cylinder.radius
                orientation = cylinder.unit_z
                size = cylinder.size
            except:
                position = cylinder.shape.position
                radius = cylinder.shape.radius
                orientation = cylinder.shape.unit_z
                size = cylinder.shape.size

            # Construct tensor. _use tensor glyph plugin from:
            # http://www.paraview.org/pipermail/paraview/2009-_march/011256.html
            # Unset Extract eigenvalues.

            # Select basis vector in which orientation is smallest.
            _, basis_vector = min(zip(abs(orientation), [[1, 0, 0], 
                                                      [0, 1, 0], 
                                                      [0, 0, 1]]))
            # Find 2 vectors perpendicular to orientation.
            perpendicular1 = numpy.cross(orientation, basis_vector)
            perpendicular2 = numpy.cross(orientation, perpendicular1)
            # A 'tensor' is represented as an array of 9 values.
            # Stupid Paraview wants  a normal vector to the cylinder to orient  
            # it. _so orientation and perpendicular1 swapped.
            tensor = numpy.concatenate((perpendicular1 * radius, 
              orientation * size, perpendicular2 * radius))

            self.append_lists(pos_list, position, tensor_list=tensor_list, 
                            tensor=tensor) 

        return (pos_list, [], color_list, tensor_list)

    def process_boxes(self, boxes=[], color_list=[]):
        pos_list, tensor_list = [], []

        if len(boxes) == 0:
            # Add dummy box to stop tensor_glyph from complaining.
            boxes = [self.get_dummy_box()]
            color_list = [0]

        for box in boxes:
            tensor = numpy.concatenate((box.unit_x * box.extent[0],
                                      box.unit_y * box.extent[1],
                                      box.unit_z * box.extent[2]))
            self.append_lists(pos_list, box.position, tensor_list=tensor_list, 
                          tensor=tensor) 

        return (pos_list, [], color_list, tensor_list)

    def append_lists(self, pos_list, pos, radius_list=[], radius=None, 
                  tensor_list=[], tensor=None):
        """Helper.

        """
        factor = 1
        pos_list.append(pos * factor)

        # Multiply radii and tensors by 2 because _paraview sets radius to 0.5 
        # by default, and it wants full lengths for cylinders and we are 
        # storing half lengths.
        if radius:
            radius_list.append(radius * 2 * factor)

        if tensor != None:
            tensor = tensor * 2 * factor
            tensor_list.append(tensor)
    

    def get_dummy_sphere(self):
        return Sphere([0, 0, 0], 1e-20)

    def get_dummy_cylinder(self):
        return Cylinder([0, 0, 0], 1e-20, [0, 0, 1], 1e-20)

    def get_dummy_box(self):
        return Box([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
                   1e-20, 1e-20, 1e-20)

