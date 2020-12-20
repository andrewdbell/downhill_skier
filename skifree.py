#!/usr/bin/env python
"""A simple mod of SkiFree"""

# Source code taken from Warren Sande at
# http://www.manning-source.com/books/sande/All_Files_By_Chapter/hw_ch10_code/skiing_game.py
# Released under the MIT license http://www.opensource.org/licenses/mit-license.php

import os
import pygame
import random
import sys
import urllib

# TODO 1) prompt user for their name
# TODO 2) show start button
# TODO 3) save leaderboard
# TODO 4) make the screen dynamically full size
# TODO 0) introduce difficulty constant

global start_screen_running

try:
    if os.environ["USERNAME"]:
        player = os.environ["USERNAME"]
    else:
        player = os.environ["LOGNAME"]
except KeyError:
    player = os.environ["LOGNAME"]

# === CONSTANTS === (UPPER_CASE names)

skier_images = ["images/skier_down.png",
                "images/skier_right1.png",
                "images/skier_right2.png",
                "images/skier_left2.png",
                "images/skier_left1.png"]

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 1240
SCREEN_HEIGHT = 600


# === CLASSES === (CamelCase names)


class Button():
    def __init__(self, text, x=0, y=0, width=100, height=50, command=None):

        self.text = text
        self.command = command

        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(GREEN)

        self.image_hovered = pygame.Surface((width, height))
        self.image_hovered.fill(RED)

        self.image = self.image_normal
        self.rect = self.image.get_rect()

        font = pygame.font.Font('freesansbold.ttf', 15)

        text_image = font.render(text, True, WHITE)
        text_rect = text_image.get_rect(center=self.rect.center)

        self.image_normal.blit(text_image, text_rect)
        self.image_hovered.blit(text_image, text_rect)

        # you can't use it before `blit`
        self.rect.topleft = (x, y)

        self.hovered = False
        # self.clicked = False

    def update(self):

        if self.hovered:
            self.image = self.image_hovered
        else:
            self.image = self.image_normal

    def draw(self, surface):

        surface.blit(self.image, self.rect)

    def handle_event(self, event):

        global start_screen_running

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                print('Clicked:', self.text)
                if self.command:
                    self.command()


class SkierClass(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/skier_down.png")
        self.rect = self.image.get_rect()
        self.rect.center = [320, 100]
        self.angle = 0

    def turn(self, direction):
        self.angle = self.angle + direction
        if self.angle < -2: self.angle = -2
        if self.angle > 2: self.angle = 2
        center = self.rect.center
        self.image = pygame.image.load(skier_images[self.angle])
        self.rect = self.image.get_rect()
        self.rect.center = center
        speed = [self.angle, 6 - abs(self.angle) * 2]
        return speed

    def move(self, speed):
        self.rect.centerx = self.rect.centerx + speed[0]
        if self.rect.centerx < 20:  self.rect.centerx = 20
        if self.rect.centerx > 620: self.rect.centerx = 620


class ObstacleClass(pygame.sprite.Sprite):
    def __init__(self, image_file, location, type):
        pygame.sprite.Sprite.__init__(self)
        self.image_file = image_file
        self.image = pygame.image.load(image_file)
        self.location = location
        self.rect = self.image.get_rect()
        self.rect.center = location
        self.type = type

    def update(self):
        self.rect.centery -= speed[1]
        if self.rect.centery < -32:
            self.kill()


def create_map():
    global obstacles
    locations = []
    for i in range(10):
        row = random.randint(0, 9)
        col = random.randint(0, 9)
        location = [col * 64 + 20, row * 64 + 20 + 640]
        if not (location in locations):
            locations.append(location)
            type = random.choice(["tree", "flag"])
            if type == "tree":
                img = "images/skier_tree.png"
            elif type == "flag":
                img = "images/skier_flag.png"
            obstacle = ObstacleClass(img, location, type)
            obstacles.add(obstacle)


def animate():
    screen.fill([255, 255, 255])
    obstacles.draw(screen)
    screen.blit(skier.image, skier.rect)
    screen.blit(score_text, [10, 10])
    pygame.display.flip()


def main():
    global screen
    global obstacles
    global skier
    global score_text
    global speed
    global has_quit
    pygame.init()
    screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    has_quit = False
    start_screen(clock, screen)
    game(clock, screen)


def game(clock, screen):
    global skier, speed, obstacles, score_text, has_quit
    skier = SkierClass()
    speed = [0, 6]
    obstacles = pygame.sprite.Group()
    map_position = 0
    points = 0
    create_map()
    font = pygame.font.Font(None, 30)

    running = True
    while running and not has_quit:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                has_quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    has_quit = True
                elif event.key == pygame.K_LEFT:
                    speed = skier.turn(-1)
                elif event.key == pygame.K_RIGHT:
                    speed = skier.turn(1)
        skier.move(speed)

        map_position += speed[1]

        if map_position >= 640:
            create_map()
            map_position = 0

        hit = pygame.sprite.spritecollide(skier, obstacles, False)
        if hit:
            if hit[0].type == "tree":
                skier.image = pygame.image.load("images/skier_crash.png")
                animate()
                pygame.time.delay(1000)
                screen.fill([255, 255, 255])
                game_over = font.render("Game Over!", 1, (0, 0, 0))
                data = urllib.urlencode(dict(player=player, score=points))
                req = urllib.Request(url="http://www.thefirstmimzy.com/skifree.php", data=data)
                f = urllib.urlopen(req)
                scores_page = f.read()
                scores_rows = scores_page.strip(",").split(",")
                scores_table = []
                for row in scores_rows:
                    scores_table.append(row.split(":"))
                for i in range(len(scores_table)):
                    high_player = "{}. {:.<100}".format(i + 1, scores_table[i][0])
                    high_score = "{}  ".format(scores_table[i][1])
                    high_player_surf = font.render(high_player, 1, (0, 0, 0))
                    high_score_surf = font.render(high_score, 1, (0, 0, 0), (255, 255, 255))
                    screen.blit(high_player_surf, [20, 250 + 50 * i])
                    screen.blit(high_score_surf, [640 - high_score_surf.get_width(), 250 + 50 * i])
                table_header = font.render("High Scores:", 1, (0, 0, 0))
                screen.blit(table_header, [20, 170])
                screen.blit(score_text, [20, 70])
                screen.blit(game_over, [20, 20])
                pygame.display.flip()
                while True:
                    clock.tick(20)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT: sys.exit()
            elif hit[0].type == "flag":
                points += 10
                hit[0].kill()

        obstacles.update()
        score_text = font.render("Score: " + str(points), 1, (0, 0, 0))
        animate()


def close_start_screen():
    global start_screen_running
    start_screen_running = False


def start_screen(clock, screen):
    global has_quit
    global start_screen_running
    font = pygame.font.Font(None, 30)
    start_button = Button("start", 200, 50, 100, 50, close_start_screen)

    start_screen_running = True
    while start_screen_running and not has_quit:

        # --- events ---

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                has_quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    has_quit = True

            # --- objects events ---

            start_button.handle_event(event)

        # --- updates ---

        start_button.update()

        # --- draws ---

        screen.fill(WHITE)

        text = font.render("press Esc to exit", True, (0, 0, 0))
        screen.blit(text, [150, 150])

        start_button.draw(screen)

        pygame.display.update()

        # --- FPS ---

        clock.tick(25)


if __name__ == "__main__":
    main()
    pygame.quit()