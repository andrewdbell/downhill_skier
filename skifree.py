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

# TODO 1) fix disabled text, enter clicks start
# TODO 2) copy classes to other files
# TODO 2.5) clean up code and start screen layout
# TODO 3) save leaderboard
# TODO 4) make the screen dynamically full size
# TODO 5) introduce difficulty constant

global start_screen_running
global player

# === CONSTANTS === (UPPER_CASE names)

skier_images = ["images/skier_down.png",
                "images/skier_right1.png",
                "images/skier_right2.png",
                "images/skier_left2.png",
                "images/skier_left1.png"]

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (127, 127, 127)
LIGHT_GREY = (191, 191, 191)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 1240
SCREEN_HEIGHT = 600

INPUT_BOX_COLOR_INACTIVE = pygame.Color('lightskyblue3')
INPUT_BOX_COLOR_ACTIVE = pygame.Color('dodgerblue2')


# === CLASSES === (CamelCase names)

class InputBox:

    def __init__(self, x, y, w, h, text='', callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = INPUT_BOX_COLOR_INACTIVE
        self.text = text
        self.callback = callback
        self.txt_surface = pygame.font.Font(None, 32).render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            self.active = self.rect.collidepoint(event.pos)

            # Change the current color of the input box.
            self.color = INPUT_BOX_COLOR_ACTIVE if self.active else INPUT_BOX_COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                if self.callback:
                    self.callback(self.text)
                # Re-render the text.
                self.txt_surface = pygame.font.Font(None, 32).render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)


class Button:

    def __init__(self, text, x=0, y=0, width=100, height=50, command=None, is_disabled=None):

        self.text = text
        self.command = command
        self.is_disabled = is_disabled

        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(GREEN)

        self.image_hovered = pygame.Surface((width, height))
        self.image_hovered.fill(RED)

        self.image_disabled = pygame.Surface((width, height))
        self.image_disabled.fill(GREY)

        self.image = self.image_normal
        self.rect = self.image.get_rect()

        font = pygame.font.Font('freesansbold.ttf', 15)

        text_image = font.render(text, True, WHITE)
        text_rect = text_image.get_rect(center=self.rect.center)

        self.image_normal.blit(text_image, text_rect)
        self.image_hovered.blit(text_image, text_rect)
        self.image_disabled.blit(font.render(text, True, LIGHT_GREY), text_rect)

        # you can't use it before `blit`
        self.rect.topleft = (x, y)

        self.hovered = False

    def update(self):

        if self.is_disabled and self.is_disabled():
            self.image = self.image_disabled
        elif self.hovered:
            self.image = self.image_hovered
        else:
            self.image = self.image_normal

    def draw(self, surface):

        surface.blit(self.image, self.rect)

    def handle_event(self, event):

        global start_screen_running

        if not (self.is_disabled and self.is_disabled()):
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


def start_screen(clock, screen):
    global has_quit, start_screen_running, player
    player = ""
    font = pygame.font.Font(None, 30)
    start_button = Button("start", 200, 50, 100, 50, close_start_screen, start_button_disabled)
    player_input_box = InputBox(100, 100, 100, 32, "", record_player)

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
            player_input_box.handle_event(event)

        # --- updates ---

        start_button.update()
        player_input_box.update()

        # --- draws ---

        screen.fill(WHITE)

        text = font.render("press Esc to exit", True, (0, 0, 0))
        screen.blit(text, [150, 150])

        start_button.draw(screen)
        player_input_box.draw(screen)

        pygame.display.update()

        # --- FPS ---

        # clock.tick(25)


def record_player(player_name):
    global player
    player = player_name


def start_button_disabled():
    global player
    return len(player) == 0


def close_start_screen():
    global start_screen_running
    start_screen_running = False


def game(clock, screen):
    global skier, speed, obstacles, score_text, has_quit, player
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
        score_text = font.render(player + " Score: " + str(points), 1, (0, 0, 0))
        animate()


if __name__ == "__main__":
    main()
    pygame.quit()
