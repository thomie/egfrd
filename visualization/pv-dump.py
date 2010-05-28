
#                                                    PV-Dump.py
# Script to be run inside Paraview:
#  Menu Tools -> Python Shell, Run Script
# Afterwards, try using "help(Dump)", "Dump.proxyList()" ...
import re

class Dump:
  """Collection of 'static methods' useful to inspect a running Paraview
  pipeline (dumping information to screen or Python code)."""

  @staticmethod
  def proxyList():
    """Prints current proxies groups and names"""
    proxies = Dump.__getProxies()
    for group in proxies:
      print "* ", group
      for name in proxies[group]:
        print "   - ", name, " ( ", proxies[group][name].SMProxy.GetXMLGroup(), " )"
      print

  @staticmethod
  def allToPython( fileName=None ):
    """Prints the python code necessary to recreate the current PV session.
    If a file name is provided, it is save into the file."""
    import sys
    
    if fileName:
      stdoutOrig = sys.stdout
      file = open( fileName, 'w')
      sys.stdout = file
  
    Dump.__scriptStart()
    Dump.proxiesToPython()
    Dump.__scriptEnd()
  
    if fileName:
      sys.stdout = stdoutOrig
      file.close()
  
  
  @staticmethod
  def proxiesToPython( includeAll=False ):
    """Prints python code to create the current proxies.
    By default some PV infrastructure proxies are not printed,
    but if includeAll is True all of them are printed."""
    proxies = Dump.__getProxies()
  
    order   = Dump.__orderProxies( proxies )  # Get proxies
                                            # ordered by dependencies among them
    for level in order:
      for item in level:
        (group, name) = item.split(':')                        # Iterate on them
  
        wrapName  = proxies[group][name].SMProxy.GetXMLName()
  
        if includeAll or wrapName not in Dump.__HIDDENPROXIES: # Avoid defaults
          Dump.proxyToPython( group, name, Dump.__niceLabel(name)) # Dump code
  
      print
    
  @staticmethod
  def proxyToPython(group, name, varName='proxy'):
    """Prints the python code necessary to create and setup the given proxy,
    using varName as the variable identifier"""
    proxies   = Dump.__getProxies()
    proxy     = proxies[group][name]
    wrapGroup = proxy.SMProxy.GetXMLGroup()
    wrapName  = proxy.SMProxy.GetXMLName()
    print ' '*54, "# ", varName                        # Code: create
    if wrapName == "LODDisplay":                       #  - display proxy
      dispInput = Dump.__niceLabel( Dump.__proxyIdLabel( proxy.GetInput()[0] ) )
      print varName +' = paraview.CreateDisplay(' \
                         + dispInput +', renderM)'
    else:                                              #  - other proxies
      print varName +' = paraview.CreateProxy("' \
                         + wrapGroup +'", "'+ wrapName +'", "' \
                         + group     +'", "'+ name +'")'
    
    patternName   = re.compile(' *XMLName: *(.*)')
    patternValues = re.compile(' *Values: *(.*)')
    patternNum    = re.compile('^[-+]?[0-9.]+$')
    patternHex    = re.compile('^0x[0-9a-f]+$')
    patternBadProp= re.compile('LightK\:')
    for prop in proxy:                                 # For each property
      match     = patternName.search( str(prop) )
      propName = match.groups()[0]
      match     = patternValues.search( str(prop) )    # Get property.Values
      if match:
        values      = match.groups()[0]
        valuesArray = values.strip().split(' ') 
  
        if   patternNum.match( valuesArray[0] ):       # If numeric: no quote
          valuesList = ', '.join( valuesArray )
  
        elif patternHex.match( valuesArray[0] ):       # If hex: fetch object
          valuesArray = proxy.__getattr__("Get"+propName)()
          valuesList = ', '.join( Dump.__niceLabel( Dump.__proxyIdLabel(p) )
                                  for p in valuesArray)
  
        else:                                          # If alpha: quote
          valuesList = ', '.join('"' + p + '"' for p in valuesArray)
  
                                                       # Code: set value
        if not patternBadProp.search( propName ) and \
           valuesList != "none" and \
           valuesList != '""':
          print varName +'.Set'+ propName +'( '+ valuesList +' )'
        else:                                          # Code: comment
          print '# '+ varName +'.Set'+ propName +'( '+ valuesList +' )'
      #else:
      #  print '# '+ varName +'.'+ propName +': no match for Values'
    print varName +'.UpdateVTKObjects()'
    print
  
  



  # Private -----------------------------------------------
  
  __HIDDENPROXIES = [ "Manipulators",     "InteractorStyle", "TrackballZoom",
                      "PVAnimationScene", "TimeKeeper",      "ElementInspectorView",
                      "LODRenderModule", "MultiViewRenderModule" ]
  
  @staticmethod
  def __getProxies():
    """Returns the list of proxies in the current connection"""
    proxies = paraview.servermanager.ProxyManager().GetProxiesOnConnection( \
                                     paraview.ActiveConnection )
    return proxies
  
  @staticmethod
  def __orderProxies( proxies ):
    """Returns an array, where each entry contains the names of the proxies that
    depend on the previous array entry."""
    patternName   = re.compile(' *XMLName: *(.*)')
    patternValues = re.compile(' *Values: *(.*)')
    patternHex    = re.compile('^0x[0-9a-f]+$')
    pmanager      = paraview.pyProxyManager()
  
    dependencies  = {}                                        # COLLECT DEPS
    for group in proxies:                                     # For each proxy
      for name in proxies[group]:
        dependencies[group+':'+name] = {}                     # Init its depend.
        proxy = proxies[group][name]
  
        for prop in proxy:
          match     = patternName.search( str(prop) )
          propName  = match.groups()[0]
          match     = patternValues.search( str(prop) )       # Check prop. values
          if match:
            values      = match.groups()[0]
            valuesArray = values.strip().split(' ') 
  
            if patternHex.match( valuesArray[0] ):            # If memory address
              valuesArray = proxy.__getattr__("Get"+propName)()
              for mother in valuesArray:
                motherProxyVTK = mother.SMProxy
  
                for motherGroup in proxies:                   # Find proxy by addr
                  motherName= pmanager.IsProxyInGroup( motherProxyVTK, motherGroup )
                  if motherName:
                     dependencies[group+':'+name][motherGroup+':'+motherName]=1
  
  
  
    order = [] ; currentLevel = [] ; previousLevel = []       # ORDER DEPS
  
    for proxy in pmanager.GetProxiesInGroup('view_modules',   # Start by Views
                                             paraview.ActiveConnection):
      previousLevel.append( 'view_modules:'+ proxy )
  
    renders = pmanager.GetProxiesInGroup("multirendermodule", # add Renderers
                                         paraview.ActiveConnection)
    for renderM in renders.keys():
      previousLevel.append( 'multirendermodule:'+renderM )
  
    order.append( previousLevel )
  
    while len( previousLevel ) > 0:                           # Follow depend.
  
      for item in previousLevel:
        currentLevel.extend( dependencies[ item ].keys() )
  
      if len(currentLevel) > 0 :order.append( currentLevel )
  
      previousLevel = [] ; previousLevel.extend( currentLevel )
      currentLevel  = []
  
    order.reverse()                                           # First pxs w/o deps
  
    uniqueOrder = [] ; alreadyDeclared = {}                   # Remove duplicates
    for level in order:
      newLevel = []
      for item in level:
        if not alreadyDeclared.get( item ):
          alreadyDeclared[ item ] = True
          newLevel.append( item )
  
      uniqueOrder.append( newLevel )
  
    return uniqueOrder
  
  
  @staticmethod
  def __niceLabel( label ):
    """Returns a string that can be used as var name
    (starting by a letter, without .-_, ...)"""
    if not label: return "none"
  
    label = label.replace('.', '')            # drop .-_
    label = label.replace('-', '')
    label = label.replace('_', '')
  
    if re.compile('[A-z]1').match( label[-2:] ):
      label = label[0:-1]                     # drop suffix '1'
  
    if re.compile('^[0-9]').match( label ):
      label = 'v' + label                     # add preffix when starts by number
  
    label = label[0].lower() + label[1:]      # lower 1st char
  
    return label
  
  @staticmethod
  def __proxyIdLabel( proxy ):
    """Returns the given proxy's PV displayed name"""
    proxyVTK = proxy.SMProxy
    pmanager = paraview.pyProxyManager()
    proxies  = Dump.__getProxies()
    for group in proxies:
      idLabel = pmanager.IsProxyInGroup( proxyVTK, group )
      if idLabel:
         return idLabel
    return None
  
  
  @staticmethod
  def __scriptStart(): 
    print '#!/usr/local/bin/pvpython'
    print '#                                                    <script>.py'
    print 'import paraview'
    print 'if     paraview.ActiveConnection == None : CONSOLE = True'
    print 'else                                     : CONSOLE = False'
    print 'if CONSOLE:                                           # init Conn and RenderM'
    print '  paraview.ActiveConnection = paraview.Connect()'
    print '  renderM = paraview.CreateRenderWindow()'
    print 'else:'
    print '  renders = paraview.pyProxyManager().GetProxiesInGroup("multirendermodule",'
    print '                                                  paraview.ActiveConnection)'
    print '  renderM = renders.values()[0].GetRenderModules()[0]'
    print
  
  @staticmethod
  def __scriptEnd(): 
    print
    print 'if CONSOLE:'
    print '  renderM.ResetCamera()'
    print '  renderM.StillRender()'
    print '  raw_input("Enter to finish")'
    print '  #import time ; time.sleep(2)'

