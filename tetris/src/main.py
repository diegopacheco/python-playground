import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)

# Shapes of tetrominoes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

# Tetromino colors
COLORS = [CYAN, YELLOW, PURPLE, BLUE, ORANGE, GREEN, RED]

# Game board
BOARD_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
BOARD_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Tetris')

clock = pygame.time.Clock()

def new_piece():
    shape = random.choice(SHAPES)
    color = COLORS[SHAPES.index(shape)]
    return {
        'shape': shape,
        'color': color,
        'x': BOARD_WIDTH // 2 - len(shape[0]) // 2,
        'y': 0
    }

def draw_board(board):
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            pygame.draw.rect(screen, board[y][x], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

def check_collision(board, piece, x, y):
    for cy, row in enumerate(piece['shape']):
        for cx, cell in enumerate(row):
            if cell:
                # Board boundaries check
                if x + cx < 0 or x + cx >= BOARD_WIDTH or y + cy >= BOARD_HEIGHT:
                    return True
                # Collision with existing blocks
                if y + cy >= 0 and board[y + cy][x + cx] != BLACK:
                    return True
    return False

def rotate_piece(piece):
    new_shape = list(zip(*piece['shape'][::-1]))
    return {'shape': new_shape, 'color': piece['color'], 'x': piece['x'], 'y': piece['y']}

def main():
    board = [[BLACK for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
    piece = new_piece()
    score = 0
    fall_speed = 0.5  # Adjust this value to control falling speed
    last_fall_time = pygame.time.get_ticks()

    while True:
        screen.fill(BLACK)
        draw_board(board)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not check_collision(board, piece, piece['x'] - 1, piece['y']):
                        piece['x'] -= 1
                if event.key == pygame.K_RIGHT:
                    if not check_collision(board, piece, piece['x'] + 1, piece['y']):
                        piece['x'] += 1
                if event.key == pygame.K_DOWN:
                    if not check_collision(board, piece, piece['x'], piece['y'] + 1):
                        piece['y'] += 1
                if event.key == pygame.K_UP:
                    rotated = rotate_piece(piece)
                    if not check_collision(board, rotated, piece['x'], piece['y']):
                        piece = rotated

        # Piece falling logic
        current_time = pygame.time.get_ticks()
        if current_time - last_fall_time > 1000 * fall_speed:  # Convert fall_speed to milliseconds
            if not check_collision(board, piece, piece['x'], piece['y'] + 1):
                piece['y'] += 1
            else:
                # Land the piece
                for cy, row in enumerate(piece['shape']):
                    for cx, cell in enumerate(row):
                        if cell:
                            board[piece['y'] + cy][piece['x'] + cx] = piece['color']

                # Clear lines and update score
                lines_cleared = 0
                for y in range(BOARD_HEIGHT - 1, -1, -1):
                    if all(board[y]):
                        del board[y]
                        board.insert(0, [BLACK for _ in range(BOARD_WIDTH)])
                        lines_cleared += 1
                score += lines_cleared ** 2

                # Get new piece
                piece = new_piece()
                if check_collision(board, piece, piece['x'], piece['y']):
                    print("Game Over!")
                    return

            last_fall_time = current_time

        # Draw the current piece
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, piece['color'],
                                     (BLOCK_SIZE * (piece['x'] + x), BLOCK_SIZE * (piece['y'] + y),
                                      BLOCK_SIZE, BLOCK_SIZE))

        pygame.display.flip()
        clock.tick(60)  # Limit frame rate to 60 FPS

if __name__ == "__main__":
    main()