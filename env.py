import time

import gym
from enums.player_action import PlayerAction
from game import Game

MOVEMENT_ACTIONS = [PlayerAction.NORTH, PlayerAction.SOUTH, PlayerAction.EAST, PlayerAction.WEST]


class SupermarketEnv(gym.Env):

    def __init__(self, num_players=1, player_speed=0.15, keyboard_input=False, render_messages=True, bagging=False,
                 headless=False, initial_state_filename=None, follow_player=-1, random_start=False,
                 render_number=False, max_num_items=33, player_sprites=None, record_path=None, stay_alive=False):

        super(SupermarketEnv, self).__init__()

        self.step_count = 0
        self.render_messages = render_messages
        self.keyboard_input = keyboard_input
        self.render_number = render_number
        self.bagging = bagging

        self.follow_player = follow_player

        self.num_players = num_players
        self.player_speed = player_speed
        self.game = None
        self.player_sprites = player_sprites

        self.record_path = record_path
        self.max_num_items=max_num_items

        self.stay_alive = stay_alive

        self.initial_state_filename = initial_state_filename

        self.action_space = gym.spaces.Tuple([gym.spaces.Tuple((gym.spaces.Discrete(len(PlayerAction)),
                                                                gym.spaces.Discrete(max_num_items)))] * num_players)
        self.observation_space = gym.spaces.Dict()
        self.headless = headless
        self.random_start = random_start

    def step(self, action):
        done = False
        for i, player_action in enumerate(action):
            player_action, arg = player_action
            if player_action in MOVEMENT_ACTIONS:
                self.game.player_move(i, player_action)
            elif player_action == PlayerAction.NOP:
                self.game.nop(i)
            elif player_action == PlayerAction.INTERACT:
                self.game.interact(i)
            elif player_action == PlayerAction.TOGGLE:
                self.game.toggle_cart(i)
                self.game.toggle_basket(i)
            elif player_action == PlayerAction.CANCEL:
                self.game.cancel_interaction(i)
            elif player_action == PlayerAction.PICKUP:
                self.game.pickup(i, arg)
        observation = self.game.observation()
        self.step_count += 1
        if not self.game.running:
            done = True
        return observation, 0., done, None

    def reset(self, obs=None):
        self.game = Game(self.num_players, self.player_speed,
                         keyboard_input=self.keyboard_input,
                         render_messages=self.render_messages,
                         bagging=self.bagging,
                         headless=self.headless, initial_state_filename=self.initial_state_filename,
                         follow_player=self.follow_player, random_start=self.random_start,
                         render_number=self.render_number,
                         sprite_paths=self.player_sprites,
                         record_path=self.record_path,
                         stay_alive=self.stay_alive)
        self.game.set_up()
        if obs is not None:
            self.game.set_observation(obs)
        self.step_count = 0
        return self.game.observation()

    def render(self, mode='human'):
        if mode.lower() == 'human' and not self.headless:
            self.game.update()
        else:
            print(self.game.observation(True))


class SinglePlayerSupermarketEnv(gym.Wrapper):
    def __init__(self, env):
        super(SinglePlayerSupermarketEnv, self).__init__(env)
        self.action_space = gym.spaces.Tuple((gym.spaces.Discrete(self.num_players),
                                              gym.spaces.Discrete(len(PlayerAction)),
                                              gym.spaces.Discrete(self.max_num_items)))

    def convert_action(self, player_action):
        i, action, arg = player_action
        full_action = [(PlayerAction.NOP, 0)]*self.num_players
        full_action[i] = (action, arg)
        return full_action

    def step(self, player_action):
        done = False
        i, player_action, arg = player_action
        if player_action in MOVEMENT_ACTIONS:
            self.game.player_move(i, player_action)
        elif player_action == PlayerAction.NOP:
            self.game.nop(i)
        elif player_action == PlayerAction.INTERACT:
            self.game.interact(i)
        elif player_action == PlayerAction.TOGGLE:
            self.game.toggle_cart(i)
            self.game.toggle_basket(i)
        elif player_action == PlayerAction.CANCEL:
            self.game.cancel_interaction(i)
        elif player_action == PlayerAction.PICKUP:
            self.game.pickup(i, arg)
        observation = self.game.observation()
        self.step_count += 1
        if not self.game.running:
            done = True
        return observation, 0., done, None


if __name__ == "__main__":
    env = SupermarketEnv(2)
    env.reset()

    for i in range(100):
        env.step((PlayerAction.EAST, PlayerAction.SOUTH))
        env.render()