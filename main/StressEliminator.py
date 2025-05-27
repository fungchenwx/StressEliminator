import pygame
import random

# Bullet sprite
class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_position, direction, speed=10):
        super().__init__()
        self.image = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect(center=start_position)
        self.position = pygame.math.Vector2(start_position)
        self.velocity = direction * speed

    def update(self):
        self.position += self.velocity
        self.rect.center = self.position
        screen_rectangle = pygame.display.get_surface().get_rect()
        if not screen_rectangle.collidepoint(self.position):
            self.kill()


# Player sprite
class Shooter(pygame.sprite.Sprite):
    def __init__(self, start_position, speed=3):
        super().__init__()
        loaded_image = pygame.image.load("assets/Player.png").convert_alpha()
        self.original_image = pygame.transform.scale(loaded_image, (50, 50))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=start_position)
        self.position = pygame.math.Vector2(start_position)
        self.speed = speed

    def update(self):
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.position)

        pressed_keys = pygame.key.get_pressed()
        movement_vector = pygame.math.Vector2(pressed_keys[pygame.K_d] - pressed_keys[pygame.K_a], pressed_keys[pygame.K_s] - pressed_keys[pygame.K_w])
        if movement_vector.length_squared() > 0:
            movement_vector = movement_vector.normalize() * self.speed
            self.position += movement_vector

            window_width, window_height = pygame.display.get_surface().get_size()
            self.position.x = max(0, min(self.position.x, window_width))
            self.position.y = max(0, min(self.position.y, window_height))
            self.rect.center = self.position

    def shoot(self):
        mouse_position = pygame.mouse.get_pos()
        direction_vector = pygame.math.Vector2(mouse_position) - self.position
        if direction_vector.length() > 0:
            direction_vector = direction_vector.normalize()
        return Bullet(self.position, direction_vector)


# Helper sprite
class Helper(pygame.sprite.Sprite):
    def __init__(self, player, offset, image=None, size=40, placeholder_color=(100,100,100)):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.player = player
        self.offset = pygame.math.Vector2(offset)

    def update(self):
        self.rect.center = self.player.position + self.offset

# Enemy sprite
class TextEnemy(pygame.sprite.Sprite):
    WORD_LIST = ["depression", "stress", "quit", "fear", "reject", "anxiety", "doubt", "failure", "loneliness", "guilt"]
    DESIRED_SEPARATION = 40
    SEPARATION_STRENGTH = 1.0

    def __init__(self, start_position, player, enemy_group, speed=1, health=20):
        super().__init__()
        self.player = player
        self.position = pygame.math.Vector2(start_position)
        self.speed = speed
        self.health = health
        self.enemy_group = enemy_group

        chosen_word = random.choice(self.WORD_LIST)
        font = pygame.font.Font(None, 46)
        text_surface = font.render(chosen_word, True, (255,255,255))
        outline_surface = font.render(chosen_word, True, (0,0,0))

        self.image = pygame.Surface((text_surface.get_width()+4, text_surface.get_height()+4), pygame.SRCALPHA)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            self.image.blit(outline_surface, (dx+2, dy+2))
        self.image.blit(text_surface, (2,2))
        self.rect = self.image.get_rect(center=start_position)

    def update(self):
        to_player_vector = self.player.position - self.position
        if to_player_vector.length() > 0:
            self.position += to_player_vector.normalize() * self.speed

        separation_force = pygame.math.Vector2()
        neighbor_count = 0
        for other_enemy in self.enemy_group:
            if other_enemy is self:
                continue
            offset_vector = self.position - other_enemy.position
            distance = offset_vector.length()
            if 0 < distance < self.DESIRED_SEPARATION:
                separation_force += offset_vector.normalize() / distance
                neighbor_count += 1

        if neighbor_count > 0 and separation_force.length() > 0:
            separation_force /= neighbor_count
            self.position += separation_force.normalize() * self.speed * self.SEPARATION_STRENGTH

        self.rect.center = self.position

        if self.health <= 0:
            self.kill()


# Main game loop
def main():
    pygame.init()
    screen_width, screen_height = 1200, 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()

    # Load and scale background
    background = pygame.image.load("assets/Background.png").convert()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    # Load helper images
    helper_size = (40, 40)
    mom_image         = pygame.image.load("assets/Mom.png").convert_alpha()
    dad_image         = pygame.image.load("assets/Dad.png").convert_alpha()
    friend_girl_image = pygame.image.load("assets/Friend_Girl.png").convert_alpha()
    friend_boy_image  = pygame.image.load("assets/Friend_Boy.png").convert_alpha()
    dog_image         = pygame.image.load("assets/Dog.png").convert_alpha()
    cat_image         = pygame.image.load("assets/Cat.png").convert_alpha()

    mom_image         = pygame.transform.scale(mom_image, helper_size)
    dad_image         = pygame.transform.scale(dad_image, helper_size)
    friend_girl_image = pygame.transform.scale(friend_girl_image, helper_size)
    friend_boy_image  = pygame.transform.scale(friend_boy_image, helper_size)
    dog_image         = pygame.transform.scale(dog_image, helper_size)
    cat_image         = pygame.transform.scale(cat_image, helper_size)

    font_large  = pygame.font.Font(None, 64)
    font_medium = pygame.font.Font(None, 48)
    font_small  = pygame.font.Font(None, 32)
    line_height = font_small.get_height() + 5

    reflection_lines = [
        "Congratulations—you made it through!",
        "",
        "Self-Care Tips:",
        " • Talk openly with someone you trust",
        " • Practice deep breathing or meditation",
        " • Take a short walk or get fresh air",
        " • Journal your thoughts and feelings",
        "",
        "If you ever need more help:",
        " • In the US call 988 (Suicide & Crisis Lifeline)",
        " • Crisis Text Line: text HOME to 741741",
        " • NAMI: https://www.nami.org",
        " • Mental Health America: https://mhanational.org",
    ]

    # Game state
    state = 'stage1'
    cutscene_index = 0
    cutscene_start_time = 0
    cutscene_duration = 3000
    cutscene_messages = [
        "You have been overwhelmed...",
        "You were surrounded with negativity...",
        "But don't forget, you can always reach out for help!"
    ]

    # Stage1 enemy spawn
    SPAWN_ENEMY_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ENEMY_EVENT, 1000)
    total_stage1_enemies = 100
    spawned_stage1_count = 0

    # Sprite groups
    all_sprites    = pygame.sprite.Group()
    bullet_sprites = pygame.sprite.Group()
    enemy_sprites  = pygame.sprite.Group()
    helper_sprites = pygame.sprite.Group()

    # Create player
    player = Shooter((screen_width//2, screen_height//2))
    all_sprites.add(player)
    max_player_health = 100
    player_health     = max_player_health
    flash_health_bar  = False

    running = True
    while running:
        current_tick = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Stage1 enemies
            elif event.type == SPAWN_ENEMY_EVENT and state == 'stage1':
                if spawned_stage1_count < total_stage1_enemies:
                    from_edge = random.random() < 0.5
                    if from_edge:
                        spawn_x = random.choice([0, screen_width])
                        spawn_y = random.randint(0, screen_height)
                    else:
                        spawn_x = random.randint(0, screen_width)
                        spawn_y = random.choice([0, screen_height])

                    new_enemy_sprite = TextEnemy((spawn_x, spawn_y), player, enemy_sprites, speed=1, health=10)

                    if not pygame.sprite.spritecollideany(new_enemy_sprite, enemy_sprites):
                        all_sprites.add(new_enemy_sprite)
                        enemy_sprites.add(new_enemy_sprite)
                        spawned_stage1_count += 1
                    else:
                        new_enemy_sprite.kill()
                else:
                    pygame.time.set_timer(SPAWN_ENEMY_EVENT, 0)

            # Shooting
            elif (event.type == pygame.MOUSEBUTTONDOWN and
                  event.button == 1 and state in ('stage1', 'play')):
                bullet_sprite = player.shoot()
                all_sprites.add(bullet_sprite)
                bullet_sprites.add(bullet_sprite)
                for helper_sprite in helper_sprites:
                    helper_origin = helper_sprite.player.position + helper_sprite.offset
                    direction = pygame.math.Vector2(pygame.mouse.get_pos()) - helper_origin
                    if direction.length() > 0:
                        direction = direction.normalize()
                    helper_bullet = Bullet(helper_sprite.rect.center, direction)
                    all_sprites.add(helper_bullet)
                    bullet_sprites.add(helper_bullet)

            # Helper selection
            elif event.type == pygame.KEYDOWN and state == 'helper_select':
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    if event.key == pygame.K_1:      # Family
                        chosen_helpers = (mom_image, dad_image)
                    elif event.key == pygame.K_2:    # Friends
                        chosen_helpers = (friend_girl_image, friend_boy_image)
                    else:                             # Pets
                        chosen_helpers = (dog_image, cat_image)

                    player_health = max_player_health
                    flash_health_bar = False

                    for helper_offset, helper_image in zip([(-60,60),(60,60)], chosen_helpers):
                        helper_sprite = Helper(player, helper_offset, image=helper_image)
                        all_sprites.add(helper_sprite)
                        helper_sprites.add(helper_sprite)

                    # Second wave enemies
                    for _ in range(30):
                        from_edge = random.random() < 0.5
                        if from_edge:
                            spawn_x = random.choice([0, screen_width])
                            spawn_y = random.randint(0, screen_height)
                        else:
                            spawn_x = random.randint(0, screen_width)
                            spawn_y = random.choice([0, screen_height])

                        wave_enemy = TextEnemy(
                            (spawn_x, spawn_y),
                            player,
                            enemy_sprites,
                            speed=1,
                            health=10
                        )
                        all_sprites.add(wave_enemy)
                        enemy_sprites.add(wave_enemy)

                    state = 'play'

        if state == 'stage1' and player_health <= 0:
            state = 'cutscene'
            cutscene_index = 0
            cutscene_start_time = current_tick
            pygame.time.set_timer(SPAWN_ENEMY_EVENT, 0)
            for enemy_sprite in enemy_sprites:
                enemy_sprite.kill()

        if (state == 'cutscene' and current_tick - cutscene_start_time > cutscene_duration * (cutscene_index + 1)):
            cutscene_index += 1
            if cutscene_index >= len(cutscene_messages):
                state = 'helper_select'

        if state in ('stage1', 'play'):
            previous_position = player.position.copy()
            all_sprites.update()

            collided_enemies = pygame.sprite.spritecollide(player, enemy_sprites, False)
            if collided_enemies:
                for enemy_sprite in collided_enemies:
                    enemy_sprite.kill()
                player.position = previous_position
                player.rect.center = previous_position
                flash_health_bar = True
                if state == 'stage1':
                    player_health = max(0, player_health - 10)

            bullet_hits = pygame.sprite.groupcollide(enemy_sprites, bullet_sprites, False, True)
            for enemy_sprite, bullets_list in bullet_hits.items():
                for _ in bullets_list:
                    enemy_sprite.health -= 1

        # Win condition
        if state == 'play' and not enemy_sprites:
            state = 'win'

        # Draw
        screen.blit(background, (0, 0))

        if state == 'stage1':
            enemy_sprites.draw(screen)
            screen.blit(player.image, player.rect)
            bullet_sprites.draw(screen)
            health_percentage = player_health / max_player_health
            pygame.draw.rect(screen, (50,50,50), (10,10,200,20), 2)
            pygame.draw.rect(screen, (30,200,30), (12,12,int((200-4)*health_percentage),16))

        elif state == 'cutscene':
            message_surface = font_medium.render(
                cutscene_messages[cutscene_index], True, (30,30,30)
            )
            screen.blit(
                message_surface,
                message_surface.get_rect(center=(screen_width//2, screen_height//2))
            )

        elif state == 'helper_select':
            prompt_text = "Who do you want to reach out to? 1) Family 2) Friends 3) Pets"
            prompt_surface = font_medium.render(prompt_text, True, (30,30,30))
            screen.blit(prompt_surface, prompt_surface.get_rect(center=(screen_width//2, screen_height//2)))

        elif state == 'play':
            enemy_sprites.draw(screen)
            screen.blit(player.image, player.rect)
            helper_sprites.draw(screen)
            bullet_sprites.draw(screen)
            health_percentage = player_health / max_player_health
            fill_percentage = 1.0 if flash_health_bar else health_percentage
            pygame.draw.rect(screen, (50,50,50), (10,10,200,20), 2)
            pygame.draw.rect(screen, (30,200,30), (12,12, int((200-4) * fill_percentage), 16))
            flash_health_bar = False

        elif state == 'win':
            win_surface = font_large.render("YOU WIN!", True, (0,200,0))
            screen.blit(
                win_surface,
                win_surface.get_rect(center=(screen_width//2, 100))
            )
            for index, line in enumerate(reflection_lines):
                line_surface = font_small.render(line, True, (30,30,30))
                y_position = 180 + index * line_height
                screen.blit(line_surface, line_surface.get_rect(center=(screen_width//2, y_position)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
