READERS   = False
PARTICLES = False
SPHERES    = False
CYLINDERS = False
HELIX     = False
SURFACES  = False

# Settings
READERS   = True
PARTICLES = True
SPHERES    = True
#CYLINDERS = True
#HELIX     = True
#SURFACES  = True


PARTICLE_SCALE_FACTOR = 4
RESOLUTION = 18


try:
    import paraview
    paraview.compatibility
    paraview.compatibility.minor = 5
    if servermanager.ActiveConnection:
        version = 6
    else:
        # Hack. I don't remember why this is needed.
        version = 4
except:
    version = 4


if version == 4:
    # helpers.py
    import sys
    sys.path.append(paraview_scripts_directory)
    import helpers
    from paraview import servermanager
else:
    from paraview import simple


if not servermanager.ActiveConnection:
    if version == 4 or version == 5:
        servermanager.Connect()
    else:
        simple.Connect()


try:
    views = servermanager.GetRenderViews()
    if len(views) > 0:
        print 'reuse render view'
        rv = views[0]
    else:
        print 'new render view'
        rv = servermanager.CreateRenderView()
except KeyError:
    rv = servermanager.CreateRenderView()


# From simple.py.
class _funcs_internals:
    "Internal class."
    first_render = True
    view_counter = 0
    rep_counter = 0


def clear():
    def name(proxy):
        return (type(proxy)).__name__

    def compare_glyphs_first(x,y):
        if name(x)[-5:] == 'Glyph':
            return -1
        if name(y)[-5:] == 'Glyph':
            return 1
        return cmp(x,y)

    if version == 4:
        pxm = servermanager.ProxyManager()
        for proxy in sorted(pxm.GetProxiesInGroup('sources').itervalues(),
                            compare_glyphs_first):
            helpers.Delete(proxy, version)
    else:
        for proxy in sorted(simple.GetSources().itervalues(), 
                            compare_glyphs_first):
            # Hack to avoid 'Connection sink not found in the pipeline model'.
            if hasattr(proxy, "Input"):
                proxy.Input = None
            simple.Delete(proxy)


def register(proxy, name):
    # Hack to avoid 'Connection sink not found in the pipeline model' in 
    '''
    if hasattr(proxy, "Input"):
        input = proxy.Input
    else:
        input = None
    '''

    # No need to unregister when using servermanager.sources/filters.
    # Or: no need to register when using simple.Glyph() etc.
    #servermanager.UnRegister(proxy)
    servermanager.Register(proxy) #, registrationName=name)

    '''
    # Reset input.
    if input != None:
        proxy.Input = input
    '''


def add_pvd_reader(file, name):
    reader = servermanager.sources.PVDReader(FileName=file)
    register(reader, name)
    # Extra update.
    reader.UpdatePipeline()
    reader.UpdatePipelineInformation()
    return reader


def add_extract_block(data, indices, name):
    block = servermanager.filters.ExtractBlock(Input=data, 
                                               BlockIndices=indices)

    # This is needed otherwise SetScaleFactor and TensorGlyph don't work.
    block.UpdatePipeline();
    block.UpdatePipelineInformation();

    register(block, name)
    return block


def add_sphere_glyph(input, resolution=None):
    if version == 4:
        source = servermanager.sources.SphereSource()
        glyph = servermanager.filters.Glyph(Input=input, 
                                               Source=source)

        # Prevent "selected proxy value not in the list".
        # http://www.paraview.org/pipermail/paraview/2008-March/007416.html
        sourceProperty = glyph.GetProperty("Source")
        domain = sourceProperty.GetDomain("proxy_list");
        domain.AddProxy(source.SMProxy)

        glyph.SetScaleMode = 0
        glyph.SelectInputScalars = ['0', '0', '0', '0', 'radii']

        if resolution != None:
            glyph.ThetaResolution = resolution
            glyph.PhiResolution = resolution
    else:
        glyph = servermanager.filters.Glyph(Input=input, 
                                               GlyphType='Sphere')
        glyph.ScaleMode = 'scalar'

        if resolution != None:
            glyph.GlyphType.ThetaResolution = resolution
            glyph.GlyphType.PhiResolution = resolution

    glyph.SetScaleFactor = 1

    register(glyph, 'SphereGlyph')
    return glyph


def add_tensor_glyph(data, type, name):
    tensor_glyph = servermanager.filters.TensorGlyph(Input=data, 
                                                     GlyphType=type)
    #tensor_glyph = vtk.vtkTensorGlyph(data, GlyphType=type)

    register(tensor_glyph, name)
    return tensor_glyph


def set_color(proxy, rep):
    rep.ColorArrayName = 'colors'

    if version == 4:
        rep.ColorAttributeType = 0 # point data

        # Adapted from MakeBlueToRedLT in simple.py.
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


def show(proxy):
    if version == 4:
        # Adapted from Show in simple.py.
        rep = servermanager.CreateRepresentation(proxy, rv)
        servermanager.ProxyManager().RegisterProxy("representations", \
          "my_representation%d" % _funcs_internals.rep_counter, rep)
        _funcs_internals.rep_counter += 1
    else:
        rep = simple.Show(proxy)

    rep.Visibility = 1
    rep.SelectionVisibility = 1
    return rep


print 'clear pipeline'
clear()
print 'build pipeline'


if READERS:
    files = add_pvd_reader(simulation_data_directory + '/files.pvd', 
                           'DynamicDataReader')

    static = add_pvd_reader(simulation_data_directory + '/static.pvd', 
                            'StaticDataReader')


if PARTICLES:
    particles = add_extract_block(files, [2], 'ParticleData')

    particle = add_sphere_glyph(particles)
    particle.SetScaleFactor = PARTICLE_SCALE_FACTOR

    rep = show(particle)

    set_color(particle, rep)



if SPHERES:
    spheres = add_extract_block(files, [4], 'SphereData')

    sphere = add_sphere_glyph(spheres, RESOLUTION)

    rep = show(sphere)

    set_color(sphere, rep)
    rep.Representation = 'Wireframe'
    rep.Opacity = 0.5


if CYLINDERS:
    cylinders = add_extract_block(files, [6], 'CylinderData')
    cylinder = add_tensor_glyph(cylinders, 'Cylinder', 
                                'CylinderTensorGlyph')
    #simple.Show(cylinder)
    # Todo.
    #cylinder.GlyphType.Resolution = RESOLUTION

    rep = simple.GetDisplayProperties(cylinder)
    rep.Representation = 'Wireframe'
    rep.Opacity = 1.0

    # Todo.
    #range = cylinder.PointData[0].GetRange()
    #rep.LookupTable = simple.MakeBlueToRedLT(range[0], range[1])


if HELIX:
    helix_file = open(paraview_scripts_directory + '/helix.py', 'r')
    if version == 4 or version == 5:
        #helix = ProgrammableFilter()
        #helix.Script = helix_file.read()
        #servermanager.Register(helix) # Needed, or register.
        pass
    else:
        # Todo. Scale it.
        helix = servermanager.sources.ProgrammableSource()
        helix.Script = helix_file.read()
        register(helix, 'Helix')
        simple.Show(helix)


if SURFACES and version == 6:
    # Cylindrical surfaces.
    cylindrical_surfaces = add_extract_block(static, [2], 
                                             'CylindricalSurfaceData')
    cylindrical_surface = add_tensor_glyph(cylindrical_surfaces, 
                                           'Cylinder', 
                                           'CylinderTensorGlyph')
    #simple.Show(cylindrical_surface)
    # Todo. 
    #cylindrical_surface = TensorGlyphWithCustomSource(cylindrical_surfaces)
    #... Input=helix
    rep = simple.GetDisplayProperties(cylindrical_surface)
    rep.Opacity = 0.2


    # Planar surfaces.
    planar_surfaces = add_extract_block(static, [4], 'PlanarSurfaceData')
    planar_surface = add_tensor_glyph(planar_surfaces, 'Box', 
                                      'BoxTensorGlyph')
    #simple.Show(planar_surface)
    rep = simple.GetDisplayProperties(planar_surface)
    rep.Representation = 'Wireframe'
    rep.Opacity = 0.2


    # Cuboidal surfaces.
    cuboidal_surfaces = add_extract_block(static, [6], 
                                          'CuboidalSurfaceData')
    cuboidal_surface = add_tensor_glyph(cuboidal_surfaces, 'Box', 
                                        'BoxTensorGlyph')
    #simple.Show(cuboidal_surface)
    rep = simple.GetDisplayProperties(cuboidal_surface)
    rep.Representation = 'Wireframe'
    rep.Opacity = 1.0


# Todo. Turn camera.
#SetActiveSource(cylindrical_surface)

# Todo.
if version == 4 or version == 5:
    rv.StillRender()
    rv.ResetCamera()
    #simple.ResetCamera(rv)
else:
    renderer = simple.Render()
    renderer.Background = [0,0,0] # Black.
    simple.ResetCamera()

#rep = simple.GetDisplayProperties(cylinder)




