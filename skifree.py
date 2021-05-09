#!/usr/bin/env python
"""A simple mod of SkiFree"""

# Source code inspired by Warren Sande at
# http://www.manning-source.com/books/sande/All_Files_By_Chapter/hw_ch10_code/skiing_game.py
# Released under the MIT license http://www.opensource.org/licenses/mit-license.php

import random
import pygame


# TODO 1) make esc in game go to start screen and make message to say appear when player stops moving
# TODO 2) make the map rendering relative to screen size to make tree density even on bigger screens
# TODO 3) clean up code and start screen layout
# TODO 4) display on start screen last score and leader board
# TODO 5) introduce difficulty constant


class InputBox:

    def __init__(self, x, y, w, h, text='', callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.input_box_color_inactive = pygame.Color('lightskyblue3')
        self.input_box_color_active = pygame.Color('dodgerblue2')
        self.color = self.input_box_color_inactive
        self.text = text
        self.callback = callback
        self.txt_surface = pygame.font.Font(None, 32).render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            self.active = self.rect.collidepoint(event.pos)

            # Change the current color of the input box.
            self.color = self.input_box_color_active if self.active else self.input_box_color_inactive
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
        self.image_normal.fill((0, 255, 0))

        self.image_hovered = pygame.Surface((width, height))
        self.image_hovered.fill((255, 0, 0))

        self.image_disabled = pygame.Surface((width, height))
        self.image_disabled.fill((127, 127, 127))

        self.image = self.image_normal
        self.rect = self.image.get_rect()

        font = pygame.font.Font('freesansbold.ttf', 15)

        text_image = font.render(text, True, (255, 255, 255))
        text_rect = text_image.get_rect(center=self.rect.center)

        self.image_normal.blit(text_image, text_rect)
        self.image_hovered.blit(text_image, text_rect)
        self.image_disabled.blit(font.render(text, True, (191, 191, 191)), text_rect)

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
        self.skier_images = ["images/skier_down.png",
                             "images/skier_right1.png",
                             "images/skier_right2.png",
                             "images/skier_left2.png",
                             "images/skier_left1.png"]
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
        self.image = pygame.image.load(self.skier_images[self.angle])
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


class StartScreen:
    def __init__(self, clock, screen):
        self.clock = clock
        self.screen = screen
        self.player_name = ""
        self.font = pygame.font.Font("seguisym.ttf", 20)
        self.start_button = Button("start", 200, 50, 100, 50, self.launch_game, self.player_name_not_entered)
        self.player_input_box = InputBox(100, 100, 100, 32, "", self.record_player)

    def open(self):
        while True:

            # --- events ---

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_RETURN and not self.player_name_not_entered():
                        self.launch_game()

                # --- objects events ---

                self.start_button.handle_event(event)
                self.player_input_box.handle_event(event)

            # --- updates ---

            self.start_button.update()
            self.player_input_box.update()

            # --- draws ---

            self.screen.fill((255, 255, 255))

            text = self.font.render("How to play:", True, (0, 0, 0))
            instructions_x_position = 500
            instructions_y_position = 160
            instructions_line_spacing = 30
            self.screen.blit(text, [instructions_x_position, instructions_y_position])
            text = self.font.render("use a/d or ←/→ to turn", True, (0, 0, 0))
            self.screen.blit(text, [instructions_x_position, instructions_y_position + instructions_line_spacing])
            text = self.font.render("use w/s or ↑/↓ to control speed", True, (0, 0, 0))
            self.screen.blit(text, [instructions_x_position, instructions_y_position + 2 * instructions_line_spacing])
            text = self.font.render("slow down to a stop to pause", True, (0, 0, 0))
            self.screen.blit(text, [instructions_x_position, instructions_y_position + 3 * instructions_line_spacing])
            text = self.font.render("use esc to exit", True, (0, 0, 0))
            self.screen.blit(text, [instructions_x_position, instructions_y_position + 4 * instructions_line_spacing])

            self.start_button.draw(self.screen)
            self.player_input_box.draw(self.screen)

            pygame.display.update()

    def launch_game(self):
        GameScreen(self.clock, self.screen, self.player_name).open()

    def record_player(self, name):
        self.player_name = name

    def player_name_not_entered(self):
        return len(self.player_name) == 0


class GameScreen:
    def __init__(self, clock, screen, player_name):
        self.clock = clock
        self.screen = screen
        self.player_name = player_name
        self.skier = SkierClass(screen)
        self.obstacles = pygame.sprite.Group()
        self.map_position = 0
        self.score = 0
        self.font = pygame.font.Font(None, 30)
        self.initial_gap = 640
        self.cols_and_rows = 30
        
    def open(self):

        self.create_map()

        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return self.score
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.skier.turn(-1)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.skier.turn(1)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.skier.slow_down()
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.skier.speed_up()
            self.skier.move()

            self.map_position += self.skier.skier_speed[1]

            if self.map_position >= self.initial_gap:
                self.create_map()
                self.map_position = 0

            hit = pygame.sprite.spritecollide(self.skier, self.obstacles, False)
            if hit:
                if hit[0].type == "tree":
                    self.skier.image = pygame.image.load("images/skier_crash.png")
                    self.animate()
                    pygame.time.delay(500)
                    return self.score
                elif hit[0].type == "flag":
                    self.score += 10
                    hit[0].kill()

            self.obstacles.update(self.skier.skier_speed)
            self.animate()

    def create_map(self):
        locations = []
        for i in range(int(pygame.display.Info().current_w / 70)):
            x = random.randint(1, self.cols_and_rows - 1) * (self.screen.get_width() / self.cols_and_rows)
            y = (random.randint(0, self.cols_and_rows) * self.screen.get_height() / self.cols_and_rows) + self.initial_gap
            location = [x, y]
            if not (location in locations):
                locations.append(location)
                if random.choice(["tree", "flag"]) == "tree":
                    self.obstacles.add(ObstacleClass("images/skier_tree.png", location, "tree"))
                else:
                    self.obstacles.add(ObstacleClass("images/skier_flag.png", location, "flag"))

    def animate(self):
        self.screen.fill([255, 255, 255])
        self.obstacles.draw(self.screen)
        self.screen.blit(self.skier.image, self.skier.rect)
        self.screen.blit(self.font.render(self.player_name + " Score: " + str(self.score), True, (0, 0, 0)), [10, 10])
        pygame.display.flip()


def main():
    pygame.init()
    display_info = pygame.display.Info()
    screen = pygame.display.set_mode(
        size=(int(display_info.current_w * .75), int(display_info.current_h * .75)),
        flags=pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE
    )
    StartScreen(pygame.time.Clock(), screen).open()


if __name__ == "__main__":
    main()
    pygame.quit()
