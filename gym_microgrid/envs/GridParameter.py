
# coding: utf-8

import os

class GridParameter():
    def __init__(self):
        #PV_TRANS_LOSS = 0.99     

        #HP_MIN_OUTPUT = 100.0
        self.HP_CAPACITY = 300.0
        self.HP_COP = 3.667

        self.DATA_PATH      = os.getcwd() + '/data_done.xlsx'

        #LOSS_TO_COMMUNITY = 0.2
        #LOSS_TANK_IN = 0.1056
        #LOSS_TANK_OUT = 0.1056

        self.DAYS = 365        
        self.NUMBER_SAMPLE_DAYS = 3
        self.TIME_INTERVAL_PER_DAY = 48
        self.TRAJ_LEN = self.NUMBER_SAMPLE_DAYS * self.TIME_INTERVAL_PER_DAY                ## 3 days * 48
        self.TRAJ_LEN_EXPERT = self.TRAJ_LEN
        #self.TRAJ_LEN_EXPERT = (self.NUMBER_SAMPLE_DAYS*2 - 1) * self.TIME_INTERVAL_PER_DAY ## 3*2-1 days * 48
        
        self.FIRST_DAY = 2
        ## day 1 is reserved for providing discounted historical data to day 2, which is day[1] 
        self.LAST_DAY  = self.DAYS - (self.NUMBER_SAMPLE_DAYS - 1)*2
        ## constrained by NUMBER_SAMPLE_DAYS,
        ## for example: NUMBER_SAMPLE_DAYS = 3, last day = 365 - 4 = 361.
        ## Reason:
        ## when choosing day 361, we sample day 361 to 363. 
        ## Day 364 and 365 provides forecast information for day 363.
        
        self.FIRST_DAY = self.FIRST_DAY-1 ## index start with 0
        self.LAST_DAY  = self.LAST_DAY -1

        self.TANK_CAPACITY = 1000.0  
        self.TANK_LOSS_PER_DAY  = 0.7
        self.TANK_LOSS_PER_T = pow(self.TANK_LOSS_PER_DAY,1/self.TIME_INTERVAL_PER_DAY)
        #TANK_RESERVATION = 0.2

        ## BASED ON: https://www.greenenergyuk.com/Tide
        self.PRICE_HIGH = 0.3    ## per kWh electricity, 16:00 – 20:00
        self.PRICE_MID  = 0.14   ## per kWh electricity, 07:00 – 16:00, 20:00 – 00:00
        self.PRICE_LOW  = 0.064  ## per kWh electricity, 00:00 – 07:00

        self.TIME_HIGH_START  = 32  ## 0 to 47 = [00:00-00:30] to [23:00-00:00(+1 day)], respectively
        self.TIME_HIGH_END    = 39  ## divide a day into 48 half-hour interval
        self.TIME_LOW_START   = 0
        self.TIME_LOW_END     = 13


        self.PRICE_EXPORT = 0.05 ## per kWh electricity, assumption

        ## if RETRO_HORIZON = 3, I(information) for t is:
        ## (I[t-1] + I[t-2]*dsct + I[t-3]*dsct**2) / (1 + dsct + dsct**2) 
        self.RETRO_DSCT    = 0.5 ## discount coefficient
        self.RETRO_HORIZON = 4
        
        r = self.RETRO_DSCT
        n = self.RETRO_HORIZON
        if n == 1:
            self.RETRO_DSCT_DENOMITATOR = 1
        else:
            self.RETRO_DSCT_DENOMITATOR  = (1 - r**n) / (1 - r) ## sum of Geometric series, where a=1
  

        self.BENEFIT_THRESHOLD = 0.8  
        ## a thresold of the ratio(of cost) = [stored heat from other time / import electricity right now]
        ## only ratio smaller than BENEFIT_THRESOLD would be taken into consideration
        ## Thus, we can avoid storing heat(namely occupying tank capacity) that doesn't bring much benefit

        self.DURATION_THRESHOLD = 72
        ## a thresold of the duration in which an amount of heat stays in tank.
        ## only duration less than DURATION_THRESOLD would be taken into consideration
        ## Thus, we can avoid occupying tank capacity for too long

        self.PRIME_PV = 7

