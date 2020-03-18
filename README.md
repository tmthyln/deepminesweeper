# Deep Learning Minesweeper
An exploration into training a machine to learn how to play Minesweeper built using pygame, numpy, and pytorch.

Minesweeper is a grid-based game of pure logic and chance (you can always either figure it out, or it's simply a game
 of probability). Can a computer learn to play it well? _How_ does it learn the game?

## Rules of the Game for Humans
Each cell can be hidden or open (or _flagged_). Underneath some of the cells is a mine; opening a cell with a mine
 underneath ends the game. To figure out where the mines are, opening cells without mines underneath will display
  the number of mines in the 8 cells adjacent to that cell. The goal of the game is to open all cells that don't have
   mines underneath.

Some usual features of the game:
- you can 'flag' a cell to mark that you believe there's a mine underneath
- by double-clicking an open cell (obviously without a mine in it), adjacent cells will be opened for you if the
 number of adjacent flags matches the number in the cell---this is called chording

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
