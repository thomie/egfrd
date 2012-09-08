from simple_model import *


'''Create model.

'''
# Size of simulation cube in meters.
L = 1e-6
model = SimpleModel(L)


'''Settings.

'''
# Radii in meters.
RADIUS_A = 5.0e-9
RADIUS_B = RADIUS_A

# Diffusion constants in meters^2 / second
D_A = 1.e-12
D_B = D_A

# Bimolecular reaction rates in 'meters^3 per second'.
kon = 1e-18

# Unimolecular reaction rates in 'per second'.
koff = 100
k3 = 200

# Diffusion limited rate.
kD = k_D(2 * D_A, 2 * RADIUS_A) 

# Overall reaction rates.
k2 = k_a(kon, kD)
k1 = k_d(koff, kon, kD)


'''Define ParticleTypes.

'''
A = ParticleType('A', D_A, RADIUS_A)
B = ParticleType('B', D_B, RADIUS_B)


'''Add ParticleTypes (to specific Regions or Surfaces).

'''
model.add_particle_type(A)
model.add_particle_type(B)


'''Add reaction rules.

A     -> A + A
A + A -> B
B     -> A

'''
model.add_reaction_rule(A,  [A, A], koff)
model.add_reaction_rule([A, A], B,  kon)
model.add_reaction_rule(B,  A, k3)


'''Output

'''
print 'L = ', L
print 'k1 = ', k1
print 'k2 = ', k2
print 'k3 = ', k3
print 'kD = ', kD
print 'koff = ', koff
print 'kon = ', kon
#print 'kon / koff = ', kon / koff
#print 'ka / kd = ', ka / kd
#model.set_all_repulsive()
print model.dump_reaction_rules()

