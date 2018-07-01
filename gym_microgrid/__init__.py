from gym.envs.registration import register

register(
    id='MicrogridPV-v0',
    entry_point='gym_microgrid.envs:MicrogridPVEnv',
)
