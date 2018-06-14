import pygame
from pygame.locals import *

PRIMARY_COLOR = (55, 200, 100)


def main():
    pygame.init()
    screen = pygame.display.set_mode((700, 900), pygame.RESIZABLE)
    pygame.display.set_caption('Deep Minesweeper')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill(PRIMARY_COLOR)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        screen.blit(background, (0, 0))
        pygame.display.flip()


if __name__ == '__main__':
    main()
