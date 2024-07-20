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
        self.image = pygame.image.load('assets/enemy.png')
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.rect = pygame.Surface((self.size, self.size)).get_rect(topleft=self.pos)

    def move(self):
        if self.path_index < len(self.path) - 1:
            target_pos = self.path[self.path_index + 1]
            direction = (target_pos[0] - self.pos[0], target_pos[1] - self.pos[1])
            distance = math.sqrt(direction[0]**2 + direction[1]**2)
            direction = (direction[0] / distance, direction[1] / distance)
            self.pos = (self.pos[0] + direction[0] * self.speed, self.pos[1] + direction[1] * self.speed)
            self.rect.topleft = self.pos
            # Check if reached the next point
            if distance < self.speed:
                self.path_index += 1
        else:
            # Reset to start or remove enemy
            self.path_index = 0  # Or handle enemy reaching the end

    def draw(self, screen):
        screen.blit(self.image, self.pos)
        #pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.size, self.size))

class Player:
    def __init__(self, pos):
        #self.pos = pos
        self.pos = [100, 100]
        self.size = 30
        self.color = (0, 0, 255)
        self.bullets = []
        self.image = pygame.image.load('assets/player.png')
        self.image = pygame.transform.scale(self.image, (50, 50))

    def draw(self, screen):
        #pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.size, self.size))
        #pygame.draw.rect(screen, self.color, (self.pos[0], self.pos[1], self.size, self.size))
        screen.blit(self.image, self.pos)
        for bullet in self.bullets:  # Draw each bullet
            bullet.draw(screen)

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
        new_bullet = Bullet(self.pos[0] + self.size // 2, self.pos[1])
        self.bullets.append(new_bullet)

class Bullet:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.radius = 5 
        self.size = 10
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect(topleft=(x, y))

    def move(self):
        self.pos[1] -= 10
        self.rect.y = self.pos[1]

    def draw(self, screen):
        pygame.draw.circle(screen, (0, 255, 0), self.pos, self.radius)


def check_bullet_collisions(bullets, enemy):
    for bullet in bullets:
        if enemy.rect.colliderect(bullet.rect):
            enemy.health -= 50
            bullets.remove(bullet)
            if enemy.health <= 0:
                if enemy in enemies:
                    enemies.remove(enemy)
                return True

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WINDOW_WIDTH = SCREEN_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
ENEMY_PATH = [(100, 100), (700, 100), (700, 500), (100, 500)]
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

bullets = []
remaining_bullets = []
enemies = []

player = Player((50, 50))
enemy_path = [(100, 100), (200, 200), (300, 300)]  # Example path
enemy = Enemy(enemy_path)
enemies.append(enemy)

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
            elif event.key == pygame.K_SPACE:
                player.shoot()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                key_up = False
            elif event.key == pygame.K_DOWN:
                key_down = False
            elif event.key == pygame.K_LEFT:
                key_left = False
            elif event.key == pygame.K_RIGHT:
                key_right = False

    # Game logic updates
    # Clear screen with black background
    screen.fill((0, 0, 0))  

    for bullet in player.bullets[:]:
        bullet.move()
        if bullet.pos[0] < 0 or bullet.pos[0] > SCREEN_WIDTH or bullet.pos[1] < 0 or bullet.pos[1] > SCREEN_HEIGHT:
            player.bullets.remove(bullet)  # Remove the bullet if it's out of bounds
            continue  # Skip the rest of the loop for this bullet
        bullet.draw(screen) 
        for enemy in enemies[:]:
            if check_bullet_collisions([bullet], enemy):
                enemies.remove(enemy)
                player.bullets.remove(bullet)
                break

    # Draw remaining enemies
    for enemy in enemies:
        enemy.draw(screen)

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
    enemy.draw(screen) 
    player.draw(screen)
    
    # Game Update
    # check for collisions, etc.

    # Game Render
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()