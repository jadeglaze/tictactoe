import sys

import pygame

from pygame.sprite import Group
from pygame.surface import Surface
from game import Game, IllegalMoveError

# Constants
FPS = 60
BLOCK_SIZE = 100
PAD_SIZE = 10
MARK_SIZE = BLOCK_SIZE - (PAD_SIZE * 2)
MARK_WIDTH = 8
GRIDLINE_WIDTH = 6
BOARD_SIZE = BLOCK_SIZE * 3
GRIDLINE_LENGTH = BOARD_SIZE

GRIDLINE_COLOR = "white"
MARK_COLOR = "white"


class MarkSprite(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.mark_images = {
            ".": Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA),
            "X": Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA),
            "O": Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        }
        self.draw_x(self.mark_images["X"])
        self.draw_o(self.mark_images["O"])
        self._mark = "."
        self.image = self.mark_images["."]
        self.rect = self.image.get_rect(center=pos)

    def mark(self, m: str):
        self._mark = m

    def update(self) -> None:
        self.image = self.mark_images[self._mark]

    def draw_x(self, screen: Surface):
        start_pos = (PAD_SIZE, PAD_SIZE)
        end_pos = (MARK_SIZE, MARK_SIZE)
        pygame.draw.line(screen, MARK_COLOR, start_pos, end_pos, MARK_WIDTH)
        start_pos = (MARK_SIZE, PAD_SIZE)
        end_pos = (PAD_SIZE, MARK_SIZE)
        pygame.draw.line(screen, MARK_COLOR, start_pos, end_pos, MARK_WIDTH)

    def draw_o(self, screen: Surface):
        center = (PAD_SIZE + MARK_SIZE//2, PAD_SIZE + MARK_SIZE//2)
        pygame.draw.circle(screen, MARK_COLOR, center, MARK_SIZE//2, MARK_WIDTH)


class GameRenderer:
    def __init__(self):
        self.game = Game(0, None)
        self.sprites = Group(
            [
                MarkSprite((x * BLOCK_SIZE + BLOCK_SIZE//2, y * BLOCK_SIZE + BLOCK_SIZE//2))
                for x in range(3) for y in range(3)
            ]
        )
        self.font = pygame.font.Font(None, 36)
        self.game_over = False

    def draw(self, screen: Surface):
        self.draw_grid(screen)
        self.sprites.draw(screen)

        if self.game_over:
            if self.game.winner == "draw":
                text = self.font.render("Draw!", True, 'yellow', 'black')
            else:
                text = self.font.render(f"{self.game.winner} wins!", True, 'yellow', 'black')
            text_rect = text.get_rect()
            text_rect.center = (BOARD_SIZE//2, BOARD_SIZE//2)
            screen.blit(text, text_rect)

    def draw_grid(self, screen):
        # horizontal gridlines
        self.draw_gridline(
            screen, (0, BLOCK_SIZE - (GRIDLINE_WIDTH//2)), (BOARD_SIZE, BLOCK_SIZE - (GRIDLINE_WIDTH//2)))
        self.draw_gridline(
            screen, (0, (BLOCK_SIZE * 2) - (GRIDLINE_WIDTH//2)), (BOARD_SIZE, (BLOCK_SIZE * 2) - (GRIDLINE_WIDTH//2)))
        # vertical gridlines
        self.draw_gridline(
            screen, (BLOCK_SIZE - (GRIDLINE_WIDTH//2), 0), (BLOCK_SIZE - (GRIDLINE_WIDTH//2), BOARD_SIZE))
        self.draw_gridline(
            screen, ((BLOCK_SIZE * 2) - (GRIDLINE_WIDTH//2), 0), ((BLOCK_SIZE * 2) - (GRIDLINE_WIDTH//2), BOARD_SIZE))

    def draw_gridline(self, screen, start_pos, end_pos):
        pygame.draw.line(screen, GRIDLINE_COLOR, start_pos, end_pos, GRIDLINE_WIDTH)

    def tic(self, mouse_pos):
        # translate mouse position to board position
        cell_y, cell_x = mouse_pos[0] // BLOCK_SIZE, mouse_pos[1] // BLOCK_SIZE
        print(mouse_pos, cell_x, cell_y)
        # mark X at board position
        try:
            self.game.play_round(cell_x, cell_y)
        except IllegalMoveError:
            return  # just ignore the click
        # set all sprite states based on current board
        for y in range(3):
            for x in range(3):
                self.sprites.sprites()[y*3+x].mark(self.game.boards[-1][y][x])
        # check for game over (win or draw)
        self.game_over = (self.game.winner is not None)

    def update(self):
        self.sprites.update()


def main():
    # Initialize pygame
    pygame.init()

    # Set up the window
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("Tic Tac Toe - n: new game, q: quit")

    # Set up the clock
    clock = pygame.time.Clock()

    # Set up the game board
    game = GameRenderer()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONUP:
                game.tic(pygame.mouse.get_pos())

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_n:
                    game = GameRenderer()

        game.update()

        pygame.display.flip()
        game.draw(screen)
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
