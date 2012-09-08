#!/usr/bin/env python

from test_model import *
from egfrd import *
from gillespie import *
import numpy

'''
To run this script:
PYTHONPATH=../../ python test.py

or, without terminal output and faster:
PYTHONPATH=../../ python -O test.py
'''


def run(SIMULATOR):
    # Number of particles.
    N_A = 300

    # For equilibrium, there should be 3 times less B than A particles.
    N_B = N_A / 3


    '''Define world.

    '''
    if SIMULATOR == 'EGFRD':
        matrix_size = int(((N_A + N_B) * 6) ** (1. / 3.))
        world = create_world(m, matrix_size)
        print 'matrix_size =', matrix_size


    '''Define simulator.

    A cube of dimension (L x L x L) is created, with periodic boundary 
    conditions.

    '''
    if SIMULATOR == 'EGFRD':
        simulator = EGFRDSimulator(world)
    else:
        simulator = GillespieSimulator(m)


    '''Toggles.

    '''
    LOGGER = None
    VTK_LOGGER = None

    #LOGGER = True
    #VTK_LOGGER = True


    '''Settings.

    '''
    # Random number generator seed.
    SEED = 0
    myrandom.seed(SEED)

    # Make multis run 'BD_DT_FACTOR' times faster than normal.
    BD_DT_FACTOR = 1
    simulator.bd_dt_factor = BD_DT_FACTOR

    print 'N_A =', N_A
    print 'N_B =', N_B


    '''Add particles to world.

    '''
    if SIMULATOR == 'EGFRD':
        throw_in_particles(simulator.world, A, N_A)
        throw_in_particles(simulator.world, B, N_B)
    else:
        simulator.throw_in_particles(A, N_A)
        simulator.throw_in_particles(B, N_B)


    '''Define loggers.

    '''
    if VTK_LOGGER == True:
        from vtklogger import VTKLogger
        # Write vtk files. See vtklogger.py. Use VTK or Paraview to 
        # visualize.  
        vtklogger = VTKLogger(simulator, 'data/run', extra_particle_step=True, 
                              buffer_size=20)

    if LOGGER == True:
        from logger import Logger
        # Write log files. See logger.py. Use visualizer.py to visualize.
        l = Logger('example')
        l.start(simulator)
        #l.set_particle_out_interval(1e-4) #1e-3)

    '''Test dumper.

    '''
    if SIMULATOR == 'EGFRD':
        get_species(simulator)
        print '\nspecies:', dump_species(simulator)
        get_species_names(simulator)
        print '\nspecies names:', dump_species_names(simulator)

        get_particles(simulator)
        dump_particles(simulator)
        get_particles(simulator, A)
        dump_particles(simulator, A)

        get_number_of_particles(simulator)
        print '\nnumber of particles:', dump_number_of_particles(simulator)
        get_number_of_particles(simulator, A)
        print '\nnumber of A particles:', dump_number_of_particles(simulator, A)

        get_domains(simulator)
        dump_domains(simulator)


    '''Run  simulation.

    '''
    averagea = get_number_of_particles(simulator, A)
    averageb = get_number_of_particles(simulator, B) 

    time_lastreaction = 0
    dt = 1.e-3
    nextt = dt

    i = 0
    while simulator.t < 1e-2:
        if simulator.last_reaction != None: 
            na = get_number_of_particles(simulator, A)
            nb = get_number_of_particles(simulator, B)

            time_since_last_reaction = simulator.t - time_lastreaction

            averagea = (averagea * time_lastreaction +
                        na * time_since_last_reaction) / simulator.t

            averageb = (averageb * time_lastreaction +
                        nb * time_since_last_reaction) / simulator.t

            time_lastreaction = simulator.t

        if simulator.t > nextt:
            nextt += dt

            print '%.3f: %.1f %.1f' % (simulator.t, averagea, averageb)

        try:
            if VTK_LOGGER == True:
                vtklogger.log()
            if LOGGER == True and simulator.last_reaction:
                l.log(simulator, simulator.t)
            simulator.step()
        except Exception, message:
            print 'Exception at step = ', i
            print message
            if VTK_LOGGER == True:
                vtklogger.stop()
            simulator.print_report()
            raise

        i += 1

    if VTK_LOGGER == True:
        vtklogger.stop()

    simulator.stop(simulator.t)

    print '%.3f: %.1f %.1f' % (simulator.t, averagea, averageb)

    print dump_number_of_particles(simulator)

    print 'time end = ', simulator.t
    print 'time left = ', simulator.t - time_lastreaction

    simulator.print_report()


'''Turn this module into a unit test case.

'''
import unittest
class TestTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_egfrd_test(self):
        print '############# Start EGFRD #############'
        run('EGFRD')

    def test_gillespie_test(self):
        print '############# Start Gillespie #############'
        run('Gillespie')


if __name__ == "__main__":
    unittest.main()
