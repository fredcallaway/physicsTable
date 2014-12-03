



from __future__ import division
import sys, os, time
from noisyTable import *
from .utils.EasyMultithread import *
import numpy as np

class PointSimulation(object):
    
    def __init__(self,table, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, ensure_end = False, nsims = 200, maxtime = 50., cpus = cpu_count(), timeres = 0.05):
        self.tab = table
        self.kapv = kapv
        self.kapb = kapb
        self.kapm = kapm / np.sqrt(timeres / 0.001) # Correction for the fact that we're simulating fewer steps and thus jitter must be noisier (by approx sqrt of number of steps)
        self.perr = perr
        self.maxtime = maxtime
        self.nsims = nsims
        self.ts = timeres
        
        self.outcomes = None
        self.endpts = None
        self.bounces = None
        self.time = None
        self.run = False
        self.enend = ensure_end
        
        self.ucpus = cpus
        self.badsims = 0
        
    
    def singleSim(self, i):
        n = makeNoisy(self.tab,self.kapv,self.kapb,self.kapm,self.perr)
        n.set_timestep(self.ts)
        r = n.simulate(self.maxtime)
        p = n.balls.getpos()
        nb = n.balls.bounces
        rp = (p[0],p[1])
        tm = n.tm
        if self.enend:
            if r == TIMEUP:
                self.badsims += 1
                return(self.singleSim(i))
            if rp[0] < 0 or rp[0] > self.tab.dim[0] or rp[1] < 0 or rp[1] > self.tab.dim[1]:
                self.badsims += 1
                return(self.singleSim(i))
        return [r, rp, nb, tm]
    
    def runSimulation(self):
        
        ret = multimap(self.singleSim,range(self.nsims), self.ucpus)
        
        self.outcomes = [r[0] for r in ret]
        self.endpts = [r[1] for r in ret]
        self.bounces = [r[2] for r in ret]
        self.time = [r[3] for r in ret]
        self.run = True
        
        return [self.outcomes, self.endpts, self.bounces, self.time]
        
    def getOutcomes(self):
        if not self.run: raise Exception('Cannot get simulation outcome without running simulations first')
        retdict = dict([(r,0) for r in self.tab.goalrettypes])
        for o in self.outcomes:
            retdict[o] += 1
        
        return retdict

    def getEndpoints(self, xonly = False, yonly = False):
        if not self.run: raise Exception('Cannot get simulation endpoints without running simulations first')
        if xonly and not yonly:
            return [p[0] for p in self.endpts]
        if yonly and not xonly:
            return [p[1] for p in self.endpts]
        return self.endpts

    def getBounces(self):
        if not self.run: raise Exception('Cannot get simulation outcome without running simulations first')
        return self.bounces

    def getTime(self):
        if not self.run: raise Exception('Cannot get simulation time without running simulations first')
        return self.time
    
    def drawdensity(self, rp_wid = 5, greyscale = (0,255), gamadj = .2):
        ptharray = np.zeros(table.dim)
        
        def singpth(i):
            print i
            n = makeNoisy(self.tab,self.kapv,self.kapb,self.kapm,self.perr)
            r = n.simulate(self.maxtime, return_path = True, rp_wid = rp_wid)
            print 'd',i
            return r[1]
        sims = map(singpth, range(self.nsims))
        
        print 'simulated'
        for s in sims:
            ptharray = np.add(ptharray,s)
        paths = ptharray / np.max(ptharray)
    
        gsadj = greyscale[1] - greyscale[0]
        #colarray = np.zeros(table.dim)
        
        print 'some adjustments'
        n = makeNoisy(self.tab,None,None,None,None)
        realpath = n.simulate(self.maxtime,return_path=True)[1]
        
        print 'real made'
        
        sc = table.draw()
        #sarray = pg.surfarray.pixels3d(sc)
        #print sarray
        
        print 'initial draw'
        for i in range(table.dim[0]):
            print i
            for j in range(table.dim[1]):
                if paths[i,j] > 0:
                    tmpcol = int(greyscale[1] - gsadj * paths[i,j] * gamadj)
                    if tmpcol < 0: tmpcol = 0
                    #sarray[i,j] = (tmpcol,tmpcol,tmpcol)
                    sc.set_at((i,j), pg.Color(tmpcol,tmpcol,tmpcol,255))
                #else:
                #    colarray[i,j] = 255
    
        
        table.balls.draw(sc)
        pg.draw.lines(sc, table.balls.col, False, realpath)
        return sc
        
    def savepath(self, imgnm):
        sc = self.drawdensity()
        pg.image.save(sc, imgnm)
   
