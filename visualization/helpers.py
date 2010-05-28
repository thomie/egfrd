from paraview import servermanager

def Connect(ds_host=None, ds_port=11111, rs_host=None, rs_port=11111):
    """Creates a connection to a server. Example usage:
    > Connect("amber") # Connect to a single server at default port
    > Connect("amber", 12345) # Connect to a single server at port 12345
    > Connect("amber", 11111, "vis_cluster", 11111) # connect to data server, render server pair
    This also create a default render view."""
    servermanager.ProxyManager().UnRegisterProxies()
    active_objects.view = None
    active_objects.source = None
    import gc
    gc.collect()
    servermanager.Disconnect()
    cid = servermanager.Connect(ds_host, ds_port, rs_host, rs_port)
    servermanager.ProxyManager().RegisterProxy("timekeeper", "tk", servermanager.misc.TimeKeeper())

    return cid


# TODO: Change this to take the array name and number of components. Register 
# the lt under the name ncomp.array_name
def MakeBlueToRedLT(min, max):
    # Define RGB points. These are tuples of 4 values. First one is
    # the scalar values, the other 3 the RGB values. 
    rgbPoints = [min, 0, 0, 1, max, 1, 0, 0]
    return CreateLookupTable(RGBPoints=rgbPoints, ColorSpace="HSV")
    

def CreateLookupTable(**params):
    """Create and return a lookup table.  Optionally, parameters can be given
    to assign to the lookup table.
    """
    lt = servermanager.rendering.PVLookupTable()
    servermanager.Register(lt)
    SetProperties(lt, **params)
    return lt


def SetProperties(proxy=None, **params):
    """Sets one or more properties of the given pipeline object. If an argument
    is not provided, the active source is used. Pass a list of property_name=value
    pairs to this function to set property values. For example:
     SetProperties(Center=[1, 2, 3], Radius=3.5)
    """
    if not proxy:
        proxy = active_objects.source
    for param in params.keys():
        if not hasattr(proxy, param):
            raise AttributeError("object has no property %s" % param)
        setattr(proxy, param, params[param])


def GetSources():
    """Given the name of a source, return its Python object."""
    return servermanager.ProxyManager().GetProxiesInGroup("sources")


def Delete(proxy, version=6):
    """Deletes the given pipeline object or the active source if no argument
    is specified."""
    if not proxy:
        proxy = active_objects.source
    # Unregister any helper proxies stored by a vtkSMProxyListDomain
    for prop in proxy:
        listdomain = prop.GetDomain('proxy_list')
        if listdomain:
            if listdomain.GetClassName() != 'vtkSMProxyListDomain':
                continue
            group = "pq_helper_proxies." + proxy.GetSelfIDAsString()
            for i in xrange(listdomain.GetNumberOfProxies()):
                pm = servermanager.ProxyManager()
                iproxy = listdomain.GetProxy(i)
                name = pm.GetProxyName(group, iproxy)
                if iproxy and name:
                    pm.UnRegisterProxy(group, name, iproxy)
                    

    # Remove source/view from time keeper
    if version == 4 or version == 5:
        # Paraview 3.4.
        # Paraview 3.6 mimicking 3.4.
        # Todo.
        pass
    else:
        # Paraview 3.6.
        tk = servermanager.ProxyManager().GetProxiesInGroup("timekeeper").values()[0]

        if isinstance(proxy, servermanager.SourceProxy):
            try:
                idx = tk.TimeSources.index(proxy)
                del tk.TimeSources[idx]
                pass
            except ValueError:
                pass
        else:
            try:
                idx = tk.Views.index(proxy)
                del tk.Views[idx]
            except ValueError:
                pass
    
    # If this is a representation, remove it from all views.
    if proxy.SMProxy.IsA("vtkSMRepresentationProxy"):
        for view in GetRenderViews():
            view.Representations.remove(proxy)
    # If this is a source, remove the representation iff it has no consumers
    # Also change the active source if necessary
    elif proxy.SMProxy.IsA("vtkSMSourceProxy"):
        sources = servermanager.ProxyManager().GetProxiesInGroup("sources")
        if version == 4 or version == 5:
            # Paraview 3.4.
            # Paraview 3.6 mimicking 3.4.
            # Todo.
            pass
        else:
            # Paraview 3.6.
            for i in range(proxy.GetNumberOfConsumers()):
                if proxy.GetConsumerProxy(i) in sources:
                    raise RuntimeError("Source has consumers. It cannot be deleted " +
                      "until all consumers are deleted.")
            if proxy == GetActiveSource():
                if hasattr(proxy, "Input") and proxy.Input:
                    if isinstance(proxy.Input, servermanager.Proxy):
                        SetActiveSource(proxy.Input)
                    else:
                        SetActiveSource(proxy.Input[0])
                else: SetActiveSource(None)
        for rep in GetRepresentations().values():
            if rep.Input == proxy:
                # Hack to avoid 'Connection sink not found in the pipeline 
                # model' in Paraview 3.6.
                #rep.Input = None
                Delete(rep)
    # Change the active view if necessary
    elif proxy.SMProxy.IsA("vtkSMRenderViewProxy"):
        if proxy == GetActiveView():
            if len(GetRenderViews()) > 0:
                SetActiveView(GetRenderViews()[0])
            else:
                SetActiveView(None)

    if hasattr(proxy, "Input"):
        proxy.Input = None
    servermanager.UnRegister(proxy)


def GetRepresentations():
    """Returns all representations (display properties)."""
    return servermanager.ProxyManager().GetProxiesInGroup("representations")


def GetActiveSource():
    "Returns the active source."
    return active_objects.source


def SetActiveSource(source):
    "Sets the active source."
    active_objects.source = source
    

def CreateRenderView():
    "Creates and returns a 3D render view."
    view = servermanager.CreateRenderView()
    servermanager.ProxyManager().RegisterProxy("views", \
      "my_view%d" % _funcs_internals.view_counter, view)
    active_objects.view = view
    _funcs_internals.view_counter += 1
    
    tk = servermanager.ProxyManager().GetProxiesInGroup("timekeeper").values()[0]
    views = tk.Views
    if not view in views:
        views.append(view)

    return view


class _funcs_internals:
    "Internal class."
    first_render = True
    view_counter = 0
    rep_counter = 0


def GetRenderViews():
    "Returns all render views as a list."
    return servermanager.GetRenderViews()


def Show(proxy=None, view=None, **params):
    """Turns the visibility of a given pipeline object on in the given view.
    If pipeline object and/or view are not specified, active objects are used."""
    if proxy == None:
        proxy = GetActiveSource()
    if proxy == None:
        raise RuntimeError, "Show() needs a proxy argument or that an active source is set."
    if not view and len(GetRenderViews()) == 0:
        CreateRenderView()
    rep = GetDisplayProperties(proxy, view)
    if rep == None:
        raise RuntimeError, "Could not create a representation object for proxy %s" % proxy.GetXMLLabel()
    for param in params.keys():
        setattr(rep, param, params[param])
    rep.Visibility = 1
    return rep

class ActiveObjects(object):
    """This class manages the active objects (source and view). The active
    objects are shared between Python and the user interface. This class
    is for internal use. Use the Set/Get methods for setting and getting
    active objects."""
    def __get_selection_model(self, name):
        "Internal method."
        pxm = servermanager.ProxyManager()
        model = pxm.GetSelectionModel(name)
        if not model:
            model = servermanager.vtkSMProxySelectionModel()
            pxm.RegisterSelectionModel(name, model)
        return model

    def set_view(self, view):
        "Sets the active view."
        active_view_model = self.__get_selection_model("ActiveView") 
        if view:
            active_view_model.SetCurrentProxy(view.SMProxy, 0)
        else:
            active_view_model.SetCurrentProxy(None, 0)

    def get_view(self):
        "Returns the active view."
        return servermanager._getPyProxy(
            self.__get_selection_model("ActiveView").GetCurrentProxy())

    def set_source(self, source):
        "Sets the active source."
        active_sources_model = self.__get_selection_model("ActiveSources") 
        if source:
            # 3 == CLEAR_AND_SELECT
            active_sources_model.SetCurrentProxy(source.SMProxy, 3)
        else:
            active_sources_model.SetCurrentProxy(None, 3)

    def __convert_proxy(self, px):
        "Internal method."
        if not px:
            return None
        if px.IsA("vtkSMSourceProxy"):
            return servermanager._getPyProxy(px)
        else:
            return servermanager.OutputPort(
              servermanager._getPyProxy(px.GetSourceProxy()),
              px.GetPortIndex())
        
    def get_source(self):
        "Returns the active source."
        return self.__convert_proxy(
          self.__get_selection_model("ActiveSources").GetCurrentProxy())

    def get_selected_sources(self):
        "Returns the set of sources selected in the pipeline browser."
        model = self.__get_selection_model("ActiveSources")
        proxies = []
        for i in xrange(model.GetNumberOfSelectedProxies()):
            proxies.append(self.__convert_proxy(model.GetSelectedProxy(i)))
        return proxies

    view = property(get_view, set_view)
    source = property(get_source, set_source)

active_objects = ActiveObjects()


def GetDisplayProperties(proxy=None, view=None):
    """"Given a pipeline object and view, returns the corresponding representation object.
    If pipeline object and/or view are not specified, active objects are used."""
    return GetRepresentation(proxy, view)
    

def GetRepresentation(proxy=None, view=None):
    """"Given a pipeline object and view, returns the corresponding representation object.
    If pipeline object and view are not specified, active objects are used."""
    if not view:
        view = active_objects.view
    if not proxy:
        proxy = active_objects.source
    rep = servermanagerGetRepresentation(proxy, view)
    if not rep:
        rep = servermanager.CreateRepresentation(proxy, view)
        servermanager.ProxyManager().RegisterProxy("representations", \
          "my_representation%d" % _funcs_internals.rep_counter, rep)
        _funcs_internals.rep_counter += 1
    return rep
    
def servermanagerGetRepresentation(aProxy, view):
    for rep in view.Representations:
        try: isRep = rep.Input == aProxy
        except: isRep = False
        if isRep: return rep
    return None

def Render(view=None):
    """Renders the given view (default value is active view)"""
    if not view:
        view = active_objects.view
    view.StillRender()
    if _funcs_internals.first_render:
        view.ResetCamera()
        view.StillRender()
        _funcs_internals.first_render = False
    return view
        

def ResetCamera(view=None):
    """Resets the settings of the camera to preserver orientation but include
    the whole scene. If an argument is not provided, the active view is
    used."""
    if not view:
        view = active_objects.view
    view.ResetCamera()
    Render(view)

def UpdatePipeline(time=None, proxy=None):
    """Updates (executes) the given pipeline object for the given time as
    necessary (i.e. if it did not already execute). If no source is provided,
    the active source is used instead."""
    if not proxy:
        proxy = active_objects.source
    if time:
        proxy.UpdatePipeline(time)
    else:
        proxy.UpdatePipeline()
