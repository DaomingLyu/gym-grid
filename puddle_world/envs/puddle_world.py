import numpy as np

from gym import error, spaces, utils
from gym.utils import seeding

def categorical_sample(prob_n, np_random):
    """
    Sample from categorical distribution
    Each row specifies class probabilities
    """
    prob_n = np.asarray(prob_n)
    csprob_n = np.cumsum(prob_n)
    return (csprob_n > np_random.rand()).argmax()


class DiscreteEnv(Env):

    """
    Has the following members
    - nS: number of states
    - nA: number of actions
    - P: transitions (*)
    - isd: initial state distribution (**)

    (*) dictionary dict of dicts of lists, where
      P[s][a] == [(probability, nextstate, reward, done), ...]
    (**) list or array of length nS


    """
    def __init__(self, nS, nA, P, isd):
        self.P = P
        self.isd = isd
        self.lastaction=None # for rendering
        self.nS = nS
        self.nA = nA

        self.action_space = spaces.Discrete(self.nA)
        self.observation_space = spaces.Discrete(self.nS)

        self._seed()
        self._reset()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _reset(self):
        self.s = categorical_sample(self.isd, self.np_random)
        self.lastaction=None
        return self.s

    def _step(self, a):
        transitions = self.P[self.s][a]
        i = categorical_sample([t[0] for t in transitions], self.np_random)
        p, s, r, d= transitions[i]
        self.s = s
        self.lastaction=a
        return (s, r, d, {"prob" : p})



UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

class GridWorld(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, n=10, noise=0.1, terminal_reward=1.0, 
          border_reward=0.0, step_reward=0.0, start_state=0, 
          bump_reward = -0.5, terminal_state_offset=11): #'random'):
    self.n = n
    self.noise = noise
    self.terminal_reward = terminal_reward
    self.border_reward = border_reward
    self.bump_reward = bump_reward
    self.step_reward = step_reward
    self.n_states = self.n ** 2 + 1
    self.terminal_state = self.n_states - 2 - terminal_state_offset
    self.absorbing_state = self.n_states - 1
    self.done = False
    self.start_state = start_state #if not isinstance(start_state, str) else np.random.rand(n**2)
    self._reset()

    self.action_space = spaces.Discrete(4)
    self.observation_space = spaces.Discrete(self.n_states) # with absorbing state
    #self._seed()

  def _step(self, action):
    assert self.action_space.contains(action)

    if self.state == self.terminal_state:
      self.state = self.absorbing_state
      self.done = True
      return self.state, self._get_reward(), self.done, None

    [row, col] = self.ind2coord(self.state)

    if np.random.rand() < self.noise:
      action = self.action_space.sample()

    if action == UP:
      row = max(row - 1, 0)
    elif action == DOWN:
      row = min(row + 1, self.n - 1)
    elif action == RIGHT:
      col = min(col + 1, self.n - 1)
    elif action == LEFT:
      col = max(col - 1, 0)

    new_state = self.coord2ind([row, col])

    reward = self._get_reward(new_state=new_state)

    self.state = new_state

    return self.state, reward, self.done, None

  def _get_reward(self, new_state=None):
    if self.done:
      return self.terminal_reward

    reward = self.step_reward
    
    if self.border_reward != 0 and self.at_border():
      reward = self.border_reward

    if self.bump_reward != 0 and self.state == new_state:
      reward = self.bump_reward

    return reward

  def at_border(self):
    [row, col] = self.ind2coord(self.state)
    return (row == 0 or row == self.n - 1 or col == 0 or col == self.n - 1)

  def ind2coord(self, index):
    assert(index >= 0)
    #assert(index < self.n_states - 1)

    col = index // self.n
    row = index % self.n

    return [row, col]


  def coord2ind(self, coord):
    [row, col] = coord
    assert(row < self.n)
    assert(col < self.n)

    return col * self.n + row


  def _reset(self):
    self.state = self.start_state if not isinstance(self.start_state, str) else np.random.randint(self.n_states - 1)
    self.done = False
    return self.state

  def _render(self, mode='human', close=False):
    pass
      