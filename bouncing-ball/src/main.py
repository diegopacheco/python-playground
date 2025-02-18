import pygame
import math
import sys

class Boundary:
    def __init__(self, center_x, center_y, radius):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.angle = 0
        self.rotation_speed = 0.5
        self.points = self._calculate_points()

    def _calculate_points(self):
        points = []
        for i in range(6):
            angle = math.radians(i * 60 + self.angle)
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y + self.radius * math.sin(angle)
            points.append((x, y))
        return points

    def update(self):
        self.angle += self.rotation_speed
        self.points = self._calculate_points()

    def draw(self, screen):
        pygame.draw.polygon(screen, (255, 255, 255), self.points, 2)

class HexagonBall:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.dx = 5
        self.dy = 5
        self.points = self._calculate_points()

    def _calculate_points(self):
        points = []
        for i in range(6):
            angle = i * 60
            x = self.x + self.radius * math.cos(math.radians(angle))
            y = self.y + self.radius * math.sin(math.radians(angle))
            points.append((x, y))
        return points

    def move(self, boundary):
        next_x = self.x + self.dx
        next_y = self.y + self.dy

        # Check collision with boundary
        distance = math.sqrt((next_x - boundary.center_x)**2 + (next_y - boundary.center_y)**2)
        if distance + self.radius > boundary.radius - 10:
            # Reflect the ball
            angle = math.atan2(self.y - boundary.center_y, self.x - boundary.center_x)
            self.dx = -self.dx if abs(math.cos(angle)) > 0.5 else self.dx
            self.dy = -self.dy if abs(math.sin(angle)) > 0.5 else self.dy
        
        self.x += self.dx
        self.y += self.dy
        self.points = self._calculate_points()

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color, self.points)

def main():
    pygame.init()
    width = 800
    height = 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Bouncing Hexagon")
    clock = pygame.time.Clock()

    boundary = Boundary(width//2, height//2, 200)
    ball = HexagonBall(width//2, height//2, 20, (255, 0, 0))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))  # Black background
        
        boundary.update()
        boundary.draw(screen)
        
        ball.move(boundary)
        ball.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()