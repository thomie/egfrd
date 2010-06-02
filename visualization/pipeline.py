from paraview import servermanager
from paraview import vtk

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
#HELIX     = True
SURFACES  = True


PARTICLE_SCALE_FACTOR = 4
RESOLUTION = 18


if not servermanager.ActiveConnection:
    exit('pvpython not supported')


# Detect version.
try:
    from paraview import simple
    version = 6
except ImportError:
    version = 4


views = servermanager.GetRenderViews()
if len(views) > 0:
    rv = views[0]
else:
    rv = servermanager.CreateRenderView()


def clear():
    def name(proxy):
        return (type(proxy)).__name__

    def programmable_filters_first_then_glyphs(x,y):
        if name(x) == 'ProgrammableFilter':
            return -1
        elif name(y) == 'ProgrammableFilter':
            return 1
        elif name(x)[-5:] == 'Glyph':
            return -1
        elif name(y)[-5:] == 'Glyph':
            return 1
        return cmp(x,y)

    pxm = servermanager.ProxyManager()
    for proxy in pxm.GetProxiesInGroup('lookup_tables').itervalues():
        servermanager.UnRegister(proxy)

    if version == 4:
        for proxy in sorted(pxm.GetProxiesInGroup('sources').itervalues(),
                            programmable_filters_first_then_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            servermanager.UnRegister(proxy)
        for proxy in pxm.GetProxiesInGroup('representations').itervalues():
            servermanager.UnRegister(proxy)

        rv.Representations = []
    else:
        for proxy in sorted(simple.GetSources().itervalues(), 
                            programmable_filters_first_then_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            simple.Delete(proxy)

    rv.ResetCamera()
    rv.StillRender()


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


def add_tensor_glyph(input, type, resolution=None, name=None):
    if version == 4:
        #tensor_glyph = vtk.vtkTensorGlyph(data, GlyphType=type)
        pass
    else:
        tensor_glyph = servermanager.filters.TensorGlyph(Input=input,
                                                         GlyphType=type)

        if resolution != None:
            tensor_glyph.GlyphType.Resolution = resolution

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


# Taken from simple.py (ParaView 3.6).
class _funcs_internals:
    "Internal class."
    first_render = True
    view_counter = 0
    rep_counter = 0

def show(proxy):
    if version == 4:
        # Adapted from Show in simple.py (ParaView 3.6).
        rep = servermanager.CreateRepresentation(proxy, rv)
        servermanager.ProxyManager().RegisterProxy("representations", \
          "my_representation%d" % _funcs_internals.rep_counter, rep)
        _funcs_internals.rep_counter += 1
    else:
        rep = simple.Show(proxy)

    rep.Visibility = 1
    return rep


print 'clear pipeline'
clear()
print 'build pipeline'


if READERS:
    files = add_pvd_reader(simulation_data_directory + '/files.pvd', 
                           'files.pvd')

    static = add_pvd_reader(simulation_data_directory + '/static.pvd', 
                            'static.pvd')


if PARTICLES:
    particles = add_extract_block(files, [2], 'b1')

    particle = add_sphere_glyph(particles, name='Particles')
    particle.SetScaleFactor = PARTICLE_SCALE_FACTOR

    rep = show(particle)

    set_color(particle, rep)


if SPHERES:
    spheres = add_extract_block(files, [4], 'b2')

    sphere = add_sphere_glyph(spheres, RESOLUTION, name='Spheres')

    rep = show(sphere)

    set_color(sphere, rep)
    rep.Representation = 'Wireframe'
    rep.Opacity = 0.5


if CYLINDERS:
    cylinders = add_extract_block(files, [6], 'b3')
    cylinder = add_tensor_glyph(cylinders, 'Cylinder', resolution=RESOLUTION,
                                name='tg')

    rep = show(cylinder)

    rep.Visibility = 0
    programmable_filter = programmable_filter_color_hack(cylinder,
                                                         name='Cylinders')
    rep = show(programmable_filter)

    set_color(programmable_filter, rep)
    rep.Representation = 'Wireframe'
    rep.Opacity = 1.0


if HELIX:
    helix_file = open(paraview_scripts_directory + '/helix.py', 'r')
    if version == 4:
        #helix = ProgrammableFilter()
        #helix.Script = helix_file.read()
        #servermanager.Register(helix) # Needed, or register.
        pass
    else:
        # Todo. Scale it.
        helix = servermanager.sources.ProgrammableSource()
        helix.Script = helix_file.read()
        servermanager.Register(helix, registrationName='Helix')
        simple.Show(helix)

    helix_file.close()


if SURFACES:
    # Cylindrical surfaces.
    cylindrical_surfaces = add_extract_block(static, [2], 'b1')
    cylindrical_surface = add_tensor_glyph(cylindrical_surfaces, 'Cylinder',
                                           name='Cylindrical Surfaces')

    rep = show(cylindrical_surface)

    # Todo. 
    #cylindrical_surface = TensorGlyphWithCustomSource(cylindrical_surfaces)
    #... Input=helix

    rep = simple.GetDisplayProperties(cylindrical_surface)
    rep.Opacity = 1.0


    # Planar surfaces.
    planar_surfaces = add_extract_block(static, [4], 'b2')
    planar_surface = add_tensor_glyph(planar_surfaces, 'Box', 
                                      name='Planar Surfaces')

    rep = show(planar_surface)
    rep.Representation = 'Surface'
    rep.Opacity = 0.5


    # Cuboidal surfaces.
    cuboidal_regions = add_extract_block(static, [6], 'b3')
    cuboidal_region = add_tensor_glyph(cuboidal_regions, 'Box',
                                       name='Cuboidal Regions')

    rep = show(cuboidal_region)
    rep.Representation = 'Wireframe'
    rep.Opacity = 1.0


SetActiveSource(cylindrical_surface)

# Set camera.
cam = GetActiveCamera()
rv.ResetCamera()
cam.SetViewUp(0,0,1)
focal = cam.GetFocalPoint()
cam.SetPosition(focal[0]*10, focal[1], focal[2])

rv.Background = [0,0,0] # Black.
rv.ResetCamera()
rv.StillRender()


