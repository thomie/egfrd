A + A -> 0
# Todo. Units.
if DRIFT:
    DRIFT_A = 1
    DRIFT_B = -1
else:
    DRIFT_A = 0
    DRIFT_B = 0



A -> (A, m) -> A
B -> (B, m) -> B

A -> (A

# Surface binding interaction (molecule + surface).
kon = kf_2
# Surface unbinding reaction (unimolecular).
koff = kb_1


    '''Add surface binding interaction rules.

    '''
    if SURFACE_BINDING_INTERACTIONS and MEMBRANE1 and BOX:
        # ParticleType C can bind from the box to membrane1. The 
        # membrane is reflective, by default, to ParticleTypes A and B.
        m.add_reaction_rule((C, b), (C, m1), kon)

    if SURFACE_BINDING_INTERACTIONS and MEMBRANE2 and BOX:
        # Membrane 2 absorbs all particles.
        m.add_reaction_rule((A, b), (0, m2), kon)
        m.add_reaction_rule((B, b), (0, m2), kon)
        m.add_reaction_rule((C, b), (0, m2), kon)

    if SURFACE_BINDING_INTERACTIONS and DNA and BOX:
        # ParticleType C can bind from the box to the dna. The dna is 
        # reflective, by default, to ParticleTypes A and B.
        m.add_reaction_rule((C, b), (C, d), kon)


    ''' Add surface unbinding reaction rules.

    '''
    if SURFACE_UNBINDING_REACTIONS and MEMBRANE1 and BOX:
        # Species C can unbind from membrane1 to the box.
        m.add_reaction_rule((C, m1), (C, b), koff)

    if SURFACE_UNBINDING_REACTIONS and MEMBRANE2 and BOX:
        pass

    if SURFACE_UNBINDING_REACTIONS and DNA and BOX:
        # Species C can unbind from the dna to the box.
        m.add_reaction_rule((C, d), (C, b), koff)

LOGGER                       = None
SURFACE_BINDING_INTERACTIONS = None
SURFACE_UNBINDING_REACTIONS  = None
#DRIFT                        = True
#SURFACE_BINDING_INTERACTIONS = True
#SURFACE_UNBINDING_REACTIONS  = True
DRIFT                        = None

# Timescale
#tau = sigma * sigma / D_tot

# Bimolecular reaction type.
#k2w = 100 * sigma * D_tot
# Unimolecular reaction type.
#k1w = 0.1 / tau
