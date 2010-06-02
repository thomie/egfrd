from paraview import servermanager

READERS   = None
PARTICLES = None
SPHERES   = None
CYLINDERS = None
HELIX     = None
SURFACES  = None

# Settings
READERS   = True
PARTICLES = True
SPHERES   = True
CYLINDERS = True
HELIX     = True
SURFACES  = True


PARTICLE_RADIUS_SCALE_FACTOR = 4
HELIX_RADIUS_SCALE_FACTOR = 4
RESOLUTION = 18


if not servermanager.ActiveConnection:
    exit('pvpython not supported')


# Detect version.
try:
    from paraview import simple
    version = 6
except ImportError:
    version = 4


if len(servermanager.GetRenderViews()) > 0:
    rv = servermanager.GetRenderViews()[0]
else:
    rv = servermanager.CreateRenderView()


def clear():
    def name(proxy):
        return (type(proxy)).__name__

    def cmp_tubes_filters_glyphs(x,y):
        if name(x) == 'GenerateTubes':
            return -1
        elif name(y) == 'GenerateTubes':
            return 1
        if name(x) == 'ProgrammableFilter':
            return -1
        elif name(y) == 'ProgrammableFilter':
            return 1
        elif name(x) == 'Glyph' or name(x)[:11] == 'TensorGlyph':
            return -1
        elif name(y) == 'Glyph' or name(y)[:11] == 'TensorGlyph':
            return 1
        return cmp(x,y)

    pxm = servermanager.ProxyManager()
    for proxy in pxm.GetProxiesInGroup('lookup_tables').itervalues():
        servermanager.UnRegister(proxy)

    if version == 4:
        for proxy in sorted(pxm.GetProxiesInGroup('sources').itervalues(),
                            cmp_tubes_filters_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            servermanager.UnRegister(proxy)
        for proxy in pxm.GetProxiesInGroup('representations').itervalues():
            servermanager.UnRegister(proxy)

        rv.Representations = []
    else:
        for proxy in sorted(simple.GetSources().itervalues(), 
                            cmp_tubes_filters_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            if hasattr(proxy, "GlyphType"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.GlyphType = None
            simple.Delete(proxy)

    rv.ResetCamera()
    rv.StillRender()


def build():
    def add_pvd_reader(file, name):
        reader = servermanager.sources.PVDReader(FileName=file)
        servermanager.Register(reader, registrationName=name)
        if version == 4:
            reader.UpdatePipeline()
        else:
            pass

        return reader


    def add_extract_block(data, indices, name):
        block = servermanager.filters.ExtractBlock(Input=data, 
                                                   BlockIndices=indices)

        # This is needed to make SetScaleFactor and TensorGlyph work.
        block.UpdatePipeline();

        servermanager.Register(block, registrationName=name)
        return block


    def add_sphere_glyph(input, resolution=None, name=None):
        if version == 4:
            source = servermanager.sources.SphereSource()
            if resolution != None:
                source.ThetaResolution = resolution
                source.PhiResolution = resolution
            glyph = servermanager.filters.Glyph(Input=input, 
                                                Source=source)

            # Prevent "selected proxy value not in the list".
            # http://www.paraview.org/pipermail/paraview/2008-March/007416.html
            sourceProperty = glyph.GetProperty("Source")
            domain = sourceProperty.GetDomain("proxy_list");
            domain.AddProxy(source.SMProxy)

            glyph.SetScaleMode = 0
            glyph.SelectInputScalars = ['0', '0', '0', '0', 'radii']

        else:
            glyph = servermanager.filters.Glyph(Input=input, 
                                                GlyphType='Sphere')
            glyph.ScaleMode = 'scalar'

            if resolution != None:
                glyph.GlyphType.ThetaResolution = resolution
                glyph.GlyphType.PhiResolution = resolution

        glyph.SetScaleFactor = 1

        if name != None:
            servermanager.Register(glyph, registrationName=name)
        else:
            servermanager.Register(glyph)

        return glyph


    def add_tensor_glyph(input, type, resolution=None, name=None, scale=None):
        if version == 4:
            pass
        else:
            tensor_glyph = servermanager.filters.TensorGlyph(Input=input,
                                                             GlyphType=type)

            if resolution != None:
                tensor_glyph.GlyphType.Resolution = resolution

            if scale != None:
                tensor_glyph.GlyphType.Radius *= scale

        if name != None:
            servermanager.Register(tensor_glyph, registrationName=name)
        else:
            servermanager.Register(tensor_glyph)

        return tensor_glyph


    def add_tensor_glyph_with_custom_source(input, source, name=None):
        if version == 4:
            pass
        else:
            Type = servermanager.filters.TensorGlyphWithCustomSource
            tensor_glyph = Type(Input=input, GlyphType=source)

        if name != None:
            servermanager.Register(tensor_glyph, registrationName=name)
        else:
            servermanager.Register(tensor_glyph)

        return tensor_glyph


    def programmable_filter_color_hack(tensor_glyph, name):
        # http://www.paraview.org/pipermail/paraview/2009-March/011267.html
        # Dealing with composite datasets:
        # http://www.itk.org/Wiki/Python_Programmable_Filter
        filter = servermanager.filters.ProgrammableFilter()
        filter.Initialize()
        filter.Input = tensor_glyph
        filter.Script = """def flatten(input, output):
    output.ShallowCopy(input)
    output.GetPointData().GetScalars().SetName('colors')

input = self.GetInput()
output = self.GetOutput()

output.CopyStructure(input)
iter = input.NewIterator()
iter.UnRegister(None)
iter.InitTraversal()
while not iter.IsDoneWithTraversal():
    curInput = iter.GetCurrentDataObject()
    curOutput = curInput.NewInstance()
    curOutput.UnRegister(None)
    output.SetDataSet(iter, curOutput)
    flatten(curInput, curOutput)
    iter.GoToNextItem();"""

        filter.UpdatePipeline()

        servermanager.Register(filter, registrationName=name)

        return filter


    def set_color(proxy, rep):
        rep.ColorArrayName = 'colors'

        if version == 4:
            rep.ColorAttributeType = 0 # point data

            # Adapted from MakeBlueToRedLT in simple.py (ParaView 3.6).
            def MakeBlueToRedLT(min, max):
                lt = servermanager.rendering.PVLookupTable()
                servermanager.Register(lt)

                # Define RGB points. These are tuples of 4 values. First one is
                # the scalar values, the other 3 the RGB values. 
                rgbPoints = [min, 0, 0, 1, max, 1, 0, 0]
                lt.RGBPoints = rgbPoints
                lt.ColorSpace = "HSV"

                return lt

            pdi = proxy.GetDataInformation().GetPointDataInformation()
            range = pdi.GetArrayInformation('colors').GetComponentRange(0)
            lt = MakeBlueToRedLT(range[0], range[1])
        else:
            range = proxy.PointData.GetArray('colors').GetRange()
            lt = simple.MakeBlueToRedLT(range[0], range[1])

        rep.LookupTable = lt


    class _funcs_internals:
        # Taken from simple.py (ParaView 3.6).
        "Internal class."
        first_render = True
        view_counter = 0
        rep_counter = 0

    def show(proxy):
        if version == 4:
            # Adapted from Show in simple.py (ParaView 3.6).
            rep = servermanager.CreateRepresentation(proxy, rv)
            servermanager.ProxyManager().RegisterProxy("representations",
              "my_representation%d" % _funcs_internals.rep_counter, rep)
            _funcs_internals.rep_counter += 1
        else:
            rep = simple.Show(proxy)

        rep.Visibility = 1
        return rep


    if READERS:
        files = add_pvd_reader(simulation_data_directory + '/files.pvd', 
                               'files.pvd')

        static = add_pvd_reader(simulation_data_directory + '/static.pvd', 
                                'static.pvd')


    if PARTICLES:
        particle_data = add_extract_block(files, [2], 'b1')

        global particles
        particles = add_sphere_glyph(particle_data, name='Particles')
        particles.SetScaleFactor = PARTICLE_RADIUS_SCALE_FACTOR

        rep = show(particles)

        set_color(particles, rep)


    if SPHERES:
        sphere_data = add_extract_block(files, [4], 'b2')

        global spheres
        spheres = add_sphere_glyph(sphere_data, RESOLUTION, name='Spheres')

        rep = show(spheres)

        set_color(spheres, rep)
        rep.Representation = 'Wireframe'
        rep.Opacity = 0.5


    if CYLINDERS:
        cylinder_data = add_extract_block(files, [6], 'b3')

        global cylinders
        cylinders = add_tensor_glyph(cylinder_data, 'Cylinder', 
                                     resolution=RESOLUTION, name='tg')

        rep = show(cylinders)

        rep.Visibility = 0
        programmable_filter = programmable_filter_color_hack(cylinders,
                                                             name='Cylinders')
        rep = show(programmable_filter)

        set_color(programmable_filter, rep)
        rep.Representation = 'Wireframe'
        rep.Opacity = 1.0


    if SURFACES:
        # Cylindrical surfaces.
        cylindrical_surface_data = add_extract_block(static, [2], 'b1')

        if not HELIX:
            global cylindrical_surfaces
            cylindrical_surfaces = \
                add_tensor_glyph(cylindrical_surface_data, 'Cylinder', 
                                 name='Cylindrical Surfaces',
                                 scale=HELIX_RADIUS_SCALE_FACTOR) 
            rep = show(cylindrical_surfaces)
            rep.Representation = 'Wireframe'
            rep.Opacity = 0.5
        else:
            helix_file = open(paraview_scripts_directory + '/helix.py', 'r')
            if version == 4:
                #source = ProgrammableFilter()
                #source.Script = helix_file.read()
                #servermanager.Register(source) # Needed, or register.
                pass
            else:
                helix_source = servermanager.sources.ProgrammableSource()
                helix_source.Script = 'HELIX_RADIUS_SCALE_FACTOR = ' + \
                                      str(HELIX_RADIUS_SCALE_FACTOR) + \
                                      '\n' + helix_file.read()
                servermanager.Register(helix_source, registrationName='ps')

            helix_file.close()


            tensor_glyph = \
                add_tensor_glyph_with_custom_source(cylindrical_surface_data, 
                                                    helix_source, 
                                                    name='tgwcs')

            global double_helix
            double_helix = \
                servermanager.filters.GenerateTubes(Input=tensor_glyph)
            servermanager.Register(double_helix,
                                   registrationName='Double Helix')

            # Compute helix radius.
            di = cylindrical_surface_data.GetDataInformation()
            pdi = di.GetPointDataInformation()
            tensor = pdi.GetArrayInformation('tensors')

            cylindrical_surface_radius = 1e100
            for i in range(9):
                # Find minimum value of tensor larger than 0.
                value = tensor.GetComponentRange(i)[0]
                if value > 0 and value < cylindrical_surface_radius:
                    cylindrical_surface_radius = value

            helix_radius = HELIX_RADIUS_SCALE_FACTOR * \
                           cylindrical_surface_radius

            # Make double_helix a bit thinner than helix.
            double_helix.Radius = helix_radius / 20

            rep = show(double_helix)
            rep.ColorArrayName = 'TubeNormals'


        # Planar surfaces.
        planar_surface_data = add_extract_block(static, [4], 'b2')
        global planar_surfaces
        planar_surfaces = add_tensor_glyph(planar_surface_data, 'Box', 
                                           name='Planar Surfaces')

        rep = show(planar_surfaces)
        rep.Representation = 'Surface'
        rep.Opacity = 0.5


        # Cuboidal surfaces.
        cuboidal_region_data = add_extract_block(static, [6], 'b3')
        global cuboidal_regions
        cuboidal_regions = add_tensor_glyph(cuboidal_region_data, 'Box',
                                           name='Cuboidal Regions')

        rep = show(cuboidal_regions)
        rep.Representation = 'Wireframe'
        rep.Opacity = 1.0


    # Set camera.
    global cam
    cam = GetActiveCamera()
    rv.ResetCamera() # Sets focalpoint to center of box.
    cam.SetViewUp(0,0,1)
    focal = cam.GetFocalPoint()
    cam.SetPosition(focal[0]*10, focal[1], focal[2]) # Straigh in front of box.

    rv.Background = [0,0,0] # Black.
    rv.ResetCamera() # Changes cam.GetPosition() only by zooming in/out.
    rv.StillRender()


print 'clear()'
clear()
print 'build()'
build()


