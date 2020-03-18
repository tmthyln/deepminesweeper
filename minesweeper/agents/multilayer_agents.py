import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn

from minesweeper.board import HiddenBoardState
from minesweeper import register_agent
from minesweeper.actions import Action
from minesweeper import Agent

from typing import Sequence, Literal

__all__ = ['LearnableConvolutionalAgent']


class DirectModel(nn.Module):
    
    def __init__(self):
        super().__init__()
        
        self.conv1 = nn.Conv2d(2, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 32, 3, padding=1)
        self.conv3 = nn.Conv2d(32, 16, 3, padding=1)
        self.conv4 = nn.Conv2d(16, 1, 1, padding=1)
    
    def forward(self, x) -> torch.Tensor:
        x = self.conv1(x.unsqueeze(0))
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        return x


@register_agent('deep')
class LearnableConvolutionalAgent(Agent):
    
    def __init__(self, mode: Literal['train', 'predict']):
        self.net = DirectModel()
        self.optimizer = optim.Adam(self.net.parameters(), lr=0.005)
    
    def start(self, grid_size, config):
        pass

    def act(self, state: HiddenBoardState) -> Sequence[Action]:
        self._input = self._stack_inputs(state.openable_layout, state.proximity_matrix)
        
        self.optimizer.zero_grad()
        self._output = self.net(input)
        
        # TODO convert output to actions
        
        pass
        
    def react(self, state: HiddenBoardState, status):
        new_input = self._stack_inputs(state.openable_layout, state.proximity_matrix)
        added = self._input[0] & ~new_input[0]
        
        # TODO create an appropriate target/loss from output
        
        loss = nn.MSELoss(self._output.flatten(start_dim=1), self._stack_inputs())
        loss.backward()
        self.optimizer.step()
        
    def _stack_inputs(self, mat1: np.ndarray, mat2: np.ndarray):
        return np.vstack([np.expand_dims(mat1, axis=0), np.expand_dims(mat2, axis=0)]).copy()
