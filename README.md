# WORK IN PROGRESS

# deepminesweeper (Deep Learning Minesweeper)
Requirements: pygame, numpy
Minesweeper is a grid-based game of pure logic and pure chance. Can a computer learn to play it well? Better than humans?

## Rules of the Game (How to Play for Yourself)
Each cell is either blank, has a number (degree in the code), or has a mine. If the cell is blank, it is not touching any mines. The number on the cell tells you how many mines (up to 8) that cell is adjacent to. The goal is to open all cells in the game that are not mines, without detonating a mine (which, in the classic version of the game, detonates ALL the mines).

When you 'open' a cell:
- if there's a mine underneath, the game's over
- if there's not a number underneath (adjacent to 0 mines), then the entire connected component is revealed for you

## Learning Models
- learn a reinforcement algorithm that plays the game and develops a sense of the logic
- train a reinforcement GAN to learn to play the game better in worse conditions
  - discriminator plays the game
  - generator produces difficult game boards

### RL Agent
Input: masks containing environment states
Output: soft bitmask containing choices of cells to open
Reward: knowledge of the board state, completion/percentage of cells opened, negative for opening mines
- weighted to encourage making riskier choices (perhaps weighted by cell degree+1)
