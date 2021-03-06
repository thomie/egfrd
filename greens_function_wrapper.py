import numpy
import myrandom
from _greens_functions import EventType
from utils import *

import logging
log = logging.getLogger('ecell')


def drawTime_wrapper(gf, r0=None):
    rnd = myrandom.uniform()

    if __debug__:
        log.debug('        *drawTime. ' + gf.__class__.__name__)
    try:
        if r0 == None:
            # Todo. Let gf handle this.
            dt = gf.drawTime(rnd)
        else:
            dt = gf.drawTime(rnd, r0)
    except Exception, e:
        raise Exception('gf.drawTime() failed, '
                        '%s, rnd = %g, %s' %
                        (str(e), rnd, gf.dump()))
    return dt

def draw_eventtype_wrapper(gf, dt, r0):
    rnd = myrandom.uniform()

    if __debug__:
        log.debug('        *drawEventType. ' + gf.__class__.__name__)
    try:
        event_type = gf.drawEventType(rnd, r0, dt)
    except Exception, e:
        raise Exception('gf.drawEventType() failed, '
                        '%s, rnd = %g, r0 = %g, dt = %g, %s' %
                        (str(e), rnd, r0, dt, gf.dump()))
    return event_type

# Todo. Returns r, not displacement.
def draw_displacement_wrapper(gf, dt, event_type, a, r0=None, sigma=None):
    if(((event_type == EventType.COM_ESCAPE or
         event_type == EventType.SINGLE_ESCAPE) and sigma == None) or
       (event_type == EventType.IV_ESCAPE and sigma != None)):
        # Escape through this coordinate. We already know the new r.
        # Todo. Let gf handle this.
        return a
    elif event_type == EventType.IV_REACTION and sigma != None:
        # Todo. Let gf handle this.
        return sigma

    rnd = myrandom.uniform()

    if __debug__:
        log.debug('        *drawR. ' + gf.__class__.__name__)
    try:
        if r0 == None:
            r = gf.drawR(rnd, dt)
        else:
            r = gf.drawR(rnd, r0, dt)
        while r > a or r <= sigma: # redraw; shouldn't happen often
            if __debug__:
                log.debug('        *drawR: redraw')
            rnd = myrandom.uniform()
            if r0 == None:
                r = gf.drawR(rnd, dt)
            else:
                r = gf.drawR(rnd, r0, dt)
    except Exception, e:
        raise Exception('gf.drawR() failed, '
                        '%s, rnd = %g, r0 = %s, dt = %g, %s' %
                        (str(e), rnd, r0, dt, gf.dump()))

    return r

# Todo. Returns (r,theta), not displacement.
def draw_displacement_iv_wrapper(gf, r0, dt, event_type, a, sigma):
    def drawTheta_wrapper(gf, r, r0, dt):
        """Draw theta for the inter-particle vector.

        """
        rnd = myrandom.uniform()

        if __debug__:
            log.debug('        *drawTheta. ' + gf.__class__.__name__)
        try:
            theta = gf.drawTheta(rnd, r, r0, dt)
        except Exception, e:
            raise Exception('gf.drawTheta() failed, '
                            '%s, rnd = %g, r = %g, r0 = %g, dt = %g' %
                            (str(e), rnd, r, r0, dt))#, gf.dump()))

        # Heads up. For cylinders theta should be between [-pi, pi]. For 
        # spheres it doesn't matter.
        return myrandom.choice(-1, 1) * theta

    r = draw_displacement_wrapper(gf, dt, event_type, a, r0, sigma)
    theta = drawTheta_wrapper(gf, r, r0, dt)
    return r, theta

