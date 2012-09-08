from model import *
from utils import *
from dumper import *


'''Create model.

'''
# Size of simulation cube in meters.
L = 1.e-6
m = ParticleModel(L)


'''Toggles.

'''
WORLD = None
BOX = None
PLANE1 = None
PLANE2 = None
CYLINDER = None

WORLD = True
#BOX = True
#PLANE1 = True
#PLANE2 = True
#CYLINDER = True


'''Settings.

'''
# Radii in meters.
RADIUS_CYLINDER = 2.5e-9
RADIUS_A = 5.0e-9
RADIUS_B = RADIUS_A #7.5e-9

# Diffusion constants in meters^2 / second
D_A = 1.0e-12 # 1.5e-12
D_B = D_A #1.0e-12

D_A_PLANE = D_A / 2
D_B_PLANE = D_B / 2

D_A_CYLINDER = D_A / 2
D_B_CYLINDER = D_B / 2

# Bimolecular reaction rates in 'meters^3 per second'.
kon = 1e-19

# Unimolecular reaction rates in 'per second'.
# For equilibrium, koff should be 7/4 * kon * [A].
koff = 61.25

# Diffusion limited rate.
kD = k_D(2 * D_A, 2 * RADIUS_A) 

# Intrinsic reaction rates.
kd = k_d(koff, kon, kD)
ka = k_a(kon, kD)

# TODO
# THESE RATES ARE NONSENSE. ALL REACTION RULES SHOULD HAVE A BACK 
# REACTION BECAUSE OF DETAILED BALANCE.


# Todo.
#kdP
#kaP
#kdC
#kaC


'''Add Regions and Surfaces. 

'''
if BOX:
    box = create_box_shaped_region('box', [0, 0, 2 * L / 10], [L, L, 6 * L / 10])
    m.add_structure(box)

if PLANE1:
    plane1 = create_planar_surface('plane1', [0, 0, 2 * L / 10],
                                   [1, 0, 0], [0, 1, 0], L, L)
    m.add_structure(plane1)

if PLANE2:
    plane2 = create_planar_surface('plane2', [0, 0, 8 * L / 10],
                                   [1, 0, 0], [0, 1, 0], L, L)
    m.add_structure(plane2)

if CYLINDER:
    cylinder = create_cylindrical_surface('cylinder', [0, 0, L / 2],
                                          RADIUS_CYLINDER, [0, 1, 0], L)
    m.add_structure(cylinder)


'''Define and add ParticleTypes (to specific Regions or Surfaces).

'''
if WORLD:
    A = Species('A', D_A, RADIUS_A)
    B = Species('B', D_B, RADIUS_B)
    m.add_species_type(A)
    m.add_species_type(B)

if BOX:
    Ab = Species('Ab', D_A, RADIUS_A, box.id)
    Bb = Species('Bb', D_B, RADIUS_B, box.id)
    m.add_species_type(Ab)
    m.add_species_type(Bb)

if PLANE1:
    Ap1 = Species('Ap1', D_A_PLANE, RADIUS_A, plane1.id)
    Bp1 = Species('Ap1', D_B_PLANE, RADIUS_B, plane1.id)
    m.add_species_type(Ap1)
    m.add_species_type(Bp1)

if PLANE2:
    pass

if CYLINDER:
    Ac = Species('Ac', D_A_CYLINDER, RADIUS_A, cylinder.id)
    Bc = Species('Ac', D_B_CYLINDER, RADIUS_B, cylinder.id)
    m.add_species_type(Ac)
    m.add_species_type(Bc)


'''Add reaction rules.

A     -> A + A
B     -> A 
B     -> 0
A + A -> B
A + A -> 0

'''
if WORLD:
    r1 = create_unbinding_reaction_rule(A, A, A, kd)
    r2 = create_unimolecular_reaction_rule(B, A, kd)
    r3 = create_decay_reaction_rule(B, kd)
    r4 = create_binding_reaction_rule(A, A, B, ka)
    r5 = create_annihilation_reaction_rule(A, A, ka)
    for rr in [r1, r2, r3, r4, r5]:
        m.network_rules.add_reaction_rule(rr)

if BOX:
    r1 = create_unbinding_reaction_rule(Ab, Ab, Ab, kd)
    r2 = create_unimolecular_reaction_rule(Bb, Ab, koff)
    r3 = create_decay_reaction_rule(Bb, koff)
    r4 = create_binding_reaction_rule(Ab, Ab, Bb, ka)
    r5 = create_annihilation_reaction_rule(Ab, Ab, ka)
    for rr in [r1, r2, r3, r4, r5]:
        m.network_rules.add_reaction_rule(rr)

if PLANE1:
    r1 = create_unbinding_reaction_rule(Ap1, Ap1, Ap1, kd)
    r2 = create_unimolecular_reaction_rule(Bp1, Ap1, koff)
    r3 = create_decay_reaction_rule(Bp1, koff)
    r4 = create_binding_reaction_rule(Ap1, Ap1, Bp1, ka)
    r5 = create_annihilation_reaction_rule(Ap1, Ap1, ka)
    for rr in [r1, r2, r3, r4, r5]:
        m.network_rules.add_reaction_rule(rr)

if PLANE2:
    pass

if CYLINDER:
    r1 = create_unbinding_reaction_rule(Ac, Ac, Ac, kd)
    r2 = create_unimolecular_reaction_rule(Bc, Ac, koff)
    r3 = create_decay_reaction_rule(Bc, koff)
    r4 = create_binding_reaction_rule(Ac, Ac, Bc, ka)
    r5 = create_annihilation_reaction_rule(Ac, Ac, ka)
    for rr in [r1, r2, r3, r4, r5]:
        m.network_rules.add_reaction_rule(rr)


'''Output

'''
print 'L = ', L
print 'koff = ', koff
print 'kon = ', kon
print 'kD = ', kD
print 'kd = ', kd
print 'ka = ', ka
print 'kon / koff = ', kon / koff
print 'ka / kd = ', ka / kd
m.set_all_repulsive()
print dump_reaction_rules(m)

