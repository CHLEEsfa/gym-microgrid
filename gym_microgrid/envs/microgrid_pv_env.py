
# coding: utf-8
import gym
from gym import error, spaces, utils
from gym.utils import seeding

import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas as pd


import GridParameter as GDP




class MicrogridPVEnv(gym.Env, GDP.GridParameter):
    metadata = {
        'render.modes': ['human'],
    }

    def __init__(self):
        GDP.GridParameter.__init__(self)
        
        self.Data = pd.read_excel(self.DATA_PATH)

        self.min_action = -1
        self.max_action = self.HP_CAPACITY
        
        self.min_tank_level = 0.0
        self.max_tank_level = self.TANK_CAPACITY

        self.min_time = 1.0
        self.max_time = self.TIME_INTERVAL_PER_DAY
        self.min_price = self.PRICE_LOW
        self.max_price = self.PRICE_HIGH
        self.min_month = 1.0
        self.max_month = 12.0
        self.min_forecast = -1.0
        self.max_forecast = 1.0
        self.min_Solar = self.Data['PV'].min() * self.HP_COP
        self.max_Solar = self.Data['PV'].max() * self.HP_COP
        self.min_Demand = self.Data['HeatDemand'].min()
        self.max_Demand = self.Data['HeatDemand'].max()
        
        self.low_state  = np.array([self.min_tank_level, self.min_time, self.min_price, 
                                    self.min_month, self.min_forecast,
                                    self.min_forecast, self.min_forecast,
                                    self.min_Solar, self.min_Demand])
        self.high_state = np.array([self.max_tank_level, self.max_time, self.max_price, 
                                    self.max_month, self.max_forecast,
                                    self.min_forecast, self.min_forecast,
                                    self.max_Solar, self.max_Demand])

        self.viewer = None  ## ??

        self.action_space = spaces.Box(low=self.min_action, high=self.max_action, shape=(1,))
        self.observation_space = spaces.Box(low=self.low_state, high=self.high_state)

        self.seed()  
        self.reset()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    
    
    def step(self, action):

        surplus_t  = self.Data.loc[self.t, 'PVSurplus_h']
        shortage_t = self.Data.loc[self.t, 'Shortage_h']
        price_t    = self.Data.loc[self.t, 'Price']
        
        end = self.SampleAt + self.TRAJ_LEN

        
        amount = action
        if amount < 0:  # agent decides to discharge

            if abs(amount) > self.TankLevel:
                amount = -self.TankLevel
            
            if surplus_t > 0 and shortage_t == 0:
                self.export_p += surplus_t / self.HP_COP * self.PRICE_EXPORT
                surplus_t = 0.0
                self.TankLevel = (self.TankLevel + amount) * self.TANK_LOSS_PER_T
                
            if shortage_t > 0:
                if shortage_t > abs(amount):
                    shortage_t += amount
                    self.TankLevel = (self.TankLevel + amount) * self.TANK_LOSS_PER_T
                    
                    if shortage_t > 0:
                        self.import_demand_p += shortage_t / self.HP_COP * price_t
                        shortage_t = 0.0
                else:
                    shortage_t = 0.0
                    self.TankLevel = (self.TankLevel + amount) * self.TANK_LOSS_PER_T

                
        elif amount > 0: # agent decides to charge
            if amount > self.TANK_CAPACITY - self.TankLevel * self.TANK_LOSS_PER_T:
                amount = self.TANK_CAPACITY - self.TankLevel * self.TANK_LOSS_PER_T
            if amount > self.HeatPump:
                amount = self.HeatPump  
                
            if  surplus_t >= 0 and shortage_t == 0:
                #print(self.t, ' amount: ', amount)
                if surplus_t >= amount:
                    surplus_t -= amount
                    self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T + amount
                    amount = 0
                    
                    if surplus_t > 0:
                        self.export_p += surplus_t / self.HP_COP * self.PRICE_EXPORT
                    surplus_t = 0.0
                else:
                    self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T + amount
                    amount -= surplus_t
                    surplus_t = 0.0
                    self.import_charge_p += amount / self.HP_COP * price_t                    
                    amount = 0.0
                    
            if shortage_t > 0:
                self.import_demand_p += shortage_t / self.HP_COP * price_t
                shortage_t = 0.0
                self.import_charge_p += amount / self.HP_COP * price_t
                self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T + amount
                amount = 0.0
                
                
        else:  # agent does nothing
            if surplus_t == 0 and shortage_t == 0:
                self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T
                
            if  surplus_t > 0:
                self.export_p += surplus_t / self.HP_COP * self.PRICE_EXPORT
                surplus_t = 0.0
                self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T
                
            if shortage_t > 0:
                self.import_demand_p += shortage_t / self.HP_COP * price_t
                shortage_t = 0.0           
                self.TankLevel = self.TankLevel * self.TANK_LOSS_PER_T
                
             
        assert surplus_t == 0 and amount <= 0 and shortage_t == 0, 'Error: check energy balance'
        
        self.t += 1
        done = bool(self.t == end)
        if not done:
            self.state = self.UpdatState_t(self.TankLevel, self.Data, self.t)
        else:
            self.CostTank = math.ceil((-self.export_p + self.import_charge_p + self.import_demand_p)*1e2)/1e2
            #print(self.SampleAt, ' env cost= ', self.CostTank, '\n\n') 
            ## cost: import = pay money(+), export = earn money(-)
        

        return self.state, 0, done, {}  ## reward set to be always 0

    
    
    
    def reset(self, index = None):
        if index != None:
            self.SampleAt = int(index)
        else:
            self.SampleAt = int(np.random.randint(self.FIRST_DAY, self.LAST_DAY) * self.TIME_INTERVAL_PER_DAY)
        
        self.t = self.SampleAt
        
        self.TankLevel = 0.0
        self.HeatPump  = self.HP_CAPACITY - self.Data.loc[self.t, 'HeatDemand']
        self.export_p        = 0.0
        self.import_charge_p = 0.0
        self.import_demand_p = 0.0
        
        self.state = self.UpdatState_t(self.TankLevel, self.Data, self.t)
        return np.array(self.state)

    
    def UpdatState_t(self, tanklevel, data, index):
        
        if tanklevel < 1e-7:  
            tanklevel = 0.0
            
        hour  = data.loc[index, 'Hour']
        price = data.loc[index, 'Price']
        month = data.loc[index, 'Month']
        forecast_t  = data.loc[index, 'Forecast']
        forecast_t1 = data.loc[index+48, 'Forecast']
        forecast_t2 = data.loc[index+48*2, 'Forecast']
        solar  = data.loc[index, 'PV_retro']
        demand = data.loc[index, 'HeatDemand_retro']
        
        #print(index, ' state: ', tanklevel, hour, price, month, forecast_t, forecast_t1, forecast_t2, solar, demand)

        return np.array([tanklevel, hour, price, month, 
                         forecast_t, forecast_t1, forecast_t2,
                         solar, demand])    
    
    
    def get_state(self):
        return self.state
    
    def get_curr_t(self):
        return self.t


    def render(self, mode='human'):
        return True

    def close(self):
        if self.viewer: self.viewer.close()


