# Deeply Learning Minesweeper
A deep exploration into the game of Minesweeper. Built using pygame, numpy, and pytorch.

Minesweeper is a grid-based game of pure logic and chance (you can always either figure it out, or it's simply a game
of probability). Can a computer learn to play it well? _How_ does it learn the game?

How complex are Minesweeper games? Could a game be guaranteed to be solvable? What do optimal solvers look like?

How likely are you to win a particular game, for different game configurations? Can you get better chances of winning?

What happens with other tesselations? Is triangular or hexagonal minesweeper any different?

## Rules of the Game for Humans
Each cell can be hidden or open (or _flagged_). Underneath some of the cells is a mine; opening a cell with a mine
underneath ends the game. To figure out where the mines are, opening cells without mines underneath will display
the number of mines in the cells adjacent to that cell (including corner adjacent cells). The goal of the game is to 
open all cells that don't have mines underneath.

Some usual features of the game:
- you can 'flag' a cell to mark that you believe there's a mine underneath
- by double-clicking an open cell (obviously without a mine in it), adjacent cells will be opened for you if the
 number of adjacent flags matches the number in the cell---this is called chording
- there are additional special features that can be activated in this version of the game

TODO: add images for clarification

## Possible Learning Models
- train an imitation learner that plays like a person
- learn a reinforcement algorithm that plays the game and develops a sense of the logic
- train a reinforcement GAN to learn to play the game better in worse conditions
  - discriminator plays the game (maximizes reward)
  - generator produces difficult game boards (minimizes discriminator's reward **and** number of mines)

### RL Agent
Input: matrices containing environment states
- visibility mask: whether each cell is {HIDDEN, OPEN, FLAGGED} (in general, FLAGGED just means HIDDEN)
- proximity (neighbors) matrix: how many mines are in the vicinity of each cell

Output: (normalized) coordinates of cell to open

Metrics: knowledge of the board state, completion/percentage of cells opened, negative for opening mines
- reward of participation: OoS (open over sites)
- reward of knowledge: msd (mean squared degree)
- cost of mines: MoS (mines over sites)
