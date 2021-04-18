#!/usr/bin/env python
"""A simple mod of SkiFree"""

# Source code taken from Warren Sande at
# http://www.manning-source.com/books/sande/All_Files_By_Chapter/hw_ch10_code/skiing_game.py
# Released under the MIT license http://www.opensource.org/licenses/mit-license.php

import random
import sys

import pygame

# TODO 0) fix esc problem
# TODO 1) make esc in game go to start screen and make message to say appear when player stops moving
# TODO 2) remove all/most global variables
# TODO 3) copy classes to other files
# TODO 4) make the map rendering relative to screen size to make tree density even on bigger screens
# TODO 5) clean up code and start screen layout
# TODO 6) display on start screen last score and leader board
# TODO 7) introduce difficulty constant


global start_screen_displayed
global player_name
global obstacles

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

INITIAL_GAP = 640
COLS_AND_ROWS = 30

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

        if not (self.is_disabled and self.is_disabled()):
            if event.type == pygame.MOUSEMOTION:
                self.hovered = self.rect.collidepoint(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.hovered:
                    if self.command:
                        self.command()


class SkierClass(pygame.sprite.Sprite):

    def __init__(self, screen):
        self.screen_width = screen.get_width
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/skier_down.png")
        self.rect = self.image.get_rect()
        self.rect.center = [320, 100]
        self.angle = 0
        self.downhill_speed = 6
        self.skier_speed = [0, self.downhill_speed]

    def turn(self, direction):
        self.angle = self.angle + direction
        if self.angle < -2: self.angle = -2
        if self.angle > 2: self.angle = 2
        center = self.rect.center
        self.image = pygame.image.load(skier_images[self.angle])
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.update_speed()

    def move(self):
        if self.skier_speed[1] > 0:
            self.rect.centerx = self.rect.centerx + self.skier_speed[0]
            if self.rect.left < 0:  self.rect.left = 0
            if self.rect.right > self.screen_width(): self.rect.right = self.screen_width()

    def slow_down(self):
        self.downhill_speed -= 3
        self.update_speed()

    def speed_up(self):
        self.downhill_speed += 3
        self.update_speed()

    def update_speed(self):
        if self.downhill_speed < 0: self.downhill_speed = 0
        if self.downhill_speed > 32: self.downhill_speed = 32
        self.skier_speed = [self.angle * self.downhill_speed / 6, self.downhill_speed - abs(self.angle) * 2]
        if self.skier_speed[1] < 0: self.skier_speed[1] = 0


class ObstacleClass(pygame.sprite.Sprite):

    def __init__(self, image_file, location, obstacle_type):
        pygame.sprite.Sprite.__init__(self)
        self.image_file = image_file
        self.image = pygame.image.load(image_file)
        self.location = location
        self.rect = self.image.get_rect()
        self.rect.center = location
        self.type = obstacle_type

    def update(self, skier_speed):
        self.rect.centery -= skier_speed[1]
        if self.rect.centery < -32:
            self.kill()


def main():
    global obstacles
    pygame.init()
    display_info = pygame.display.Info()
    screen = pygame.display.set_mode(
        size=(int(display_info.current_w * .75), int(display_info.current_h * .75)),
        flags=pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE
    )
    start_screen(pygame.time.Clock(), screen)


def start_screen(clock, screen):
    global start_screen_displayed
    global player_name
    player_name = ""
    font = pygame.font.Font(None, 30)
    start_button = Button("start", 200, 50, 100, 50, close_start_screen, player_name_not_entered)
    player_input_box = InputBox(100, 100, 100, 32, "", record_player)

    start_screen_displayed = True
    while start_screen_displayed:

        # --- events ---

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_RETURN and not player_name_not_entered():
                    close_start_screen()

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

    game(clock, screen)


def record_player(name):
    global player_name
    player_name = name


def player_name_not_entered():
    global player_name
    return len(player_name) == 0


def close_start_screen():
    global start_screen_displayed
    start_screen_displayed = False


def game(clock, screen):
    global player_name
    global obstacles
    skier = SkierClass(screen)
    obstacles = pygame.sprite.Group()
    map_position = 0
    score = 0
    create_map(screen)

    game_running = True
    while game_running:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    start_screen(clock, screen)
                    break
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    skier.turn(-1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    skier.turn(1)
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    skier.slow_down()
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    skier.speed_up()
        skier.move()

        map_position += skier.skier_speed[1]

        if map_position >= INITIAL_GAP:
            create_map(screen)
            map_position = 0

        hit = pygame.sprite.spritecollide(skier, obstacles, False)
        if hit:
            if hit[0].type == "tree":
                skier.image = pygame.image.load("images/skier_crash.png")
                animate(skier, screen, score)
                pygame.time.delay(500)
                return
            elif hit[0].type == "flag":
                score += 10
                hit[0].kill()

        obstacles.update(skier.skier_speed)
        animate(skier, screen, score)


def create_map(screen):
    global obstacles
    locations = []
    for i in range(int(pygame.display.Info().current_w/70)):
        x = random.randint(1, COLS_AND_ROWS - 1) * (screen.get_width() / COLS_AND_ROWS)
        y = (random.randint(0, COLS_AND_ROWS) * screen.get_height() / COLS_AND_ROWS) + INITIAL_GAP
        location = [x, y]
        if not (location in locations):
            locations.append(location)
            if random.choice(["tree", "flag"]) == "tree":
                obstacles.add(ObstacleClass("images/skier_tree.png", location, "tree"))
            else:
                obstacles.add(ObstacleClass("images/skier_flag.png", location, "flag"))


def animate(skier, screen, score):
    font = pygame.font.Font(None, 30)
    screen.fill([255, 255, 255])
    obstacles.draw(screen)
    screen.blit(skier.image, skier.rect)
    screen.blit(font.render(player_name + " Score: " + str(score), True, (0, 0, 0)), [10, 10])
    pygame.display.flip()


def display_high_scores(clock, font, screen, score):
    screen.fill([255, 255, 255])
    game_over = font.render("Game Over!", 1, (0, 0, 0))
    scores_table = [
        ["Andrew", 10],
        ["James", 100]
    ]
    for i in range(len(scores_table)):
        high_player = "{}. {:.<100}".format(i + 1, scores_table[i][0])
        high_score = "{}  ".format(scores_table[i][1])
        high_player_surf = font.render(high_player, 1, (0, 0, 0))
        high_score_surf = font.render(high_score, 1, (0, 0, 0), (255, 255, 255))
        screen.blit(high_player_surf, [20, 250 + 50 * i])
        screen.blit(high_score_surf, [640 - high_score_surf.get_width(), 250 + 50 * i])
    table_header = font.render("High Scores:", 1, (0, 0, 0))
    screen.blit(table_header, [20, 170])
    screen.blit(font.render(player_name + " Score: " + str(score), True, (0, 0, 0)), [20, 70])
    screen.blit(game_over, [20, 20])
    pygame.display.flip()
    while True:
        clock.tick(20)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()


if __name__ == "__main__":
    main()
    pygame.quit()
