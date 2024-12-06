import pygame
import sys
import time

from minesweeper import Minesweeper, MinesweeperAI

# Constants
HEIGHT = 8
WIDTH = 8
MINES = 8

# Colors
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
WHITE = (255, 255, 255)
DARK_BLUE = (10, 25, 47)
LIGHT_BLUE = (173, 216, 230)
BUTTON_COLOR = (0, 123, 255)
BUTTON_HOVER_COLOR = (0, 105, 217)
TEXT_COLOR = (255, 255, 255)
BLUE = (0, 119, 182)
ORANGE = (245, 172, 66)

# Initialize Pygame
pygame.init()
size = width, height = 600, 400
screen = pygame.display.set_mode(size)

# Fonts
OPEN_SANS = "assets/fonts/OpenSans-Regular.ttf"
small_font = pygame.font.Font(OPEN_SANS, 20)
medium_font = pygame.font.Font(OPEN_SANS, 28)
large_font = pygame.font.Font(OPEN_SANS, 40)

# Compute board size
BOARD_PADDING = 20
board_width = ((2 / 3) * width) - (BOARD_PADDING * 2)
board_height = height - (BOARD_PADDING * 2)
cell_size = int(min(board_width / WIDTH, board_height / HEIGHT))
board_origin = (BOARD_PADDING, BOARD_PADDING)

# Load images
flag = pygame.image.load("assets/images/flag.png")
flag = pygame.transform.scale(flag, (cell_size, cell_size))
mine = pygame.image.load("assets/images/mine.png")
mine = pygame.transform.scale(mine, (cell_size, cell_size))

# Create game and AI agent
game = Minesweeper(height=HEIGHT, width=WIDTH, mines=MINES)
ai = MinesweeperAI(height=HEIGHT, width=WIDTH)

# Track game state
revealed = set()
flags = set()
lost = False
instructions = True

def draw_text(text, font, color, center):
    rendered_text = font.render(text, True, color)
    text_rect = rendered_text.get_rect()
    text_rect.center = center
    screen.blit(rendered_text, text_rect)

def draw_button(rect, text, font, text_color, bg_color):
    pygame.draw.rect(screen, bg_color, rect)
    draw_text(text, font, text_color, rect.center)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    screen.fill(DARK_BLUE)

    if instructions:
        draw_text("Play Minesweeper", large_font, TEXT_COLOR, (width / 2, 50))
        rules = [
            "Click a cell to reveal it.",
            "Right-click a cell to mark it as a mine.",
            "Mark all mines successfully to win!",
        ]
        for i, rule in enumerate(rules):
            draw_text(rule, small_font, TEXT_COLOR, (width / 2, 150 + 30 * i))

        play_button_rect = pygame.Rect((width / 4), (3 / 4) * height, width / 2, 50)
        mouse_pos = pygame.mouse.get_pos()
        if play_button_rect.collidepoint(mouse_pos):
            button_color = BUTTON_HOVER_COLOR
        else:
            button_color = BUTTON_COLOR
        draw_button(play_button_rect, "Play Game", medium_font, TEXT_COLOR, button_color)

        if pygame.mouse.get_pressed()[0] and play_button_rect.collidepoint(mouse_pos):
            instructions = False
            time.sleep(0.3)

        pygame.display.flip()
        continue

    cells = []
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            rect = pygame.Rect(board_origin[0] + j * cell_size, board_origin[1] + i * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, ORANGE, rect)
            pygame.draw.rect(screen, BLUE, rect, 3)

            if game.is_mine((i, j)) and lost:
                screen.blit(mine, rect)
            elif (i, j) in flags:
                screen.blit(flag, rect)
            elif (i, j) in revealed:
                neighbors = small_font.render(str(game.nearby_mines((i, j))), True, BLACK)
                neighbors_rect = neighbors.get_rect()
                neighbors_rect.center = rect.center
                screen.blit(neighbors, neighbors_rect)

            row.append(rect)
        cells.append(row)

    ai_button_rect = pygame.Rect((2 / 3) * width + BOARD_PADDING, (1 / 3) * height - 50, (width / 3) - BOARD_PADDING * 2, 50)
    mouse_pos = pygame.mouse.get_pos()
    if ai_button_rect.collidepoint(mouse_pos):
        button_color = BUTTON_HOVER_COLOR
    else:
        button_color = BUTTON_COLOR
    draw_button(ai_button_rect, "AI Move", medium_font, TEXT_COLOR, button_color)

    reset_button_rect = pygame.Rect((2 / 3) * width + BOARD_PADDING, (1 / 3) * height + 90, (width / 3) - BOARD_PADDING * 2, 50)
    if reset_button_rect.collidepoint(mouse_pos):
        button_color = BUTTON_HOVER_COLOR
    else:
        button_color = BUTTON_COLOR
    draw_button(reset_button_rect, "Reset", medium_font, TEXT_COLOR, button_color)

    status_text = "Lost" if lost else "Won" if game.mines == flags else ""
    draw_text(status_text, medium_font, TEXT_COLOR, ((5 / 6) * width, (2 / 3) * height))

    move = None
    left, _, right = pygame.mouse.get_pressed()

    if right and not lost:
        mouse_pos = pygame.mouse.get_pos()
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if cells[i][j].collidepoint(mouse_pos) and (i, j) not in revealed:
                    if (i, j) in flags:
                        flags.remove((i, j))
                    else:
                        flags.add((i, j))
                    time.sleep(0.2)

    elif left:
        mouse_pos = pygame.mouse.get_pos()

        if ai_button_rect.collidepoint(mouse_pos) and not lost:
            move = ai.mace4_wrapper() or ai.mace4_move()
            if move is None:
                flags = ai.mines.copy()
                print("No moves left to make.")
            else:
                print("AI making move.")
            time.sleep(0.2)

        elif reset_button_rect.collidepoint(mouse_pos):
            game = Minesweeper(height=HEIGHT, width=WIDTH, mines=MINES)
            ai = MinesweeperAI(height=HEIGHT, width=WIDTH)
            revealed = set()
            flags = set()
            lost = False
            continue

        elif not lost:
            for i in range(HEIGHT):
                for j in range(WIDTH):
                    if cells[i][j].collidepoint(mouse_pos) and (i, j) not in flags and (i, j) not in revealed:
                        move = (i, j)

    if move:
        if game.is_mine(move):
            lost = True
        else:
            nearby = game.nearby_mines(move)
            revealed.add(move)
            ai.add_knowledge(move, nearby)

    pygame.display.flip()