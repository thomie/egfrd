#!/usr/env python


from weakref import ref
import math

import numpy

from _gfrd import EventScheduler, FirstPassageGreensFunction, FirstPassagePairGreensFunction, FirstPassageNoCollisionPairGreensFunction, BasicPairGreensFunction, FreePairGreensFunction, EventType, Particle, Shell, ShellContainer, DomainIDGenerator, ShellIDGenerator, DomainID, ParticleContainer, ShellContainer

from surface import CuboidalSurface

from gfrdbase import *
from utils import *
from cObjectMatrix import ObjectMatrix
from bd import BDSimulatorCoreBase
import myrandom

import logging
import os

log = logging.getLogger('ecell')

SAFETY = 1.0 + 1e-5

class Delegate( object ):
    def __init__( self, obj, method ):
        self.ref = ref( obj )
        self.method = method

    def __call__( self, *arg ):
        return self.method( self.ref(), *arg )


class MultiBDCore( BDSimulatorCoreBase ):
    '''
    Used internally by Multi.
    '''
    def __init__( self, main, multi ):

        BDSimulatorCoreBase.__init__( self, main )

        # this has to be ref, not proxy, since it is used for comparison.
        self.multiref = ref( multi )

        self.particleMatrix = ParticleContainer(self.main.worldSize, self.main.matrixSize)
        self.shellMatrix = ShellContainer(self.main.worldSize, self.main.matrixSize)
        self.escaped = False

    def updateParticle( self, pid_particle_pair ):
        self.particleMatrix.update( pid_particle_pair )
        self.main.moveParticle( pid_particle_pair )

    def initialize( self ):
        BDSimulatorCoreBase.initialize( self )

    def step( self ):
        self.escaped = False
        BDSimulatorCoreBase.step( self )

    def addParticle(self, pid_particle_pair):
        self.addToParticleList(pid_particle_pair[0])
        self.particleMatrix.update(pid_particle_pair)

    def removeParticle( self, pid_particle_pair):
        self.main.removeParticle(pid_particle_pair)
        self.removeFromParticleList(pid_particle_pair[0])
        del self.particleMatrix[pid_particle_pair[0]]

    def createParticle( self, species, pos ):
        particle = self.main.createParticle( species, pos )
        self.addParticle( particle )
        return particle

    def moveParticle( self, pid_particle_pair ):
        self.updateParticle( pid_particle_pair )

    def clearVolume( self, pos, radius, ignore=[] ):
        if not self.withinShell( pos, radius ):
            self.escaped = True
            self.clearOuterVolume( pos, radius, ignore )

    def clearOuterVolume( self, pos, radius, ignore=[] ):
        self.main.clearVolume( pos, radius, ignore=[self.multiref().domain_id,] )
        if self.main.checkOverlap( pos, radius, ignore ):
            raise NoSpace()

    def withinShell( self, pos, radius ):
        result = self.shellMatrix.get_neighbors_within_radius( pos, - radius )
        return bool(result)
        
    def checkOverlap( self, pos, radius, ignore=[] ):
        result = self.particleMatrix.get_neighbors_within_radius( pos, radius )
        for item in result:
            if item[0][0] not in ignore:
                return item
        return None

    def getParticlesWithinRadiusNoSort( self, pos, radius, ignore=[] ):
        result = self.particleMatrix.get_neighbors_within_radius( pos, radius )
        return [ n[0] for n in result if n[0][0] not in ignore ]

    def check( self ):
        BDSimulatorCoreBase.check( self )

        # shells are contiguous
        for shell in self.multiref().shell_list:
            result = self.shellMatrix.get_neighbors(shell[1].position)
            d = None
            for i in result:
                if i[0][0] == shell[0]:
                    continue
                d = i
            assert d is not None
            assert d[1] - shell[1].radius < 0.0,\
                'shells of %s are not contiguous.' % str(self.multiref())

        # all particles within the shell.
        for pid in self.particleList:
            p = self.main.particleMatrix[pid] 
            assert self.withinShell( p.position, p.radius ),\
                'not all particles within the shell.'


class Single( object ):
    def __init__( self, domain_id, pid_particle_pair, shell_id_shell_pair, reactiontypes ):
        self.multiplicity = 1

        self.pid_particle_pair = pid_particle_pair
        self.reactiontypes = reactiontypes

        self.k_tot = 0

        self.lastTime = 0.0
        self.dt = 0.0
        self.eventType = None

        self.shell_list = [shell_id_shell_pair, ]

        self.eventID = None

        self.domain_id = domain_id

        self.updatek_tot()

    def getD( self ):
        return self.pid_particle_pair[1].D
    D = property( getD )

    def getMinRadius(self):
        return self.pid_particle_pair[1].radius
    minRadius = property(getMinRadius)

    def getShell(self):
        return self.shell_list[0]

    def setShell(self, value):
        self.shell_list[0] = value

    shell = property(getShell, setShell)

    def initialize( self, t ):
        '''
        Initialize this Single.

        The radius (shell size) is shrunken to the radius of the particle
        it represents.   
        self.lastTime is reset to the current time, and self.dt
        is set to zero.
        '''
        self.reset()
        self.lastTime = t

    def reset( self ):
        '''
        Reset the Single.

        Radius (shell size) is shrunken to the actual radius of the particle.
        self.dt is reset to 0.0.  Do not forget to reschedule this Single
        after calling this method.
        '''
        self.dt = 0.0
        self.eventType = EventType.ESCAPE

    def isReset( self ):
        return self.dt == 0.0 and self.eventType == EventType.ESCAPE
        
    def drawR( self, dt, shellSize):
        assert dt >= 0
        a = shellSize - self.pid_particle_pair[1].radius
        rnd = myrandom.uniform()
        gf = FirstPassageGreensFunction( self.pid_particle_pair[1].D )
        gf.seta(a)
        try:
            r = gf.drawR(rnd , dt)
        except Exception, e:
            raise Exception, 'gf.drawR failed; %s; rnd=%g, t=%g, %s' %\
                (str(e), rnd, dt, gf.dump())
        return r

    def drawReactionTime( self ):
        if self.k_tot == 0:
            return numpy.inf
        if self.k_tot == numpy.inf:
            return 0.0
        rnd = myrandom.uniform()
        dt = ( 1.0 / self.k_tot ) * math.log( 1.0 / rnd )
        return dt

    def drawEscapeTime(self, a):
        D = self.pid_particle_pair[1].D

        if D == 0:
            return numpy.inf

        gf = FirstPassageGreensFunction(D)
        gf.seta(a)

        rnd = myrandom.uniform()
        try:
            return gf.drawTime( rnd )
        except Exception, e:
            raise Exception, 'gf.drawTime() failed; %s; rnd=%g, %s' %\
                ( str( e ), rnd, gf.dump() )


    def updatek_tot( self ):
        self.k_tot = 0

        if not self.reactiontypes:
            return

        for rt in self.reactiontypes:
            self.k_tot += rt.k


    def drawReactionRule( self ):
        k_array = [ rt.k for rt in self.reactiontypes ]
        k_array = numpy.add.accumulate( k_array )
        k_max = k_array[-1]

        rnd = myrandom.uniform()
        i = numpy.searchsorted( k_array, rnd * k_max )

        return self.reactiontypes[i]


    def check( self ):
        pass

    def __repr__( self ):
        return 'Single[%s: %s: eventID=%s]' % ( self.domain_id, self.pid_particle_pair[0], self.eventID )


# def calculatePairCoM( pos1, pos2, D1, D2, worldSize ):
#     '''
#     Calculate and return the center-of-mass of a Pair.
#     '''
#     #pos2t = cyclicTranspose( pos2, pos1, worldSize )
#     pos2t = cyclic_transpose( pos2, pos1, worldSize )
#     return ( ( D2 * pos1 + D1 * pos2t ) / ( D1 + D2 ) ) % worldSize


class Pair( object ):
    
    # CUTOFF_FACTOR is a threshold to choose between the real and approximate
    # Green's functions.
    # H = 4.0: ~3e-5, 4.26: ~1e-6, 5.0: ~3e-7, 5.2: ~1e-7,
    # 5.6: ~1e-8, 6.0: ~1e-9
    CUTOFF_FACTOR = 5.6

    def __init__(self, domain_id, single1, single2, shell_id_shell_pair, rt):
        self.multiplicity = 2

        # Order single1 and single2 so that D1 < D2.
        if single1.pid_particle_pair[1].D <= single2.pid_particle_pair[1].D:
            self.single1, self.single2 = single1, single2 
        else:
            self.single1, self.single2 = single2, single1 

        self.rt = rt

        D1 = self.single1.pid_particle_pair[1].D
        D2 = self.single2.pid_particle_pair[1].D

        self.D_tot = D1 + D2
        self.D_R = ( D1 * D2 ) / self.D_tot

        self.sigma = self.single1.pid_particle_pair[1].radius + \
                     self.single2.pid_particle_pair[1].radius

        self.eventID = None

        self.lastTime = 0.0
        self.dt = 0.0
        self.eventType = None

        self.shell_list = [shell_id_shell_pair, ]
        self.domain_id = domain_id

    def __del__( self ):
        if __debug__:
            log.debug( 'del %s' % str( self ) )

    def getShell(self):
        return self.shell_list[0]

    def setShell(self, value):
        self.shell_list[0] = value

    shell = property(getShell, setShell)

    def initialize( self, t ):

        self.lastTime = t
        self.dt = 0
        self.eventType = None

    def getD( self ):
        return self.D_tot #FIXME: is this correct?

    def choosePairGreensFunction( self, r0, t ):
        distanceFromSigma = r0 - self.sigma
        distanceFromShell = self.a_r - r0

        thresholdDistance = Pair.CUTOFF_FACTOR * \
            math.sqrt( 6.0 * self.D_tot * t )

        if distanceFromSigma < thresholdDistance:
        
            if distanceFromShell < thresholdDistance:
                # near both a and sigma;
                # use FirstPassagePairGreensFunction
                if __debug__:
                    log.debug( 'GF: normal' )
                pgf = FirstPassagePairGreensFunction( self.D_tot, 
                                                      self.rt.k, self.sigma )

                return pgf
            else:
                # near sigma; use BasicPairGreensFunction
                if __debug__:
                    log.debug( 'GF: only sigma' )
                pgf = BasicPairGreensFunction( self.D_tot, self.rt.k, 
                                               self.sigma )
                return pgf
        else:
            if distanceFromShell < thresholdDistance:
                # near a;
                if __debug__:
                    log.debug( 'GF: only a' )
                pgf = FirstPassageNoCollisionPairGreensFunction( self.D_tot )
                return pgf
                
            else:
                # distant from both a and sigma; 
                if __debug__:
                    log.debug( 'GF: free' )
                pgf = FreePairGreensFunction( self.D_tot )
                return pgf

    def drawTime_single( self, sgf ):
        rnd = myrandom.uniform()
        return sgf.drawTime( rnd )

    def drawTime_pair( self, pgf, r0 ):
        rnd = myrandom.uniform()
        #print 'r0 = ', r0, ', rnd = ', rnd[1],\
        #    pgf.dump()
        return pgf.drawTime( rnd, r0 )

    def drawEventType( self, pgf, r0, t ):
        rnd = myrandom.uniform()
        return pgf.drawEventType( rnd, r0, t )

    def drawR_single( self, sgf, t ):
        rnd = myrandom.uniform()
        try:
            r = sgf.drawR( rnd, t )
            while r > self.a_R: # redraw; shouldn't happen often
                if __debug__:
                    log.info( 'drawR_single: redraw' )
                rnd = myrandom.uniform()
                r = sgf.drawR( rnd, t )
        except Exception, e:
            raise Exception,\
                'gf.drawR_single() failed; %s; rnd= %g, t= %g, %s' %\
                ( str( e ), rnd, t, sgf.dump() )

        return r

    def drawR_pair( self, r0, t, a ):
        '''
        Draw r for the pair inter-particle vector.
        '''
        gf = self.choosePairGreensFunction( r0, t )

        if hasattr( gf, 'seta' ):  # FIXME: not clean
            gf.seta( a )

        rnd = myrandom.uniform()
        try:
            r = gf.drawR( rnd, r0, t )
            # redraw; shouldn't happen often
            while r >= self.a_r or r <= self.sigma: 
                if __debug__:
                    log.info( 'drawR_pair: redraw' )
                #self.sim.rejectedMoves += 1  #FIXME:
                rnd = myrandom.uniform()
                r = gf.drawR( rnd, r0, t )
        except Exception, e:
            raise Exception,\
                'gf.drawR_pair() failed; %s; rnd= %g, r0= %g, t= %g, %s' %\
                ( str( e ), rnd, r0, t, gf.dump() )


        return r

    def drawTheta_pair( self, rnd, r, r0, t, a ):
        '''
        Draw theta for the pair inter-particle vector.
        '''
        gf = self.choosePairGreensFunction( r0, t )

        if hasattr( gf, 'seta' ):  # FIXME: not clean
            gf.seta( a )

        try:
            theta = gf.drawTheta( rnd, r, r0, t )
        except Exception, e:
            raise Exception,\
                'gf.drawTheta() failed; %s; rnd= %g, r= %g, r0= %g, t=%g, %s' %\
                ( str( e ), rnd, r, r0, t, gf.dump() )

        return theta

    def check( self ):
        pass

    def __repr__( self ):
        return 'Pair[%s: %s, %s: eventID=%s]' % (
            self.domain_id,
            self.single1.pid_particle_pair[0],
            self.single2.pid_particle_pair[0],
            self.eventID )


class Multi( object ):
    def __init__( self, domain_id, main ):
        self.domain_id = domain_id
        self.eventID = None
        self.sim = MultiBDCore( main, self )

    def initialize( self, t ):
        self.lastTime = t
        self.startTime = t

        self.sim.initialize() # ??

    def getDt( self ):
        return self.sim.dt

    dt = property( getDt )

    def getMultiplicity( self ):
        return len( self.sim.particleList )

    multiplicity = property( getMultiplicity )

    def addParticle(self, pid_particle_pair):
        self.sim.addParticle(pid_particle_pair)

    def addShell(self, position, size):
        shell_id_shell_pair = (
            self.sim.main.shellIDGenerator(),
            Shell(position, size, self.domain_id) )
        self.sim.main.shellMatrix.update(shell_id_shell_pair)
        self.sim.shellMatrix.update(shell_id_shell_pair)

    def check( self ):
        self.sim.check()

        for shell_id_shell_pair in self.shell_list:
            try:
                self.sim.main.shellMatrix[shell_id_shell_pair[0]]
            except:
                raise RuntimeError,\
                    'self.sim.main.shellMatrix does not contain %s'\
                    % str(shell_id_shell_pair[0])

    def __repr__( self ):
        return 'Multi[%s: %s: eventID=%s]' % (
            self.domain_id,
            ', '.join( repr( p ) for p in self.sim.particleList ),
            self.eventID )

    def getShellList(self):
        return self.sim.shellMatrix
    shell_list = property(getShellList)


class EGFRDSimulator( ParticleSimulatorBase ):
    def __init__( self ):
        self.shellMatrix = None
        self.domainIDGenerator = DomainIDGenerator(0)
        self.shellIDGenerator = ShellIDGenerator(0)

        ParticleSimulatorBase.__init__( self )

        self.MULTI_SHELL_FACTOR = 0.05
        self.SINGLE_SHELL_FACTOR = 0.1

        self.isDirty = True
        self.scheduler = EventScheduler()

        self.smallT = 1e-8  # FIXME: is this ok?

        self.userMaxShellSize = numpy.inf

        self.domains = {}

        self.reset()

    def setWorldSize( self, size ):
        ParticleSimulatorBase.setWorldSize( self, size )
        self.shellContainer = ShellContainer( self.worldSize, self.matrixSize )

    def setMatrixSize( self, size ):
        ParticleSimulatorBase.setMatrixSize( self, size )
        self.shellContainer = ShellContainer( self.worldSize, self.matrixSize )

    def getMatrixCellSize( self ):
        return self.shellMatrix.cell_size

    def getNextTime( self ):
        if self.scheduler.getSize() == 0:
            return self.t

        return self.scheduler.getTopTime()

    def setUserMaxShellSize( self, size ):
        self.userMaxShellSize = size

    def getUserMaxShellSize( self ):
        return self.userMaxShellSize

    def getMaxShellSize( self ):
        return min( self.getMatrixCellSize() * .5 / SAFETY,
                    self.userMaxShellSize )

    def reset( self ):
        self.t = 0.0
        self.dt = 0.0
        self.stepCounter = 0
        self.single_steps = {EventType.ESCAPE:0, EventType.REACTION:0}
        self.pair_steps = {0:0,1:0,2:0,3:0}
        self.multi_steps = {EventType.ESCAPE:0, EventType.REACTION:0, 2:0}
        self.zeroSteps = 0
        self.rejectedMoves = 0
        self.reactionEvents = 0
        self.lastEvent = None
        self.lastReaction = None

        self.isDirty = True
        #self.initialize()

    def initialize( self ):
        ParticleSimulatorBase.initialize( self )

        self.scheduler.clear()
        self.shellMatrix = ShellContainer(self.worldSize, self.matrixSize)

        singles = []
        for pid_particle_pair in self.particleMatrix:
            singles.append(self.createSingle(pid_particle_pair))
        assert len(singles) == len(self.particleMatrix)
        for single in singles:
            self.addSingleEvent( single )

        self.isDirty = False

    def stop( self, t ):
        if __debug__:
            log.info( 'stop at %g' % t )

        if self.t == t:
            return

        if t >= self.scheduler.getTopEvent().getTime():
            raise RuntimeError, 'Stop time >= next event time.'

        if t < self.t:
            raise RuntimeError, 'Stop time < current time.'

        self.t = t
        print 'stop'
        scheduler = self.scheduler
        
        nonSingleList = []

        # first burst all Singles.
        for i in range( scheduler.getSize() ):
            obj = scheduler.getEventByIndex(i).getArg()
            if isinstance( obj, Pair ) or isinstance( obj, Multi ):
                nonSingleList.append( obj )
            elif isinstance( obj, Single ):
                if __debug__:
                    log.debug( 'burst %s, lastTime= %g' % 
                           ( str( obj ), obj.lastTime ) )
                self.burstSingle( obj )
            else:
                assert False, 'do not reach here'


        # then burst all Pairs and Multis.
        if __debug__:
            log.debug( 'burst %s' % nonSingleList )
        self.burstObjs( nonSingleList )

        self.dt = 0.0

    def step( self ):
        self.lastReaction = None

        if self.isDirty:
            self.initialize()
            
        if __debug__:
            if int("0" + os.environ.get("ECELL_CHECK", ""), 10):
                self.check()
        
        self.stepCounter += 1

        event = self.scheduler.getTopEvent()
        self.t, self.lastEvent = event.getTime(), event.getArg()

        if __debug__:
            domain_counts = self.count_domains()
            log.info( '\n%d: t=%g dt=%g\tSingles: %d, Pairs: %d, Multis: %d'
                      % (( self.stepCounter, self.t, self.dt ) + domain_counts ))
            log.info( 'event=%s reactions=%d rejectedmoves=%d' 
                      % ( self.lastEvent, self.reactionEvents, 
                          self.rejectedMoves ) )
        
        self.scheduler.step()

        nextTime = self.scheduler.getTopTime()
        self.dt = nextTime - self.t


        # assert if not too many successive dt=0 steps occur.
        if __debug__:
            if self.dt == 0:
                self.zeroSteps += 1
                if self.zeroSteps >= max( self.scheduler.getSize() * 3, 10 ):
                    raise RuntimeError, 'too many dt=zero steps.  simulator halted?'
            else:
                self.zeroSteps = 0


        assert self.scheduler.getSize() != 0

    def createSingle( self, pid_particle_pair ):
        rt = self.getReactionRule1(pid_particle_pair[1].sid)
        domain_id = self.domainIDGenerator()
        shell_id_shell_pair = (self.shellIDGenerator(),
                               Shell(pid_particle_pair[1].position,
                                     pid_particle_pair[1].radius,
                                     domain_id))
        single = Single(domain_id, pid_particle_pair, shell_id_shell_pair, rt)
        single.initialize(self.t)
        self.moveShell(shell_id_shell_pair)
        self.domains[domain_id] = single
        return single

    def determineSingleEvent(self, single, t, shellSize):
        a = shellSize - single.pid_particle_pair[1].radius
        escape_time = single.drawEscapeTime(a)
            
        reaction_time = single.drawReactionTime()

        if escape_time <= reaction_time:
            single.dt = escape_time
            single.eventType = EventType.ESCAPE
        else:
            single.dt = reaction_time
            single.eventType = EventType.REACTION

        single.lastTime = t

        if __debug__:
            log.info( "determineSingleEvent: type=%s, dt=%g" %\
                          ( single.eventType, single.dt ) )

    def createPair(self, single1, single2, shellSize):
        assert single1.dt == 0.0
        assert single2.dt == 0.0

        rt = self.getReactionRule2(single1.pid_particle_pair[1].sid, single2.pid_particle_pair[1].sid)[ 0 ]

        domain_id = self.domainIDGenerator()
        shell_id_shell_pair = (self.shellIDGenerator(),
                               Shell(calculate_pair_CoM(
                                        single1.pid_particle_pair[1].position,
                                        single2.pid_particle_pair[1].position,
                                        single1.pid_particle_pair[1].D,
                                        single2.pid_particle_pair[1].D,
                                        self.worldSize),
                                     shellSize,
                                     domain_id))
        pair = Pair( domain_id, single1, single2, shell_id_shell_pair, rt ) 
        pair.initialize( self.t )

        self.moveShell(shell_id_shell_pair)
        self.domains[domain_id] = pair
        return pair

    def determinePairEvent(self, pair, t, pos1, pos2, shellSize):
        pair.lastTime = t

        single1 = pair.single1
        single2 = pair.single2
        radius1 = single1.pid_particle_pair[1].radius
        radius2 = single2.pid_particle_pair[1].radius

        D1 = single1.pid_particle_pair[1].D
        D2 = single2.pid_particle_pair[1].D

        shellSize /= SAFETY  # FIXME:

        D_tot = D1 + D2
        D_geom = math.sqrt(D1 * D2)

        r0 = self.distance(pos1, pos2)

        assert r0 >= pair.sigma, \
            '%s;  r0 %g < sigma %g' % ( pair, r0, pair.sigma )

        # equalize expected mean t_r and t_R.
        if ((D_geom - D2) * r0) / D_tot + shellSize +\
                math.sqrt(D2 / D1) * (radius1 - shellSize) - radius2 >= 0:
            Da = D1
            Db = D2
            radiusa = radius1
            radiusb = radius2
        else:
            Da = D2
            Db = D1
            radiusa = radius2
            radiusb = radius1


        #aR
        pair.a_R = (D_geom * (Db * (shellSize - radiusa) + \
                               Da * (shellSize - r0 - radiusa))) /\
                               (Da * Da + Da * Db + D_geom * D_tot)

        #ar
        pair.a_r = (D_geom * r0 + D_tot * (shellSize - radiusa)) /\
            (Da + D_geom)

        assert pair.a_R + pair.a_r * Da / D_tot + radius1 >= \
            pair.a_R + pair.a_r * Db / D_tot + radius2

        assert abs( pair.a_R + pair.a_r * Da / D_tot + radiusa - shellSize ) \
            < 1e-12 * shellSize


        if __debug__:
          log.debug( 'a %g, r %g, R %g r0 %g' % 
                  ( shellSize, pair.a_r, pair.a_R, r0 ) )
        if __debug__:
          log.debug( 'tr %g, tR %g' % 
                     ( ( ( pair.a_r - r0 ) / math.sqrt(6 * pair.D_tot))**2,\
                           (pair.a_R / math.sqrt( 6*pair.D_R ))**2 ) )
        assert pair.a_r > 0
        assert pair.a_r > r0, '%g %g' % ( pair.a_r, r0 )
        assert pair.a_R > 0 or ( pair.a_R == 0 and ( D1 == 0 or D2 == 0 ) )

        sgf = FirstPassageGreensFunction(pair.D_R)
        sgf.seta(pair.a_R)


        # draw t_R
        try:
            pair.t_R = pair.drawTime_single( sgf )
        except Exception, e:
            raise Exception, 'sgf.drawTime() failed; %s; %s' %\
                ( str( e ), sgf.dump() )

        pgf = FirstPassagePairGreensFunction( pair.D_tot, 
                                              pair.rt.k, pair.sigma )
        pgf.seta( pair.a_r )

        # draw t_r
        try:
            pair.t_r = pair.drawTime_pair(pgf, r0)
        except Exception, e:
            raise Exception, \
                'pgf.drawTime() failed; %s; r0=%g, %s' % \
                ( str( e ), r0, pgf.dump() )


        # draw t_reaction
        t_reaction1 = pair.single1.drawReactionTime()
        t_reaction2 = pair.single2.drawReactionTime()

        if t_reaction1 < t_reaction2:
            pair.t_single_reaction = t_reaction1
            pair.reactingsingle = pair.single1
        else:
            pair.t_single_reaction = t_reaction2
            pair.reactingsingle = pair.single2

        pair.dt = min( pair.t_R, pair.t_r, pair.t_single_reaction )

        assert pair.dt >= 0
        if __debug__:
            log.debug( 'dt %g, t_R %g, t_r %g' % 
                     ( pair.dt, pair.t_R, pair.t_r ) )

        if pair.dt == pair.t_r:  # type = 0 (REACTION) or 1 (ESCAPE_r)
            try:
                pair.eventType = pair.drawEventType(pgf, r0, pair.t_r)
            except Exception, e:
                raise Exception,\
                    'pgf.drawEventType() failed; %s; r0=%g, %s' %\
                    ( str( e ), r0, pgf.dump() )

        elif pair.dt == pair.t_R: # type = ESCAPE_R (2)
            pair.eventType = 2
        elif pair.dt == pair.t_single_reaction:  # type = single reaction (3)
            pair.eventType = 3 
        else:
            raise AssertionError, "Never get here"

    def calculatePairPos(self, pair, CoM, newInterParticle, oldInterParticle):
        '''
        Calculate new positions of the particles in the Pair using
        a new center-of-mass, a new inter-particle vector, and
        an old inter-particle vector.
        '''
        #FIXME: need better handling of angles near zero and pi.

        # I rotate the new interparticle vector along the
        # rotation axis that is perpendicular to both the
        # z-axis and the original interparticle vector for
        # the angle between these.
        
        # the rotation axis is a normalized cross product of
        # the z-axis and the original vector.
        # rotationAxis = crossproduct( [ 0,0,1 ], interParticle )

        angle = vectorAngleAgainstZAxis(oldInterParticle)
        if angle % numpy.pi != 0.0:
            rotationAxis = crossproductAgainstZAxis(oldInterParticle)
            rotationAxis = normalize(rotationAxis)
            rotated = rotateVector(newInterParticle, rotationAxis, angle)
        elif angle == 0.0:
            rotated = newInterParticle
        else:
            rotated = numpy.array([newInterParticle[0], newInterParticle[1],
                                   - newInterParticle[2]])

        D1 = pair.single1.pid_particle_pair[1].D
        D2 = pair.single2.pid_particle_pair[1].D
        newpos1 = CoM - rotated * (D1 / (D1 + D2))
        newpos2 = CoM + rotated * (D2 / (D1 + D2))

        return newpos1, newpos2

    def createMulti( self ):
        domain_id = self.domainIDGenerator()
        multi = Multi( domain_id, self )
        self.domains[domain_id] = multi
        return multi

    def moveSingle(self, single, position, radius=None):
        if radius is None:
            radius = single.shell[1].radius
        new_sid_shell_pair = (single.shell[0],
                Shell(position, radius, single.domain_id))
        new_pid_particle_pair = (single.pid_particle_pair[0],
                          Particle(position,
                                   single.pid_particle_pair[1].radius,
                                   single.pid_particle_pair[1].D,
                                   single.pid_particle_pair[1].sid))
        single.shell = new_sid_shell_pair
        single.pid_particle_pair = new_pid_particle_pair
        self.moveShell(new_sid_shell_pair)
        self.moveParticle(new_pid_particle_pair)

    def removeDomain( self, obj ):
        del self.domains[obj.domain_id]
        for shell_id, _ in obj.shell_list:
            del self.shellMatrix[shell_id]
    
    def moveShell(self, shell_id_shell_pair):
        self.shellMatrix.update(shell_id_shell_pair)

    def addEvent( self, t, func, arg ):
        return self.scheduler.addEvent( t, func, arg )

    def addSingleEvent( self, single ):
        eventID = self.addEvent( self.t + single.dt, 
                                 Delegate( self, EGFRDSimulator.fireSingle ), 
                                 single )
        if __debug__:
            log.info( 'addSingleEvent: #%d (t=%g)' % (
                eventID, self.t + single.dt ) )
        single.eventID = eventID

    def addPairEvent( self, pair ):
        eventID = self.addEvent( self.t + pair.dt, 
                                 Delegate( self, EGFRDSimulator.firePair ), 
                                 pair )
        if __debug__:
            log.info( 'addPairEvent: #%d (t=%g)' % (
                eventID, self.t + pair.dt ) )
        pair.eventID = eventID

    def addMultiEvent( self, multi ):
        eventID = self.addEvent( self.t + multi.dt, 
                                 Delegate( self, EGFRDSimulator.fireMulti ), 
                                 multi )
        if __debug__:
            log.info( 'addMultiEvent: #%d (t=%g)' % (
                eventID, self.t + multi.dt ) )
        multi.eventID = eventID

    def removeEvent( self, event ):
        if __debug__:
            log.info( 'removeEvent: #%d' % event.eventID )
        self.scheduler.removeEvent( event.eventID )

    def updateEvent( self, t, event ):
        if __debug__:
            log.info( 'updateEvent: #%d (t=%g)' % ( event.eventID, t ) )
        self.scheduler.updateEventTime( event.eventID, t )

    def burstObj( self, obj ):
        if __debug__:
            log.info( 'burstObj: bursting %s' % obj )

        if isinstance( obj, Single ):
            self.burstSingle( obj )
            bursted = [obj,]
        elif isinstance( obj, Pair ):  # Pair
            single1, single2 = self.burstPair( obj )
            self.removeEvent( obj )
            self.addSingleEvent( single1 )
            self.addSingleEvent( single2 )
            bursted = [ single1, single2 ]
        else:  # Multi
            bursted = self.burstMulti( obj )
            self.removeEvent( obj )

        if __debug__:
            log.info( 'burstObj: bursted=%s' % bursted )

        return bursted

    def burstObjs( self, objs ):
        bursted = []
        for obj in objs:
            b = self.burstObj( obj )
            bursted.extend( b )

        return bursted

    def clearVolume( self, pos, radius, ignore=[] ):
        neighbors = self.getNeighborsWithinRadiusNoSort( pos, radius, ignore )
        return self.burstObjs( neighbors )

    def burstNonMultis( self, neighbors ):
        bursted = []

        for obj in neighbors:
            if not isinstance( obj, Multi ):
                b = self.burstObj( obj )
                bursted.extend( b )
            else:
                bursted.append( obj )

        return bursted

    def fireSingleReaction( self, single ):
        reactantSpeciesRadius = single.pid_particle_pair[1].radius
        oldpos = single.pid_particle_pair[1].position
        
        rt = single.drawReactionRule()

        if len( rt.products ) == 0:
            
            self.removeParticle(single.pid_particle_pair)

            self.lastReaction = Reaction( rt, [single.particle], [] )

            
        elif len( rt.products ) == 1:
            
            productSpecies = rt.products[0]

            if reactantSpeciesRadius < productSpecies.radius:
                self.clearVolume( oldpos, productSpecies.radius )

            if self.checkOverlap( oldpos, productSpecies.radius,
                                  ignore = [ single.pid_particle_pair[0], ] ):
                if __debug__:
                    log.info( 'no space for product particle.' )
                raise NoSpace()

            self.removeParticle(single.pid_particle_pair)
            newparticle = self.createParticle( productSpecies, oldpos )
            newsingle = self.createSingle( newparticle )
            self.addSingleEvent( newsingle )

            self.lastReaction = Reaction( rt, [single.particle], [newparticle] )

            if __debug__:
                log.info( 'product; %s' % str( newsingle ) )

            
        elif len( rt.products ) == 2:
            
            productSpecies1 = rt.products[0]
            productSpecies2 = rt.products[1]
            
            D1 = productSpecies1.D
            D2 = productSpecies2.D
            D12 = D1 + D2
            
            particleRadius1 = productSpecies1.radius
            particleRadius2 = productSpecies2.radius
            particleRadius12 = particleRadius1 + particleRadius2

            # clean up space.
            rad = max( particleRadius12 * ( D1 / D12 ) + particleRadius1,
                       particleRadius12 * ( D2 / D12 ) + particleRadius2 )

            self.clearVolume( oldpos, rad )

            for _ in range( 100 ):
                unitVector = randomUnitVector()
                vector = unitVector * particleRadius12 * ( 1.0 + 1e-7 )
            
                # place particles according to the ratio D1:D2
                # this way, species with D=0 doesn't move.
                # FIXME: what if D1 == D2 == 0?

                while 1:
                    newpos1 = oldpos + vector * ( D1 / D12 )
                    newpos2 = oldpos - vector * ( D2 / D12 )
                    newpos1 = self.applyBoundary( newpos1 )
                    newpos2 = self.applyBoundary( newpos2 )

                    if self.distance( newpos1, newpos2 ) >= particleRadius12:
                        break

                    vector *= 1.0 + 1e-7


                # accept the new positions if there is enough space.
                if (not self.checkOverlap(newpos1, particleRadius1,
                                          ignore=[single.pid_particle_pair[0]])) and \
                   (not self.checkOverlap(newpos2, particleRadius2,
                                          ignore=[single.pid_particle_pair[0]])):
                    break
            else:
                if __debug__:
                    log.info( 'no space for product particles.' )
                raise NoSpace()

            self.removeParticle(single.pid_particle_pair)

            particle1 = self.createParticle(productSpecies1.serial, newpos1)
            particle2 = self.createParticle(productSpecies2.serial, newpos2)
            newsingle1 = self.createSingle(particle1)
            newsingle2 = self.createSingle(particle2)

            self.addSingleEvent( newsingle1 )
            self.addSingleEvent( newsingle2 )

            self.lastReaction = Reaction( rt, [single.pid_particle_pair], 
                                          [particle1, particle2] )

            if __debug__:
                log.info( 'products; %s %s' % 
                      ( str( newsingle1 ), str( newsingle2 ) ) )

        else:
            raise RuntimeError, 'num products >= 3 not supported.'

        self.reactionEvents += 1

    def propagateSingle(self, single, r):
        if __debug__:
            log.debug( "single.dt=%g, single.lastTime=%g, self.t=%g" % (
                single.dt, single.lastTime, self.t ) )
        assert abs( single.dt + single.lastTime - self.t ) <= 1e-18 * self.t
        
        displacement = randomVector( r )

        assert abs( length( displacement ) - r ) <= 1e-15 * r
            
        newpos = single.pid_particle_pair[1].position + displacement
        newpos = self.applyBoundary( newpos )

        if __debug__:
            log.debug( "propagate %s: %s => %s" % ( single, single.pid_particle_pair[1].position, newpos ) )
        assert not self.checkOverlap(newpos,
                                     single.pid_particle_pair[1].radius,
                                     ignore=[single.pid_particle_pair[0]])

        single.initialize( self.t )

        self.moveSingle(single, newpos, single.pid_particle_pair[1].radius)

    def fireSingle( self, single ):

        self.single_steps[single.eventType] += 1

        if __debug__:
            log.info('fireSingle: eventType %s' % single.eventType)

        # Reaction.
        if single.eventType == EventType.REACTION:
            if __debug__:
                log.info( 'single reaction %s' % str( single ) )
            r = single.drawR( single.dt, single.shell[1].radius )

            self.propagateSingle( single, r )

            try:
                self.removeDomain( single )
                self.fireSingleReaction( single )
                return
            except NoSpace:
                if __debug__:
                    log.info( 'single reaction; placing product failed.' )
                self.shellMatrix.update( single.shell )
                self.rejectedMoves += 1
                single.reset()
                self.addSingleEvent(single)
                return

        # Propagate, if not reaction.

        # Handle immobile case first.
        if single.getD() == 0:
            # no propagation, just calculate next reaction time.
            self.determineSingleEvent(single, self.t, single.shell[1].radius) 
            self.addSingleEvent(single)
            return
        
        # Propagate this particle to the exit point on the shell.
        a = single.shell[1].radius - single.pid_particle_pair[1].radius
        self.propagateSingle(single, a)
        singlepos = single.shell[1].position

        # (2) Clear volume.

        minShell = single.pid_particle_pair[1].radius * ( 1.0 + self.SINGLE_SHELL_FACTOR )

        intruders = []   # intruders are domains within minShell
        closest = None   # closest is the closest domain, excluding intruders.
        closestDistance = numpy.inf # distance to the shell of the closet.
        
        neighbors = self.getNeighbors(singlepos)
        seen = set([single.domain_id,])
        for n in neighbors:
            did = n[0][1].did
            distance = n[1]
            if distance > minShell:
                closest = self.domains[did]
                closestDistance = distance
                break
            elif did not in seen:
                seen.add(did)
                intruders.append(self.domains[did])

        if __debug__:
            log.debug( "intruders: %s, closest: %s (dist=%g)" %\
                           (intruders, closest, closestDistance) )

        burst = []
        if intruders:
            burst = self.burstNonMultis(intruders)

            obj = self.formPairOrMulti(single, singlepos, burst)

            if obj:
                return

            # if nothing was formed, recheck closest and restore shells.
            closest, closestDistance = \
                self.getClosestObj( singlepos, ignore = [ single.domain_id, ] )

        self.updateSingle( single, closest, closestDistance )

        burst = uniq( burst )
        burstSingles = [ s for s in burst if isinstance( s, Single ) ]
        self.restoreSingleShells( burstSingles )
            
        if __debug__:
            log.info( 'single shell %s dt %g.' %\
                          ( single.shell, single.dt ) )

        self.addSingleEvent(single)
        return

    def restoreSingleShells( self, singles ):
        for single in singles:
            assert single.isReset()
            c, d = self.getClosestObj( single.shell[1].position, ignore = [single.domain_id,] )

            self.updateSingle( single, c, d )
            self.updateEvent( self.t + single.dt, single )
            if __debug__:
                log.debug( 'restore shell %s %g dt %g closest %s %g' %
                       ( single, single.shell[1].radius, single.dt, c, d ) )

    def calculateSingleShellSize( self, single, closest, 
                                  distance, shellDistance ):
        assert isinstance( closest, Single )

        minRadius1 = single.pid_particle_pair[1].radius
        D1 = single.getD()

        if D1 == 0:
            return minRadius1

        D2 = closest.getD()
        minRadius2 = closest.pid_particle_pair[1].radius
        minRadius12 = minRadius1 + minRadius2
        sqrtD1 = math.sqrt( D1 )
            
        shellSize = min( sqrtD1 / ( sqrtD1 + math.sqrt( D2 ) )
                         * ( distance - minRadius12 ) + minRadius1,
                         shellDistance / SAFETY )
        if shellSize < minRadius1:
            shellSize = minRadius1

        return shellSize

    def updateSingle( self, single, closest, distanceToShell ): 
        singlepos = single.shell[1].position
        if isinstance( closest, Single ):
            closestpos = closest.shell[1].position
            distanceToClosest = self.distance(singlepos, closestpos)
            new_shell_size = self.calculateSingleShellSize( single, closest, 
                                                       distanceToClosest,
                                                       distanceToShell )
        else:  # Pair or Multi
            new_shell_size = distanceToShell / SAFETY
            new_shell_size = max( new_shell_size, single.pid_particle_pair[1].radius )

        new_shell_size = min( new_shell_size, self.getMaxShellSize() )

        self.determineSingleEvent(single, self.t, new_shell_size)
        new_sid_shell_pair = (single.shell[0],
                              Shell(singlepos, new_shell_size, single.domain_id))
        single.shell = new_sid_shell_pair
        self.moveShell(new_sid_shell_pair)

    def firePair( self, pair ):
        self.pair_steps[pair.eventType] += 1

        if __debug__:
            log.info('firePair: eventType %s' % pair.eventType)

        assert self.checkObj( pair )

        particle1 = pair.single1.pid_particle_pair
        particle2 = pair.single2.pid_particle_pair
        
        oldInterParticle = particle2[1].position - particle1[1].position
        oldCoM = calculate_pair_CoM(
            particle1[1].position,
            particle2[1].position,
            particle1[1].D,
            particle2[1].D,
            self.worldSize)
        oldCoM = self.applyBoundary( oldCoM )

        # Four cases:
        #  0. Reaction
        #  1. Escaping through a_r.
        #  2. Escaping through a_R.
        #  3. Single reaction 

        # First handle single reaction case.
        if pair.eventType == 3:

            reactingsingle = pair.reactingsingle

            if __debug__:
                log.info( 'pair: single reaction %s' % str( reactingsingle ) )

            if reactingsingle == pair.single1:
                theothersingle = pair.single2
            else:
                theothersingle = pair.single1

            self.burstPair( pair )

            self.addSingleEvent( theothersingle )

            try:
                self.removeDomain( reactingsingle )
                self.fireSingleReaction( reactingsingle )
            except NoSpace:
                self.shellMatrix.update( reactingsingle.shell )
                self.rejectedMoves += 1
                reactingsingle.dt = 0
                self.addSingleEvent( reactingsingle )

            return
        


        #
        # 0. Reaction
        #
        if pair.eventType == EventType.REACTION:
            if __debug__:
                log.info( 'reaction' )

            if len( pair.rt.products ) == 1:
                
                species3 = pair.rt.products[0]

                # calculate new R
            
                sgf = FirstPassageGreensFunction(pair.D_R)
                sgf.seta(pair.a_R)

                r_R = pair.drawR_single( sgf, pair.dt )
            
                displacement_R_S = [ r_R, myrandom.uniform() * Pi,
                                     myrandom.uniform() * 2 * Pi ]
                displacement_R = sphericalToCartesian( displacement_R_S )
                newCoM = oldCoM + displacement_R
                
                if __debug__:
                    shellSize = pair.shell[1].radius
                    assert self.distance( oldCoM, newCoM ) + species3.radius <\
                        shellSize

                #FIXME: SURFACE
                newCoM = self.applyBoundary( newCoM )

                self.removeParticle(pair.single1.pid_particle_pair)
                self.removeParticle(pair.single2.pid_particle_pair)

                particle = self.createParticle( species3.serial, newCoM )
                newsingle = self.createSingle( particle )
                self.addSingleEvent( newsingle )

                self.reactionEvents += 1

                self.lastReaction = Reaction( pair.rt, [particle1, particle2],
                                              [particle] )

                if __debug__:
                    log.info( 'product; %s' % str( newsingle ) )

            else:
                raise NotImplementedError,\
                      'num products >= 2 not supported.'

            self.removeDomain( pair )

            return


        #
        # Escape 
        #

        r0 = self.distance( particle1[1].position, particle2[1].position )

        # 1 Escaping through a_r.
        if pair.eventType == EventType.ESCAPE:

            # calculate new R
            
            sgf = FirstPassageGreensFunction(pair.D_R)
            sgf.seta(pair.a_R)

            r_R = pair.drawR_single( sgf, pair.dt )
                
            displacement_R_S = [r_R, myrandom.uniform() * Pi, 
                                myrandom.uniform() * 2 * Pi]
            displacement_R = sphericalToCartesian( displacement_R_S )
            newCoM = oldCoM + displacement_R

            # calculate new r
            theta_r = pair.drawTheta_pair(myrandom.uniform(), pair.a_r, 
                                          r0, pair.dt, pair.a_r )
            phi_r = myrandom.uniform() * 2 * Pi
            newInterParticleS = numpy.array( [ pair.a_r, theta_r, phi_r ] )
            newInterParticle = sphericalToCartesian( newInterParticleS )
                
            newpos1, newpos2 = self.calculatePairPos(pair, newCoM,
                                                     newInterParticle,
                                                     oldInterParticle)
            newpos1 = self.applyBoundary( newpos1 )
            newpos2 = self.applyBoundary( newpos2 )


        # 2 escaping through a_R.
        elif pair.eventType == 2:

            # calculate new r
            r = pair.drawR_pair( r0, pair.dt, pair.a_r )
            if __debug__:
                log.debug( 'new r = %g' % r )
            #assert r >= pair.sigma
            
            theta_r = pair.drawTheta_pair(myrandom.uniform(), r, r0, pair.dt, 
                                          pair.a_r)
            phi_r = myrandom.uniform() * 2*Pi
            newInterParticleS = numpy.array( [ r, theta_r, phi_r ] )
            newInterParticle = sphericalToCartesian( newInterParticleS )
                
            # calculate new R
            displacement_R_S = [ pair.a_R, myrandom.uniform() * Pi, 
                                 myrandom.uniform() * 2 * Pi ]
            displacement_R = sphericalToCartesian( displacement_R_S )
            
            newCoM = oldCoM + displacement_R
                
            newpos1, newpos2 = self.calculatePairPos(pair, newCoM, 
                                                     newInterParticle,
                                                     oldInterParticle)
            newpos1 = self.applyBoundary( newpos1 )
            newpos2 = self.applyBoundary( newpos2 )

        else:
            raise SystemError, 'Bug: invalid eventType.'

        # this has to be done before the following clearVolume()

        assert self.checkPairPos(pair, newpos1, newpos2, oldCoM, pair.shell[1].radius)

        self.removeDomain( pair )

        assert not self.checkOverlap(newpos1, particle1[1].radius,
                                     ignore=[particle1[0], particle2[0]])
        assert not self.checkOverlap(newpos2, particle2[1].radius,
                                     ignore=[particle1[0], particle2[0]])

        single1, single2 = pair.single1, pair.single2

        single1.initialize(self.t)
        single2.initialize(self.t)

        if __debug__:
            log.debug("firePair: #1 { %s: %s => %s }" % (single1, particle1[1].position, newpos1))
            log.debug("firePair: #2 { %s: %s => %s }" % (single2, particle2[1].position, newpos2))

        self.domains[single1.domain_id] = single1
        self.domains[single2.domain_id] = single2

        self.moveSingle(single1, newpos1, single1.pid_particle_pair[1].radius)
        self.moveSingle(single2, newpos2, single2.pid_particle_pair[1].radius)
            
        self.addSingleEvent( single1 )
        self.addSingleEvent( single2 )

        assert self.checkObj( single1 )
        assert self.checkObj( single2 )

        return

    def fireMulti( self, multi ):
            
        sim = multi.sim

        self.multi_steps[2] += 1  # multi_steps[2]: total multi steps
        sim.step()

        if __debug__:
            event_type = ''
            if multi.sim.lastReaction:
                event_type = 'reaction'
            elif multi.sim.escaped:
                event_type = 'escaped'
            log.info('fireMulti: %s' % event_type)

        if sim.lastReaction:
            self.breakUpMulti( multi )
            self.reactionEvents += 1
            self.lastReaction = sim.lastReaction
            self.multi_steps[EventType.REACTION] += 1
            return

        if sim.escaped:
            self.breakUpMulti( multi )
            self.multi_steps[EventType.ESCAPE] += 1
            return

        self.addMultiEvent(multi)

        return

    def breakUpMulti( self, multi ):
        self.removeDomain( multi )

        singles = []
        for pid in multi.sim.particleList:
            single = self.createSingle((pid, multi.sim.particleMatrix[pid]))
            self.addSingleEvent( single )
            singles.append( single )

        return singles

    def burstMulti( self, multi ):
        #multi.sim.sync()
        assert isinstance(multi, Multi)
        singles = self.breakUpMulti( multi )

        return singles

    def burstSingle( self, single ):
        assert self.t >= single.lastTime
        assert self.t <= single.lastTime + single.dt

        dt = self.t - single.lastTime

        particleRadius = single.pid_particle_pair[1].radius

        oldpos, shellSize, _ = single.shell[1]
        r = single.drawR(dt, shellSize)
        displacement = randomVector( r )

        newpos = oldpos + displacement

        newpos = self.applyBoundary( newpos )

        assert self.distance( newpos, oldpos ) <=\
            single.shell[1].radius - single.pid_particle_pair[1].radius
        assert self.distance( newpos, oldpos ) - r <= r * 1e-6
        assert not self.checkOverlap(newpos, particleRadius,
                                     ignore=[single.pid_particle_pair[0]])

        single.initialize( self.t )

        self.moveSingle( single, newpos, particleRadius )

        self.updateEvent( self.t, single )

        assert single.shell[1].radius == particleRadius

    def burstPair( self, pair ):
        if __debug__:
            log.debug('burstPair: %s', pair)

        assert self.t >= pair.lastTime
        assert self.t <= pair.lastTime + pair.dt

        single1 = pair.single1
        single2 = pair.single2

        dt = self.t - pair.lastTime 

        particle1 = single1.pid_particle_pair
        particle2 = single2.pid_particle_pair

        if dt > 0.0:

            pos1 = particle1[1].position
            pos2 = particle2[1].position
            D1 = particle1[1].D
            D2 = particle2[1].D

            oldInterParticle = pos2 - pos1
            oldCoM = calculate_pair_CoM(pos1, pos2, D1, D2, self.worldSize)
            r0 = self.distance(pos1, pos2)
            
            sgf = FirstPassageGreensFunction(pair.D_R)
            sgf.seta(pair.a_R)

            # calculate new CoM
            r_R = pair.drawR_single( sgf, dt )
            
            displacement_R_S = [r_R, myrandom.uniform() * Pi, 
                                 myrandom.uniform() * 2 * Pi]
            displacement_R = sphericalToCartesian( displacement_R_S )
            newCoM = oldCoM + displacement_R
            
            # calculate new interparticle
            r_r = pair.drawR_pair( r0, dt, pair.a_r )
            print r_r
            theta_r = pair.drawTheta_pair(myrandom.uniform(), r_r, r0, dt, 
                                          pair.a_r)
            phi_r = myrandom.uniform() * 2 * Pi
            newInterParticleS = numpy.array( [ r_r, theta_r, phi_r ] )
            newInterParticle = sphericalToCartesian( newInterParticleS )
            newpos1, newpos2 = self.calculatePairPos(pair, newCoM, 
                                                     newInterParticle,
                                                     oldInterParticle)

            newpos1 = self.applyBoundary(newpos1)
            newpos2 = self.applyBoundary(newpos2)
            assert not self.checkOverlap(newpos1, particle1[1].radius,
                                         ignore=[particle1[0], particle2[0]])
            assert not self.checkOverlap(newpos2, particle2[1].radius,
                                         ignore=[particle1[0], particle2[0]])
            assert self.checkPairPos(pair, newpos1, newpos2, oldCoM,\
                                         pair.shell[1].radius)

        single1.initialize( self.t )
        single2.initialize( self.t )
        
        self.removeDomain( pair )
        assert single1.domain_id not in self.domains
        assert single2.domain_id not in self.domains
        self.domains[single1.domain_id] = single1
        self.domains[single2.domain_id] = single2
        self.moveSingle(single1, newpos1, particle1[1].radius)
        self.moveSingle(single2, newpos2, particle2[1].radius)

        assert self.shellMatrix[single1.shell[0]].radius == single1.shell[1].radius
        assert self.shellMatrix[single2.shell[0]].radius == single2.shell[1].radius
        assert single1.shell[1].radius == particle1[1].radius
        assert single2.shell[1].radius == particle2[1].radius

        return single1, single2

    def formPairOrMulti( self, single, singlepos, neighbors ):
        assert neighbors

        # sort burst neighbors by distance
        dists = self.objDistanceArray(singlepos, neighbors)
        if len(dists) >= 2:
            n = dists.argsort()
            dists = dists.take(n)
            neighbors = numpy.take(neighbors, n)

        # First, try forming a Pair.
        if isinstance(neighbors[0], Single):
            obj = self.formPair(single, singlepos, neighbors[0], neighbors[1:])
            if obj:
                return obj

        # If a Pair is not formed, then try forming a Multi.
        obj = self.formMulti(single, neighbors, dists)
        if obj:
            return obj


    def formPair( self, single1, pos1, single2, burst ):
        if __debug__:
           log.debug( 'trying to form %s' %
                  'Pair( %s, %s )' % ( single1.pid_particle_pair, 
                                       single2.pid_particle_pair ) )

        assert single1.isReset()
        assert single2.isReset()

        radius1 = single1.pid_particle_pair[1].radius
        radius2 = single2.pid_particle_pair[1].radius

        sigma = radius1 + radius2

        D1, D2 = single1.pid_particle_pair[1].D, single2.pid_particle_pair[1].D
        D12 = D1 + D2

        assert (pos1 - single1.shell[1].position).sum() == 0
        pos2 = single2.shell[1].position
        pairDistance = self.distance(pos1, pos2)
        r0 = pairDistance - sigma
        assert r0 >= 0, 'r0 (pair gap) between %s and %s = %g < 0' \
            % ( single1, single2, r0 )

        shellSize1 = pairDistance * D1 / D12 + radius1
        shellSize2 = pairDistance * D2 / D12 + radius2
        shellSizeMargin1 = radius1 * 2 #* self.SINGLE_SHELL_FACTOR
        shellSizeMargin2 = radius2 * 2 #* self.SINGLE_SHELL_FACTOR
        shellSizeWithMargin1 = shellSize1 + shellSizeMargin1
        shellSizeWithMargin2 = shellSize2 + shellSizeMargin2
        if shellSizeWithMargin1  >= shellSizeWithMargin2:
            minShellSize = shellSize1
            shellSizeMargin = shellSizeMargin1
        else:
            minShellSize = shellSize2
            shellSizeMargin = shellSizeMargin2

        # 1. Shell cannot be larger than max shell size or sim cell size.
        com = calculate_pair_CoM( pos1, pos2, D1, D2, self.getWorldSize() )
        com = self.applyBoundary( com )
        minShellSizeWithMargin = minShellSize + shellSizeMargin
        maxShellSize = min( self.getMaxShellSize(),
                            r0 * 100 + sigma + shellSizeMargin )

        if minShellSizeWithMargin >= maxShellSize:
            if __debug__:
                log.debug( '%s not formed: minShellSize >= maxShellSize' %
                       ( 'Pair( %s, %s )' % ( single1.pid_particle_pair[0], 
                                              single2.pid_particle_pair[0] ) ) )
            return None

        # Here, we have to take into account of the burst Singles in
        # this step.  The simple check for closest below could miss
        # some of them, because sizes of these Singles for this
        # distance check has to include SINGLE_SHELL_FACTOR, while
        # these burst objects have zero mobility radii.  This is not
        # beautiful, a cleaner framework may be possible.

        closest, closestShellDistance = None, numpy.inf
        for b in burst:
            if isinstance( b, Single ):
                bpos = b.shell[1].position
                d = self.distance( com, bpos ) \
                    - b.pid_particle_pair[1].radius * ( 1.0 + self.SINGLE_SHELL_FACTOR )
                if d < closestShellDistance:
                    closest, closestShellDistance = b, d

        if closestShellDistance <= minShellSizeWithMargin:
            if __debug__:
                log.debug( '%s not formed: squeezed by burst neighbor %s' %
                       ( 'Pair( %s, %s )' % ( single1.pid_particle_pair[0], 
                                              single2.pid_particle_pair[0]),
                         closest ) )
            return None

        assert closestShellDistance > 0
        c, d = self.getClosestObj( com, ignore=[ single1.domain_id, single2.domain_id ] )
        if d < closestShellDistance:
            closest, closestShellDistance = c, d

        if __debug__:
            log.debug( 'Pair closest neighbor: %s %g, minShellWithMargin %g' %
                   ( closest, closestShellDistance, minShellSizeWithMargin ) )

        assert closestShellDistance > 0

        if isinstance( closest, Single ):

            D_closest = closest.pid_particle_pair[1].D
            D_tot = D_closest + D12
            closestDistance = self.distance( com, closest.pid_particle_pair[1].position ) ##??

            closestMinRadius = closest.pid_particle_pair[1].radius
            closestMinShell = closestMinRadius * \
                ( self.SINGLE_SHELL_FACTOR + 1.0 )

            shellSize = min( ( D12 / D_tot ) *
                             ( closestDistance - minShellSize 
                               - closestMinRadius ) + minShellSize,
                             closestDistance - closestMinShell,
                             closestShellDistance )

            shellSize /= SAFETY
            assert shellSize < closestShellDistance

        else:
            assert isinstance( closest, ( Pair, Multi, None.__class__ ) )

            shellSize = closestShellDistance / SAFETY

        if shellSize <= minShellSizeWithMargin:
            if __debug__:
                log.debug( '%s not formed: squeezed by %s' %
                       ( 'Pair( %s, %s )' % ( single1.pid_particle_pair[0], 
                                              single2.pid_particle_pair[0]),
                         closest ) )
            return None


        d1 = self.distance(com, pos1)
        d2 = self.distance(com, pos2)

        if shellSize < max( d1 + single1.pid_particle_pair[1].radius *
                            ( 1.0 + self.SINGLE_SHELL_FACTOR ), \
                                d2 + single2.pid_particle_pair[1].radius * \
                                ( 1.0 + self.SINGLE_SHELL_FACTOR ) ) * 1.3:
            if __debug__:
                log.debug( '%s not formed: singles are better' %
                       'Pair( %s, %s )' % ( single1.pid_particle_pair[0], 
                                            single2.pid_particle_pair[0] ) )
            return None

        # 3. Ok, Pair makes sense.  Create one.
        shellSize = min( shellSize, maxShellSize )

        pair = self.createPair(single1, single2, shellSize)

        self.determinePairEvent(pair, self.t, pos1, pos2, shellSize)

        self.removeDomain( single1 )
        self.removeDomain( single2 )

        self.addPairEvent( pair )
        # single1 will be removed by the scheduler.
        self.removeEvent( single2 )

        assert closestShellDistance == numpy.inf or shellSize < closestShellDistance
        assert shellSize >= minShellSizeWithMargin
        assert shellSize <= maxShellSize

        if __debug__:
            log.info( '%s, dt=%g, pairDistance=%g, shell=%g,' %
                  ( pair, pair.dt, pairDistance, shellSize ) + 
                  'closest=%s, closestShellDistance=%g' %
                  ( closest, closestShellDistance ) )

        assert self.checkObj( pair )

        return pair
    

    def formMulti(self, single, neighbors, dists):

        minShell = single.pid_particle_pair[1].radius * ( 1.0 + self.MULTI_SHELL_FACTOR )
        if dists[0] > minShell:
            return None

        neighbors = [neighbors[i] for i in (dists <= minShell).nonzero()[0]]

        closest = neighbors[0]

        # if the closest to this Single is a Single, create a new Multi
        if isinstance( closest, Single ):

            multi = self.createMulti()
            self.addToMulti( single, multi )
            self.removeDomain( single )
            for neighbor in neighbors:
                self.addToMultiRecursive( neighbor, multi )

            multi.initialize( self.t )
            
            self.addMultiEvent( multi )

            return multi

        # if the closest to this Single is a Multi, reuse the Multi.
        elif isinstance( closest, Multi ):

            multi = closest
            if __debug__:
                log.info( 'multi merge %s %s' % ( single, multi ) )

            self.addToMulti( single, multi )
            self.removeDomain( single )
            for neighbor in neighbors[1:]:
                self.addToMultiRecursive( neighbor, multi )

            multi.initialize( self.t )

            self.updateEvent( self.t + multi.dt, multi )

            return multi


        assert False, 'do not reach here'


    def addToMultiRecursive( self, obj, multi ):
        if isinstance( obj, Single ):
            if obj.pid_particle_pair[0] in multi.sim.particleList:  # Already in the Multi.
                return
            assert obj.isReset()
            objpos = obj.shell[1].position
            
            self.addToMulti( obj, multi )
            self.removeDomain( obj )
            self.removeEvent( obj )

            radius = obj.pid_particle_pair[1].radius *\
                ( 1.0 + self.MULTI_SHELL_FACTOR )
            neighbors = self.getNeighborsWithinRadiusNoSort( objpos, radius,
                                                             ignore=[obj.domain_id] )

            burst = self.burstNonMultis( neighbors )
            neighborDists = self.objDistanceArray( objpos, burst )
            neighbors = [ burst[i] for i in 
                          ( neighborDists <= radius ).nonzero()[0] ]

            for obj in neighbors:
                self.addToMultiRecursive( obj, multi )

        elif isinstance( obj, Multi ):
            if obj.sim.particleList.isdisjoint(multi.sim.particleList):
                self.mergeMultis(obj, multi)
                self.removeDomain(obj)
                self.removeEvent(obj)
            else:
                if __debug__:
                    log.debug( '%s already added. skipping.' % obj )
        else:
            assert False, 'do not reach here.'  # Pairs are burst

    def addToMulti( self, single, multi ):
        if __debug__:
            log.info( 'adding %s to %s' % ( single, multi ) )
        shellSize = single.pid_particle_pair[1].radius * \
            ( 1.0 + self.MULTI_SHELL_FACTOR )
        multi.addParticle(single.pid_particle_pair)
        multi.addShell(single.pid_particle_pair[1].position, shellSize)

    def mergeMultis( self, multi1, multi2 ):
        '''
        merge multi1 into multi2
        '''
        if __debug__:
            log.info( 'merging %s to %s' % ( multi1, multi2 ) )

        assert not multi1.sim.particleList[0] in multi2.sim.particleList

        for pid in multi1.sim.particleList:
            # FIXME: shells should be renewed
            multi2.addParticle(multi1.sim.particleMatrix[pid])

        for shell in multi1.shell_list:
            multi2.addShell(shell[1].position, shell[1].radius)

    def getNeighborsWithinRadiusNoSort( self, pos, radius, ignore=[] ):
        '''
        Get neighbor domains within given radius.

        ignore: domain ids.
        '''

        result = self.shellMatrix.get_neighbors_within_radius(pos, radius)
        return [self.domains[did] for did in uniq(s[0][1].did for s in result) if did not in ignore]

    def getNeighbors(self, pos):
        return self.shellMatrix.get_neighbors_cyclic(pos)

    def getNeighborsWithinRadius( self, pos, radius=numpy.inf, ignore=[] ):
        '''
        ignore: domain ids
        '''
        result = self.shellMatrix.get_neighbors_within_radius(pos, radius)

        seen = set(ignore)
        neighbors = []
        distances = []

        for item in result:
            did = item[0][1].did
            if not did in seen:
                seen.add(did)
                neighbors.append(self.domains[did])
                distances.append(item[1])
        return neighbors, distances

    def getClosestObj( self, pos, ignore=[] ):
        '''
        ignore: domain ids.
        '''

        result = self.shellMatrix.get_neighbors_cyclic(pos)

        for item in result:
            if item[0][1].did not in ignore:
                return self.domains[item[0][1].did], item[1]

        return None, numpy.inf

    def objDistance( self, pos, obj ):
        dists = numpy.zeros( len( obj.shell_list ) )
        for i, shell_id_shell_pair in enumerate(obj.shell_list):
            dists[i] = self.distance( pos, shell_id_shell_pair[1].position ) - shell_id_shell_pair[1].radius
        return min( dists )

    def objDistanceArray( self, pos, objs ):
        dists = numpy.array( [ self.objDistance( pos, obj ) for obj in objs ] )
        return dists
            

    #
    # statistics reporter
    #

    def print_report(self, out=None):
        report = '''
t = %g
steps = %d 
\tSingle:\t%d\t(escape: %d, reaction: %d)
\tPair:\t%d\t(escape r: %d, R: %d, reaction pair: %d, single: %d)
\tMulti:\t%d\t(escape: %d, reaction: %d)
total reactions = %d
rejected moves = %d
'''\
            % (self.t, self.stepCounter,
               numpy.array(self.single_steps.values()).sum(),
               self.single_steps[EventType.ESCAPE],
               self.single_steps[EventType.REACTION],
               numpy.array(self.pair_steps.values()).sum(),
               self.pair_steps[1],
               self.pair_steps[2],
               self.pair_steps[0],
               self.pair_steps[3],
               self.multi_steps[2], # total multi steps
               self.multi_steps[EventType.ESCAPE],
               self.multi_steps[EventType.REACTION],
               self.reactionEvents,
               self.rejectedMoves
               )

        print >> out, report

    #
    # consistency checkers
    #

    def checkObj( self, obj ):
        obj.check()

        for shell_id, shell in obj.shell_list:
            closest, distance = self.getClosestObj( shell.position,
                                                    ignore = [obj.domain_id] )

            assert shell.radius <= self.getUserMaxShellSize(),\
                '%s shell size larger than user-set max shell size' % \
                str( shell_id )

            assert shell.radius <= self.getMaxShellSize(),\
                '%s shell size larger than simulator cell size / 2' % \
                str( shell_id )

            assert distance - shell.radius >= 0.0,\
                '%s overlaps with %s. (shell: %g, dist: %g, diff: %g.' \
                % ( str( obj ), str( closest ), shell.radius, distance,\
                        distance - shell.radius )

        return True

    def checkObjForAll( self ):
        for i in range( self.scheduler.getSize() ):
            obj = self.scheduler.getEventByIndex(i).getArg()
            self.checkObj( obj )

    def checkEventStoichiometry( self ):
        population = 0
        for pool in self.particlePool.itervalues():
            population += len(pool)

        eventPopulation = 0
        for i in range( self.scheduler.getSize() ):
            obj = self.scheduler.getEventByIndex(i).getArg()
            eventPopulation += obj.multiplicity

        if population != eventPopulation:
            raise RuntimeError, 'population %d != eventPopulation %d' %\
                  ( population, eventPopulation )

    def checkShellMatrix( self ):
        if self.worldSize != self.shellMatrix.world_size:
            raise RuntimeError,\
                'self.worldSize != self.shellMatrix.worldSize'

        shellPopulation = 0
        for i in range( self.scheduler.getSize() ):
            obj = self.scheduler.getEventByIndex(i).getArg()
            shellPopulation += len(obj.shell_list)

        if shellPopulation != len(self.shellMatrix):
            raise RuntimeError,\
                'num shells (%d) != self.shellMatrix.size (%d)' % (shellPopulation, len(self.shellMatrix))
        
        self.shellMatrix.check()

    def check_domains(self):
        domains = set(self.domains.itervalues())
        for i in range(self.scheduler.getSize()):
            obj = self.scheduler.getEventByIndex(i).getArg()
            if obj not in domains:
                raise RuntimeError,\
                    '%s in EventScheduler not in self.domains' % obj
            domains.remove(obj)

        # self.domains always include a None  --> this can change in future
        if len(domains):
            raise RuntimeError,\
                'following domains in self.domains not in Event Scheduler: %s' \
                % str(tuple(domains))

    def checkPairPos( self, pair, pos1, pos2, com, radius ):
        particle1 = pair.single1.pid_particle_pair[1]
        particle2 = pair.single2.pid_particle_pair[1]

        oldCoM = com
        
        # debug: check if the new positions are valid:
        newDistance = distance_Simple( pos1, pos2 )
        particleRadius12 = particle1.radius + particle2.radius

        # check 1: particles don't overlap.
        if newDistance <= particleRadius12:
            if __debug__:
                log.info( 'rejected move: radii %g, particle distance %g',
                          ( particle1.radius + particle2.radius, newDistance ) )
            if __debug__:
                log.debug( 'DEBUG: pair.dt %g, pos1 %s, pos2 %s' %
                           ( pair.dt, str( pos1 ), str( pos2 ) ) )
            raise RuntimeError, 'New particles overlap'

        # check 2: particles within mobility radius.
        d1 = self.distance( oldCoM, pos1 ) + particle1.radius
        d2 = self.distance( oldCoM, pos2 ) + particle2.radius
        if d1 > radius or d2 > radius:
            raise RuntimeError, \
                'New particle(s) out of protective sphere. %s' % \
                'radius = %g, d1 = %g, d2 = %g ' % ( radius, d1, d2 )
                
        

        return True




    def check( self ):
        ParticleSimulatorBase.check( self )

        assert self.scheduler.check()

        assert self.t >= 0.0
        assert self.dt >= 0.0

        self.checkShellMatrix()
        self.check_domains()
        self.checkEventStoichiometry()
        
        self.checkObjForAll()

    #
    # methods for debugging.
    #

    def dumpScheduler( self ):
        scheduler = self.scheduler
        for i in range( scheduler.getSize() ):
            event = scheduler.getEventByIndex(i)
            print i, event.getTime(), event.getArg()

    def dump( self ):
        scheduler = self.scheduler
        for i in range( scheduler.getSize() ):
            event = scheduler.getEventByIndex(i)
            print i, event.getTime(), event.getArg(), event.getArg().pos

    def count_domains(self):
        '''
        Returns a tuple (# Singles, # Pairs, # Multis).
        '''

        numSingles = 0
        numPairs = 0
        numMultis = 0
        for d in self.domains.itervalues():
            if isinstance(d, Single):
                numSingles += 1
            elif isinstance(d, Pair):
                numPairs += 1
            elif isinstance(d, Multi):
                numMultis += 1
            else:
                raise RuntimeError, 'NO NOT GET HERE'

        return (numSingles, numPairs, numMultis)
