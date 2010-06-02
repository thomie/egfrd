
import os
import shutil
#import re
#import logging
import numpy
from vtk_xml_serial_unstructured import *
#from bd import BD_simulator
from _gfrd import Sphere, Cylinder, Box, Plane
from multi import Multi
from utils import crossproduct


class VTKLogger:
    """Logger that can be used to visualize data with Kitware ParaView.


    * Setup. Specify buffer_size to only write last 'buffer_size' simulation 
      steps to file:
        vtklogger = VTKLogger(sim=s, name='run')
        or
        vtklogger = VTKLogger(sim=s, name='run', buffer_size=100)

    * Each step, to write .vtk files:
        vtklogger.log()

    * Finalize, to write .pvd file:
        vtklogger.stop()


    Inner workings:
        log():
            (get.......data = create_doc() + add_piece()) + write_doc()
        stop():
            write_pvd(name.pvd)


    === Cylinders
    To visualize the cylinders a workaround using tensors is used, as 
    explained here: 
        http://www.paraview.org/pipermail/paraview/2009-March/011256.html.
    The mentioned tensorGlyph.xml should be supplied with this package.

    As explainded in the above link, to give cylinders the right color, there 
    are 2 options.

    1. Build ParaView from source, after adding in file
    Paraview3/VTK/Graphics/vtkTensorGlyph.cxx after
        newScalars = vtkFloatArray::New();
    a new line:
        newScalars->SetName("colors");
    2. Do that Python script thing.

    Another hack was needed to get the coloring to work. This makes VTKLogger 
    write a vector instead of a scalar value for each color to the .vtu files. 
    But you shouldn't have to worry about that, just select 'colors' to color 
    the Glyph.

    When doing Brownian Dynamics, don't show shells.

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

        self.i = 0           # Step counter.
        self.delta_t = 1e-11 # Needed for hack. Note: don't make too small, 
                             # should be relative to max time.
        self.last_time = 0   # Needed for hack.

    def log(self):
        time = self.sim.t
        if (abs(time - self.last_time) < 1e-9) and not self.no_shells:
            # Hack to make ParaView understand this is a different simulator 
            # step but with the same time.
            # 1. During multi global time is not updated.
            # 2. During initialization time is 0.
            # 3. Sometimes shells have mobility_radius = 0 --> dt = 0.
            # And I want every step recorded, so I can find out what happened 
            # in which step (divide by 2 actually).
            #
            # Now ParaView should perceive a state change.
            # When doing Brownian Dynamics, this is not needed.
            time = self.last_time + self.delta_t

        # Get data.
        particle_data = self.get_particle_data()
        sphere_data, cylinder_data = self.get_shell_data_from_scheduler()

        # Write to buffer or file.
        if self.buffer_size:
            # Store in buffer, instead of writing to file directly.
            self.buffer.append((time, self.i, particle_data, sphere_data, 
                                cylinder_data))

            if self.i >= self.buffer_size:
                # FIFO.
                del self.buffer[0]
        else:
            # Write normal log.
            self.writelog(time, self.i,
                          (particle_data, sphere_data, cylinder_data))

        self.i += 1
        self.last_time = time

    def writelog(self, time, index,
                 (particle_data, sphere_data, cylinder_data)):
        if index == 0:
            self.previous_sphere_data = sphere_data
            self.previous_cylinder_data = cylinder_data

        if not self.no_shells and self.extra_particle_step:
            # Show step where only particle_data have been updated.
            index *= 2;
            self.make_snapshot('particle_data', particle_data, index, time)
            self.make_snapshot('sphere_data', self.previous_sphere_data, 
                               index, time)
            self.make_snapshot('cylinder_data', self.previous_cylinder_data, 
                               index, time)

            time += self.delta_t
            index += 1

        self.make_snapshot('particle_data', particle_data, index, time)
        self.make_snapshot('sphere_data', sphere_data, index, time)
        self.make_snapshot('cylinder_data', cylinder_data, index, time)

        self.previous_sphere_data = sphere_data
        self.previous_cylinder_data = cylinder_data

    def make_snapshot(self, type, data, index='', time=None):
        """Write data to file.

        """
        doc = self.vtk_writer.create_doc(data)
        file_name = 'files/' + type + str(index) + '.vtu'
        self.vtk_writer.write_doc(doc, self.name + '/' + file_name)

        # Store filename and time in file_list, used by 
        # vtk_writer.write_pvd().
        if time == None:
            self.static_list.append((type, file_name, None, None))
        else:
            self.file_list.append((type, file_name, index, time))

    def stop(self):
        self.log()

        # Write contents of buffer.
        for index, entry in enumerate(self.buffer):
            if index == 0:
                # Add dummy data with color range.
                # Todo. Clean this up. Write color range as field data maybe.
                dummy_particles, dummy_colors = \
                    self.get_dummy_particles_and_color_range()
                dummy_particle_data = \
                    self.process_spheres(dummy_particles, dummy_colors)
                particle_data = entry[2]
                particle_data[0].extend(dummy_particle_data[0])
                particle_data[1].extend(dummy_particle_data[1])
                particle_data[2].extend(dummy_particle_data[2])
                particle_data[3].extend(dummy_particle_data[3])

                dummy_spheres, dummy_colors = \
                    self.get_dummy_spheres_and_color_range()
                dummy_sphere_data = \
                    self.process_spheres(dummy_spheres, dummy_colors)
                sphere_data = entry[3]
                sphere_data[0].extend(dummy_sphere_data[0])
                sphere_data[1].extend(dummy_sphere_data[1])
                sphere_data[2].extend(dummy_sphere_data[2])
                sphere_data[3].extend(dummy_sphere_data[3])

                dummy_cylinders, dummy_colors = \
                    self.get_dummy_cylinders_and_color_range()
                dummy_cylinder_data = \
                    self.process_cylinders(dummy_cylinders, dummy_colors)
                cylinder_data = entry[4]
                cylinder_data[0].extend(dummy_cylinder_data[0])
                cylinder_data[1].extend(dummy_cylinder_data[1])
                cylinder_data[2].extend(dummy_cylinder_data[2])
                cylinder_data[3].extend(dummy_cylinder_data[3])
            if index % 10 == 0:
                print 'vtklogger writing step %s from buffer' % index
            self.writelog(entry[0], index, entry[2:])

        # Surfaces.
        self.make_snapshot('cylindrical_surfaces', 
                           self.get_cylindrical_surface_data())
        self.make_snapshot('planar_surfaces',
                           self.get_planar_surface_data())
        self.make_snapshot('cuboidal_regions', 
                           self.get_cuboidal_region_data())

        # Finally, write PVD files.
        self.vtk_writer.write_pvd(self.name + '/' + 'files.pvd', 
                                  self.file_list)

        self.vtk_writer.write_pvd(self.name + '/' + 'static.pvd', 
                                  self.static_list)

    def get_dummy_particles_and_color_range(self):
        # Todo. Clean this up. Write color range as field data maybe.
        # Add dummy particle with color 1 (species.id.serial starts at 1).
        particles = [self.get_dummy_sphere()]
        colors = [1]
        # Add dummy particle with color is highest species index.
        particles.append(self.get_dummy_sphere())
        try:
            max_color = max(self.color_dict.values())
        except:
            for species in self.sim.world.species:
                # Find species with highest id.
                pass
            max_color = species.id.serial
        colors.append(max_color)
        return particles, colors

    def get_dummy_spheres_and_color_range(self):
        # Todo. Clean this up. Write color range as field data maybe.
        # Add dummy sphere with color is 0.
        spheres = [self.get_dummy_sphere()]
        colors = [0]
        # Add dummy sphere with color is 3.
        spheres.append(self.get_dummy_sphere())
        colors.append(3)
        return spheres, colors

    def get_dummy_cylinders_and_color_range(self):
        # Todo. Clean this up. Write color range as field data maybe.
        # Add dummy cylinder with color is 0.
        cylinders = [self.get_dummy_cylinder()]
        colors = [0]
        # Add dummy cylinder with color is 3.
        cylinders.append(self.get_dummy_cylinder())
        colors.append(3)
        return cylinders, colors

    def get_particle_data(self):
        particles, colors = [], []

        for species in self.sim.world.species:
            for particle_id in self.sim.world.get_particle_ids(species):
                particle = self.sim.world.get_particle(particle_id)[1]
                particles.append(particle)
                try:
                    color = self.color_dict[species.id.serial]
                except:
                    color = species.id.serial
                colors.append(color)

        if self.i == 0:
            dummy_particles, dummy_colors = \
                self.get_dummy_particles_and_color_range()
            particles.extend(dummy_particles)
            colors.extend(dummy_colors)

        return self.process_spheres(particles, colors)

    def get_shell_data_from_scheduler(self):
        spheres, sphere_colors = [], []
        cylinders, cylinder_colors = [], []

        if self.no_shells == True:
            number_of_shells = 0
        else:
            number_of_shells = self.sim.scheduler.getSize()

        if number_of_shells > 0:
            top_event = self.sim.scheduler.getTopEvent()

        if self.i == 0:
            dummy_spheres, dummy_colors = \
                self.get_dummy_spheres_and_color_range()
            spheres.extend(dummy_spheres)
            sphere_colors.extend(dummy_colors)

            dummy_cylinders, dummy_colors = \
                self.get_dummy_cylinders_and_color_range()
            cylinders.extend(dummy_cylinders)
            cylinder_colors.extend(dummy_colors)

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
                cylinder_colors.append(color)
            except:
                # Spheres: single, pair or multi.
                for _, shell in object.shell_list:
                    spheres.append(shell)
                    sphere_colors.append(color)

        return self.process_spheres(spheres, sphere_colors), \
               self.process_cylinders(cylinders, cylinder_colors)

    def get_cuboidal_region_data(self):
        boxes = [self.sim.world.get_structure("world").shape]

        return self.process_boxes(boxes)

    def get_planar_surface_data(self):
        world = self.sim.world.get_structure("world")
        boxes = [surface.shape for surface
                               in self.sim.world.structures
                               if isinstance(surface.shape, Plane)
                               and not surface == world]
    
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
            # Add dummy sphere to stop ParaView from complaining.
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
            # Add dummy cylinder to stop TensorGlyph from complaining.
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

            # Construct tensor. Use TensorGlyph plugin from:
            # http://www.paraview.org/pipermail/paraview/2009-March/011256.html
            # Unset Extract eigenvalues.

            # Select basis vector in which orientation is smallest.
            _, basis_vector = min(zip(abs(orientation), [[1, 0, 0], 
                                                         [0, 1, 0],
                                                         [0, 0, 1]]))
            # Find 2 vectors perpendicular to orientation.
            perpendicular1 = numpy.cross(orientation, basis_vector)
            perpendicular2 = numpy.cross(orientation, perpendicular1)
            # A 'tensor' is represented as an array of 9 values.
            # Stupid ParaView wants  a normal vector to the cylinder to orient 
            # it. So orientation and perpendicular1 swapped.
            tensor = numpy.concatenate((perpendicular1 * radius, 
                                        orientation * size,
                                        perpendicular2 * radius))

            self.append_lists(pos_list, position, tensor_list=tensor_list, 
                              tensor=tensor)

        return (pos_list, [], color_list, tensor_list)

    def process_boxes(self, boxes=[], color_list=[]):
        pos_list, tensor_list = [], []

        if len(boxes) == 0:
            # Add dummy box to stop TensorGlyph from complaining.
            boxes = [self.get_dummy_box()]
            color_list = [0]

        for box in boxes:
            try:
                dz = box.unit_z * box.extent[2]
            except AttributeError:
                # Planes don't have z dimension.
                unit_z = crossproduct(box.unit_x, box.unit_y)
                dz = unit_z * 1e-20
            tensor = numpy.concatenate((box.unit_x * box.extent[0],
                                        box.unit_y * box.extent[1],
                                        dz))
            self.append_lists(pos_list, box.position, tensor_list=tensor_list, 
                              tensor=tensor)

        return (pos_list, [], color_list, tensor_list)

    def append_lists(self, pos_list, pos, radius_list=[], radius=None, 
                     tensor_list=[], tensor=None):
        """Helper.

        """
        factor = 1
        pos_list.append(pos * factor)

        # Multiply radii and tensors by 2 because ParaView sets radius to 0.5 
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

