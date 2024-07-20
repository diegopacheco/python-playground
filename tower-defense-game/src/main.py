import pygame
import sys
import math
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

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
            # Or handle enemy reaching the end
            self.path_index = 0  

    def draw(self, screen):
        screen.blit(self.image, self.pos)

class Player:
    def __init__(self, pos):
        self.pos = [100, 100]
        self.size = 30
        self.color = (0, 0, 255)
        self.bullets = []
        self.image = pygame.image.load('assets/player.png')
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect(topleft=(self.pos[0], self.pos[1]))

    def draw(self, screen):
        screen.blit(self.image, self.pos)
        for bullet in self.bullets:
            bullet.draw(screen)

    def move(self, direction):
        if direction == "UP":
            new_pos = (self.pos[0], max(0, self.pos[1] - 5))
        elif direction == "DOWN":
            # Subtract self.size to ensure the bottom edge of the player does not go out of bounds
            new_pos = (self.pos[0], min(SCREEN_HEIGHT - self.size, self.pos[1] + 5))
        elif direction == "LEFT":
            new_pos = (max(0, self.pos[0] - 5), self.pos[1])
        elif direction == "RIGHT":
            # Subtract self.size to ensure the right edge of the player does not go out of bounds
            new_pos = (min(SCREEN_WIDTH - self.size, self.pos[0] + 5), self.pos[1])
        # Update position if within bounds
        self.pos = new_pos
        self.rect.topleft = self.pos
    
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


class Game:
    def __init__(self):
        pygame.init()
        self.ENEMY_PATH = [(100, 100), (700, 100), (700, 500), (100, 500)]
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.bullets = []
        self.remaining_bullets = []
        self.enemies = []
        self.score = 0
        self.life = 100

        self.player = Player(( SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.enemy_path = [(100, 100), (200, 200), (300, 300)]
        self.enemy = Enemy(self.enemy_path)
        self.enemies.append(self.enemy)

        self.key_up = False
        self.key_down = False
        self.key_left = False
        self.key_right = False

        self.running = True

    def check_bullet_collisions(self,bullets, enemy):
        for bullet in bullets:
            if enemy.rect.colliderect(bullet.rect):
                enemy.health -= 50
                bullets.remove(bullet)
                if enemy.health <= 0:
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                        return True
        return False

    def check_collision(self, player, enemy):
        return player.rect.colliderect(enemy.rect)     

    def create_enemy(self):
        # ramdon generate 3 valid enemy paths
        enemy_paths = []
        for i in range(3):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            enemy_paths.append([x,y])
        new_enemy = Enemy(self.enemy_path)
        
        # Add the new enemy to the enemies list
        self.enemies.append(new_enemy)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.key_up = True
                    elif event.key == pygame.K_DOWN:
                        self.key_down = True
                    elif event.key == pygame.K_LEFT:
                        self.key_left = True
                    elif event.key == pygame.K_RIGHT:
                        self.key_right = True
                    elif event.key == pygame.K_SPACE:
                        self.player.shoot()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.key_up = False
                    elif event.key == pygame.K_DOWN:
                        self.key_down = False
                    elif event.key == pygame.K_LEFT:
                        self.key_left = False
                    elif event.key == pygame.K_RIGHT:
                        self.key_right = False

            # Game logic updates
            # Clear screen with black background
            self.screen.fill((0, 0, 0))  

            # Move the player based on key states
            if self.key_up:
                self.player.move("UP")
            if self.key_down:
                self.player.move("DOWN")
            if self.key_left:
                self.player.move("LEFT")
            if self.key_right:
                self.player.move("RIGHT")

            # Bullets move and draw
            for bullet in self.player.bullets[:]:
                bullet.move()
                if bullet.pos[0] < 0 or bullet.pos[0] > SCREEN_WIDTH or bullet.pos[1] < 0 or bullet.pos[1] > SCREEN_HEIGHT:
                    self.player.bullets.remove(bullet)  # Remove the bullet if it's out of bounds
                    continue  # Skip the rest of the loop for this bullet
                bullet.draw(self.screen) 
                for enemy in self.enemies[:]:
                    if self.check_bullet_collisions(self.player.bullets, enemy):
                        self.score += 10
                        # ramon 1/9 chances creates 2 enmies
                        if random.randint(1, 9) == 1:
                            self.create_enemy()
                        self.create_enemy()

            # Draw the enemy and player
            for enemy in self.enemies:
                enemy.move()
                enemy.draw(self.screen)
                if self.check_collision(self.player, enemy):
                    self.life -= 1
                    if self.life <= 0:
                        game_over_text = font.render('Game Over', True, (255, 0, 0))
                        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                        pygame.display.update()
                        pygame.time.wait(2000)
                        self.running = False
                        break  
            self.player.draw(self.screen)

            # Display the score
            font = pygame.font.Font(None, 36)
            text = font.render(f'Score: {self.score}', True, (255, 255, 255))
            self.screen.blit(text, (10, 10))

            # Display the life
            font = pygame.font.Font(None, 36)
            text = font.render(f'Life: {self.life}', True, (0, 255, 0))
            self.screen.blit(text, (680, 10))

            # Game Render
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()