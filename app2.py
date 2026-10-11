import pygame
import sys
import random
import math
import struct
import wave
import io

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)

# Initialize Pygame & Mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders - Ultimate")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 24, bold=True)
big_font = pygame.font.SysFont("monospace", 48, bold=True)
small_font = pygame.font.SysFont("monospace", 18, bold=True)

# Game Surface for screen shake
game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

# --- Sound Generators (Pure Python) ---
def generate_sound(freq, duration_ms, vol=0.3):
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            val = vol if math.sin(2 * math.pi * freq * t) > 0 else -vol
            data = struct.pack('<h', int(val * 32767))
            wf.writeframes(data)
    buf.seek(0)
    return pygame.mixer.Sound(buf)

def generate_music_loop():
    sample_rate = 22050
    duration = 2.0 
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        freqs = [110, 130.81, 146.83, 164.81] # A, C, D, E
        samples_per_note = n_samples // len(freqs)
        for i in range(n_samples):
            note_idx = (i // samples_per_note) % len(freqs)
            freq = freqs[note_idx]
            t = i / sample_rate
            val = (2 * abs(2 * (t * freq - math.floor(t * freq + 0.5))) - 1) * 0.15
            data = struct.pack('<h', int(val * 32767))
            wf.writeframes(data)
    buf.seek(0)
    return pygame.mixer.Sound(buf)

shoot_sound = generate_sound(880, 100, 0.2)
explosion_sound = generate_sound(150, 300, 0.4)
ufo_sound = generate_sound(440, 150, 0.2)
music = generate_music_loop()

# --- Classes ---
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.5, 3.0)
        self.size = 1 if self.speed < 2 else 2

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        pygame.draw.rect(screen, (150, 150, 150), (self.x, self.y, self.size, self.size))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.dx = random.uniform(-4, 4)
        self.dy = random.uniform(-4, 4)
        self.life = random.randint(15, 35)
        self.color = color
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

class Player:
    def __init__(self):
        self.width = 50
        self.height = 30
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - self.width // 2, SCREEN_HEIGHT - 60, self.width, self.height)
        self.speed = 6
        self.color = CYAN
        self.lives = 3
        self.invincible_timer = 0
        self.shield_timer = 0
        self.multi_shot = 0

    def move(self, dx):
        self.rect.x += dx
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

    def draw(self, screen):
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            pass # Blink effect
        else:
            pygame.draw.rect(screen, self.color, (self.rect.x, self.rect.y + 10, self.width, 20))
            pygame.draw.rect(screen, self.color, (self.rect.x + 20, self.rect.y, 10, 15))
            
        if self.shield_timer > 0:
            radius = 35 + int(5 * math.sin(pygame.time.get_ticks() / 100))
            pygame.draw.circle(screen, CYAN, self.rect.center, radius, 2)

class Bullet:
    def __init__(self, x, y, color, speed, is_player_bullet=True, dx=0):
        self.rect = pygame.Rect(x, y, 4, 15)
        self.color = color
        self.speed = speed
        self.is_player_bullet = is_player_bullet
        self.dx = dx

    def update(self):
        self.rect.y -= self.speed if self.is_player_bullet else -self.speed
        self.rect.x += self.dx

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Alien:
    def __init__(self, x, y, color, tier):
        self.width = 40
        self.height = 30
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = color
        self.tier = tier
        self.frame = 0
        self.points = (4 - tier) * 10

    def draw(self, screen):
        x, y = self.rect.x, self.rect.y
        pygame.draw.rect(screen, self.color, (x+10, y+5, 20, 15))
        pygame.draw.rect(screen, self.color, (x+5, y+10, 30, 10))
        pygame.draw.rect(screen, BLACK, (x+12, y+10, 4, 4))
        pygame.draw.rect(screen, BLACK, (x+24, y+10, 4, 4))
        
        if self.frame == 0:
            pygame.draw.rect(screen, self.color, (x+5, y+20, 6, 6))
            pygame.draw.rect(screen, self.color, (x+29, y+20, 6, 6))
            pygame.draw.rect(screen, self.color, (x+15, y+20, 10, 4))
        else:
            pygame.draw.rect(screen, self.color, (x+10, y+20, 6, 6))
            pygame.draw.rect(screen, self.color, (x+24, y+20, 6, 6))
            pygame.draw.rect(screen, self.color, (x+5, y+22, 6, 4))
            pygame.draw.rect(screen, self.color, (x+29, y+22, 6, 4))

class Shield:
    def __init__(self, x, y):
        self.blocks = []
        shape = ["  XXXXXX  ", " XXXXXXXX ", "XXXXXXXXXX", "XXXXXXXXXX", "XXX    XXX"]
        block_size = 5
        for r, row in enumerate(shape):
            for c, char in enumerate(row):
                if char == 'X':
                    self.blocks.append(pygame.Rect(x + c*block_size, y + r*block_size, block_size, block_size))

    def draw(self, screen):
        for block in self.blocks:
            pygame.draw.rect(screen, GREEN, block)

    def check_collision(self, bullet):
        for block in self.blocks[:]:
            if block.colliderect(bullet.rect):
                self.blocks.remove(block)
                for b in self.blocks[:]:
                    if b.colliderect(block.inflate(4, 4)) and random.random() < 0.3:
                        self.blocks.remove(b)
                return True
        return False

class UFO:
    def __init__(self):
        self.width = 50
        self.height = 20
        self.rect = pygame.Rect(-self.width, 40, self.width, self.height)
        self.speed = 3 if random.random() > 0.5 else -3
        if self.speed < 0: self.rect.x = SCREEN_WIDTH
        self.active = True

    def update(self):
        self.rect.x += self.speed
        if (self.speed > 0 and self.rect.left > SCREEN_WIDTH) or (self.speed < 0 and self.rect.right < 0):
            self.active = False

    def draw(self, screen):
        pygame.draw.ellipse(screen, MAGENTA, self.rect)
        pygame.draw.rect(screen, MAGENTA, (self.rect.x+15, self.rect.y-8, 20, 10))

class PowerUp:
    def __init__(self, x, y, ptype):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.ptype = ptype
        self.speed = 2
        self.active = True
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.active = False
            
    def draw(self, screen):
        color = YELLOW if self.ptype == 'M' else CYAN if self.ptype == 'L' else MAGENTA
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text = small_font.render(self.ptype, True, BLACK)
        screen.blit(text, (self.rect.x + 5, self.rect.y + 2))

# --- Game State & Setup ---
muted = False
shake_timer = 0
shake_magnitude = 0

def trigger_shake(mag, dur):
    global shake_timer, shake_magnitude
    shake_timer = dur
    shake_magnitude = mag

def play_sound(sound):
    if not muted:
        sound.play()

def start_wave():
    global aliens, shields, powerups, alien_direction, base_alien_speed, alien_anim_timer
    aliens = []
    powerups = []
    alien_direction = 1
    alien_anim_timer = 0
    
    alien_colors = [RED, ORANGE, YELLOW, GREEN]
    for row in range(4):
        for col in range(8):
            x = col * 60 + 70
            y = row * 50 + 80
            aliens.append(Alien(x, y, alien_colors[row], row))
            
    shields = [Shield(120, 480), Shield(280, 480), Shield(440, 480), Shield(600, 480)]

def reset_game():
    global player, aliens, shields, powerups, player_bullets, alien_bullets, particles, ufo
    global score, high_score, game_state, current_wave, base_alien_speed, shoot_timer, ufo_timer
    global shake_timer, shake_magnitude
    
    player = Player()
    player_bullets = []
    alien_bullets = []
    particles = []
    ufo = None
    score = 0
    game_state = 'playing'
    current_wave = 1
    base_alien_speed = 1.5
    shoot_timer = 0
    ufo_timer = 0
    shake_timer = 0
    shake_magnitude = 0
    
    start_wave()
    if not muted:
        music.play(-1)

player = None
aliens = []
shields = []
powerups = []
player_bullets = []
alien_bullets = []
particles = []
ufo = None
stars = [Star() for _ in range(100)]

score = 0
high_score = 0
game_state = 'menu' # 'menu', 'playing', 'paused', 'game_over', 'wave_clear'
current_wave = 1
base_alien_speed = 1.5
shoot_timer = 0
ufo_timer = 0
alien_anim_timer = 0
wave_clear_timer = 0

# --- Main Game Loop ---
running = True
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if game_state == 'menu':
                if event.key == pygame.K_RETURN:
                    reset_game()
            elif game_state in ['game_over', 'wave_clear']:
                if event.key == pygame.K_r:
                    if score > high_score: high_score = score
                    reset_game()
            elif game_state in ['playing', 'paused']:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    game_state = 'paused' if game_state == 'playing' else 'playing'
                if event.key == pygame.K_m:
                    muted = not muted
                    if muted:
                        music.stop()
                    else:
                        if game_state == 'playing': music.play(-1)
                        
            if game_state == 'playing' and event.key == pygame.K_SPACE and shoot_timer <= 0:
                bullet_x = player.rect.x + player.width // 2 - 2
                bullet_y = player.rect.y
                
                if player.multi_shot > 0:
                    player.multi_shot -= 1
                    player_bullets.append(Bullet(bullet_x, bullet_y, YELLOW, 8, True, dx=0))
                    player_bullets.append(Bullet(bullet_x, bullet_y, YELLOW, 8, True, dx=-2))
                    player_bullets.append(Bullet(bullet_x, bullet_y, YELLOW, 8, True, dx=2))
                else:
                    player_bullets.append(Bullet(bullet_x, bullet_y, YELLOW, 8, True))
                    
                shoot_timer = 15
                play_sound(shoot_sound)

    # 2. Update Logic
    for star in stars: star.update()

    if game_state == 'playing':
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: player.move(-player.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player.move(player.speed)

        if shoot_timer > 0: shoot_timer -= 1
        if player.invincible_timer > 0: player.invincible_timer -= 1
        if player.shield_timer > 0: player.shield_timer -= 1
        if shake_timer > 0: shake_timer -= 1

        for bullet in player_bullets: bullet.update()
        for bullet in alien_bullets: bullet.update()
        for p in particles: p.update()
        for p in powerups: p.update()
        
        if ufo:
            ufo.update()
            if not ufo.active: ufo = None

        player_bullets = [b for b in player_bullets if b.rect.bottom > 0 and b.rect.right > 0 and b.rect.left < SCREEN_WIDTH]
        alien_bullets = [b for b in alien_bullets if b.rect.top < SCREEN_HEIGHT]
        particles = [p for p in particles if p.life > 0]
        powerups = [p for p in powerups if p.active]

        # Alien Movement & Animation
        current_alien_speed = base_alien_speed + (32 - len(aliens)) * 0.08
        alien_anim_timer += 1
        if alien_anim_timer >= 30:
            alien_anim_timer = 0
            for alien in aliens: alien.frame = 1 - alien.frame
        
        hit_edge = False
        for alien in aliens:
            if alien.rect.right + current_alien_speed * alien_direction > SCREEN_WIDTH or \
               alien.rect.left + current_alien_speed * alien_direction < 0:
                hit_edge = True
                break
        
        if hit_edge:
            alien_direction *= -1
            for alien in aliens: alien.rect.y += 20
        else:
            for alien in aliens: alien.rect.x += current_alien_speed * alien_direction

        # Shooting
        if aliens and random.randint(1, max(20, 60 - len(aliens))) == 1:
            shooter = random.choice(aliens)
            alien_bullets.append(Bullet(shooter.rect.x + 20, shooter.rect.y + 30, RED, 5, False))

        ufo_timer += 1
        if not ufo and ufo_timer > 900:
            ufo = UFO()
            ufo_timer = 0
            play_sound(ufo_sound)

        # Collisions
        for bullet in player_bullets[:]:
            for alien in aliens[:]:
                if bullet.rect.colliderect(alien.rect):
                    if bullet in player_bullets: player_bullets.remove(bullet)
                    aliens.remove(alien)
                    score += alien.points
                    for _ in range(15): particles.append(Particle(alien.rect.centerx, alien.rect.centery, alien.color))
                    play_sound(explosion_sound)
                    if random.random() < 0.1:
                        ptype = random.choice(['M', 'L', 'S'])
                        powerups.append(PowerUp(alien.rect.centerx - 10, alien.rect.centery - 10, ptype))
                    break
        
        if ufo:
            for bullet in player_bullets[:]:
                if bullet.rect.colliderect(ufo.rect):
                    player_bullets.remove(bullet)
                    score += 50
                    for _ in range(25): particles.append(Particle(ufo.rect.centerx, ufo.rect.centery, MAGENTA))
                    play_sound(explosion_sound)
                    trigger_shake(5, 10)
                    ptype = random.choice(['M', 'L', 'S'])
                    powerups.append(PowerUp(ufo.rect.centerx - 10, ufo.rect.centery - 10, ptype))
                    ufo.active = False
                    ufo = None
                    break

        for bullet in player_bullets[:]:
            for shield in shields:
                if shield.check_collision(bullet):
                    player_bullets.remove(bullet)
                    break
        
        for bullet in alien_bullets[:]:
            for shield in shields:
                if shield.check_collision(bullet):
                    alien_bullets.remove(bullet)
                    break

        for p in powerups[:]:
            if p.rect.colliderect(player.rect):
                if p.ptype == 'M': player.multi_shot += 5
                elif p.ptype == 'L': player.lives += 1
                elif p.ptype == 'S': player.shield_timer = 300
                powerups.remove(p)

        if player.invincible_timer <= 0 and player.shield_timer <= 0:
            for bullet in alien_bullets:
                if bullet.rect.colliderect(player.rect):
                    alien_bullets.remove(bullet)
                    player.lives -= 1
                    for _ in range(20): particles.append(Particle(player.rect.centerx, player.rect.centery, CYAN))
                    play_sound(explosion_sound)
                    trigger_shake(10, 20)
                    if player.lives <= 0:
                        game_state = 'game_over'
                        if score > high_score: high_score = score
                    else:
                        player.invincible_timer = 120
                    break

        for alien in aliens:
            if alien.rect.bottom >= player.rect.top:
                game_state = 'game_over'
                if score > high_score: high_score = score

        if not aliens:
            game_state = 'wave_clear'
            wave_clear_timer = 120

    elif game_state == 'wave_clear':
        wave_clear_timer -= 1
        if wave_clear_timer <= 0:
            current_wave += 1
            base_alien_speed += 0.5
            start_wave()
            game_state = 'playing'

    # 3. Drawing
    game_surface.fill(BLACK)
    
    for star in stars: star.draw(game_surface)
    for shield in shields: shield.draw(game_surface)
    
    if game_state != 'menu':
        player.draw(game_surface)
        for alien in aliens: alien.draw(game_surface)
        for bullet in player_bullets: bullet.draw(game_surface)
        for bullet in alien_bullets: bullet.draw(game_surface)
        if ufo: ufo.draw(game_surface)
        for p in particles: p.draw(game_surface)
        for p in powerups: p.draw(game_surface)

        # HUD
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        high_score_text = font.render(f"HI: {high_score}", True, WHITE)
        wave_text = font.render(f"WAVE {current_wave}", True, YELLOW)
        
        game_surface.blit(score_text, (10, 10))
        game_surface.blit(high_score_text, (SCREEN_WIDTH - high_score_text.get_width() - 10, 10))
        game_surface.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 10))

        for i in range(player.lives):
            lx = SCREEN_WIDTH - 40 - i * 40
            ly = 40
            pygame.draw.rect(game_surface, CYAN, (lx, ly + 10, 30, 12))
            pygame.draw.rect(game_surface, CYAN, (lx + 12, ly, 6, 10))

    # Apply Screen Shake
    offset_x = random.randint(-shake_magnitude, shake_magnitude) if shake_timer > 0 else 0
    offset_y = random.randint(-shake_magnitude, shake_magnitude) if shake_timer > 0 else 0
    screen.fill(BLACK)
    screen.blit(game_surface, (offset_x, offset_y))

    # Draw Overlays (No Shake)
    if game_state == 'menu':
        title = big_font.render("SPACE INVADERS", True, CYAN)
        start = font.render("Press ENTER to Start", True, WHITE)
        controls = small_font.render("ARROWS/WASD: Move | SPACE: Shoot | P: Pause | M: Mute", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, 300))
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, 400))
    
    elif game_state == 'paused':
        pause_text = big_font.render("PAUSED", True, YELLOW)
        screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 24))
        
    elif game_state == 'wave_clear':
        clear_text = big_font.render(f"WAVE {current_wave} CLEARED!", True, GREEN)
        screen.blit(clear_text, (SCREEN_WIDTH//2 - clear_text.get_width()//2, SCREEN_HEIGHT//2 - 24))
        
    elif game_state == 'game_over':
        go_text = big_font.render("GAME OVER", True, RED)
        restart_text = font.render("Press 'R' to Restart", True, WHITE)
        screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 40))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()