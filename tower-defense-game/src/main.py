import pygame
import sys
import math

class Enemy:
    def __init__(self, path):
        self.path = path
        self.path_index = 0
        self.pos = self.path[self.path_index]
        self.speed = 2
        self.health = 100
        self.radius = 10 
        self.size = 20
        self.color = (255, 0, 0)

    def move(self):
        if self.path_index < len(self.path) - 1:
            target_pos = self.path[self.path_index + 1]
            direction = (target_pos[0] - self.pos[0], target_pos[1] - self.pos[1])
            distance = math.sqrt(direction[0]**2 + direction[1]**2)
            direction = (direction[0] / distance, direction[1] / distance)
            self.pos = (self.pos[0] + direction[0] * self.speed, self.pos[1] + direction[1] * self.speed)
            # Check if reached the next point
            if distance < self.speed:
                self.path_index += 1
        else:
            # Reset to start or remove enemy
            self.path_index = 0  # Or handle enemy reaching the end

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.size, self.size))

class Player:
    def __init__(self, pos):
        self.pos = pos
        self.size = 30
        self.color = (0, 0, 255)
        self.bullets = []

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.size, self.size))

    def move(self, direction):
        if direction == "UP":
            new_pos = (self.pos[0], max(0, self.pos[1] - 5))
        elif direction == "DOWN":
            # Subtract self.size to ensure the bottom edge of the player does not go out of bounds
            new_pos = (self.pos[0], min(WINDOW_HEIGHT - self.size, self.pos[1] + 5))
        elif direction == "LEFT":
            new_pos = (max(0, self.pos[0] - 5), self.pos[1])
        elif direction == "RIGHT":
            # Subtract self.size to ensure the right edge of the player does not go out of bounds
            new_pos = (min(WINDOW_WIDTH - self.size, self.pos[0] + 5), self.pos[1])
        # Update position if within bounds
        self.pos = new_pos
    
    def shoot(self):
        global bullets
        new_bullet = Bullet((self.pos[0], self.pos[1]))
        bullets.append(new_bullet)

class Bullet:
    def __init__(self, pos):
        self.pos = pos
        self.speed = 10
        self.radius = 5

    def move(self):
        self.pos = (self.pos[0], self.pos[1] - self.speed)

    def draw(self, screen):
        pygame.draw.circle(screen, (0, 255, 0), self.pos, self.radius)

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WINDOW_WIDTH = SCREEN_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
ENEMY_PATH = [(100, 100), (700, 100), (700, 500), (100, 500)]  # Simplified path
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

player = Player((50, 50))
enemy_path = [(100, 100), (200, 200), (300, 300)]  # Example path
enemy = Enemy(enemy_path)
bullets = []

key_up = False
key_down = False
key_left = False
key_right = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                key_up = True
            elif event.key == pygame.K_DOWN:
                key_down = True
            elif event.key == pygame.K_LEFT:
                key_left = True
            elif event.key == pygame.K_RIGHT:
                key_right = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                key_up = False
            elif event.key == pygame.K_DOWN:
                key_down = False
            elif event.key == pygame.K_LEFT:
                key_left = False
            elif event.key == pygame.K_RIGHT:
                key_right = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # Game logic updates
    # Clear screen with black background
    screen.fill((0, 0, 0))  

    for bullet in bullets[:]:
        bullet.move()
        bullet.draw(screen)
        # Remove bullets that go off-screen
        if bullet.pos[1] < -10:
            bullets.remove(bullet)

    # Move the player based on key states
    if key_up:
        player.move("UP")
    if key_down:
        player.move("DOWN")
    if key_left:
        player.move("LEFT")
    if key_right:
        player.move("RIGHT")

    # Draw the enemy and player
    enemy.move()  
    screen.fill((0, 0, 0))
    enemy.draw(screen) 
    player.draw(screen)
    
    # Game Update
    # check for collisions, etc.

    # Game Render
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()