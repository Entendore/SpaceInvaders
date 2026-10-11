import pygame
import random
import math
import json
import numpy as np
from datetime import datetime

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders - Enhanced Edition")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (147, 0, 211)
PINK = (255, 105, 180)
BLUE = (0, 100, 255)
DARK_GREEN = (0, 100, 0)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
medium_font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 24)

# ============================================================
# SOUND SYNTHESIS ENGINE - No external files needed!
# ============================================================

SAMPLE_RATE = 44100

def generate_tone(frequency, duration, volume=0.3, wave_type='square', fade_out=True):
    """Generate a tone using numpy arrays"""
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    if wave_type == 'square':
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave_type == 'sawtooth':
        wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))
    elif wave_type == 'sine':
        wave = np.sin(2 * np.pi * frequency * t)
    elif wave_type == 'triangle':
        wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
    elif wave_type == 'noise':
        wave = np.random.uniform(-1, 1, samples)
    else:
        wave = np.sign(np.sin(2 * np.pi * frequency * t))

    # Apply envelope
    if fade_out:
        envelope = np.ones(samples)
        fade_samples = min(int(SAMPLE_RATE * 0.05), samples // 4)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        wave = wave * envelope

    # Convert to 16-bit PCM stereo
    audio = (wave * volume * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))

    sound = pygame.sndarray.make_sound(stereo)
    return sound

def generate_laser_sound():
    """Classic 8-bit laser pew-pew"""
    duration = 0.15
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    freq = np.linspace(800, 200, samples)
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    envelope = np.exp(-t * 15)
    audio = (wave * envelope * 0.25 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_enemy_laser_sound():
    """Deeper enemy laser"""
    duration = 0.2
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    freq = np.linspace(400, 100, samples)
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    envelope = np.exp(-t * 10)
    audio = (wave * envelope * 0.2 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_explosion_sound(size='medium'):
    """Explosion with noise and low frequency"""
    if size == 'small':
        duration = 0.2
        vol = 0.2
    elif size == 'large':
        duration = 0.5
        vol = 0.35
    else:
        duration = 0.3
        vol = 0.25

    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    # White noise with low-pass filter effect
    noise = np.random.uniform(-1, 1, samples)
    # Simple moving average for low-pass
    window_size = 20
    filtered = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

    # Frequency sweep down
    freq = np.linspace(200, 50, samples)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)

    # Combine
    wave = filtered * 0.7 + tone * 0.3
    envelope = np.exp(-t * 8)
    audio = (wave * envelope * vol * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_powerup_sound():
    """Magical ascending chime"""
    duration = 0.4
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    # Major chord arpeggio
    freqs = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    wave = np.zeros(samples)

    for i, freq in enumerate(freqs):
        start = int(samples * i / len(freqs))
        end = samples
        seg_t = t[start:end]
        seg_wave = np.sin(2 * np.pi * freq * seg_t) * np.exp(-(seg_t - seg_t[0]) * 5)
        wave[start:end] += seg_wave * 0.25

    audio = (wave * 0.3 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_bomb_sound():
    """Massive explosion"""
    duration = 0.8
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    noise = np.random.uniform(-1, 1, samples)
    window_size = 50
    filtered = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

    freq = np.linspace(100, 20, samples)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)

    wave = filtered * 0.6 + tone * 0.4
    envelope = np.exp(-t * 4)
    audio = (wave * envelope * 0.4 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_ufo_sound():
    """Classic UFO oscillating hum"""
    duration = 0.3
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    # Oscillating frequency
    osc_freq = 6  # Hz
    base_freq = 400
    freq_mod = base_freq + 100 * np.sin(2 * np.pi * osc_freq * t)
    phase = np.cumsum(freq_mod) / SAMPLE_RATE * 2 * np.pi
    wave = np.sin(phase)

    audio = (wave * 0.15 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_invader_move_sound(step=0):
    """Classic 4-step invader march"""
    base_freqs = [110, 100, 95, 90]
    freq = base_freqs[step % 4]
    return generate_tone(freq, 0.08, volume=0.08, wave_type='sawtooth')

def generate_game_over_sound():
    """Sad descending notes"""
    duration = 1.5
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    freqs = [400, 350, 300, 250, 200, 150]
    wave = np.zeros(samples)

    for i, freq in enumerate(freqs):
        start = int(samples * i / len(freqs))
        end = int(samples * (i + 1) / len(freqs))
        seg_t = np.linspace(0, duration/len(freqs), end - start, False)
        seg_wave = np.sin(2 * np.pi * freq * seg_t) * np.exp(-seg_t * 3)
        wave[start:end] += seg_wave * 0.3

    audio = (wave * 0.3 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_level_up_sound():
    """Victory ascending fanfare"""
    duration = 0.8
    samples = int(SAMPLE_RATE * duration)

    notes = [523.25, 659.25, 783.99, 1046.50, 1318.51]  # C major chord up
    wave = np.zeros(samples)

    for i, freq in enumerate(notes):
        start = int(samples * i / len(notes))
        end = samples
        seg_samples = end - start
        seg_t = np.linspace(0, seg_samples/SAMPLE_RATE, seg_samples, False)
        seg_wave = np.sin(2 * np.pi * freq * seg_t) * np.exp(-seg_t * 4)
        wave[start:end] += seg_wave * 0.25

    audio = (wave * 0.3 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_menu_select_sound():
    """Short blip for menu navigation"""
    return generate_tone(600, 0.05, volume=0.15, wave_type='square')

def generate_hit_sound():
    """Player hit damage sound"""
    duration = 0.3
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    noise = np.random.uniform(-1, 1, samples)
    freq = np.linspace(300, 50, samples)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    wave = noise * 0.5 + tone * 0.5
    envelope = np.exp(-t * 10)
    audio = (wave * envelope * 0.25 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

def generate_shield_break_sound():
    """Glass shattering sound"""
    duration = 0.3
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)

    noise = np.random.uniform(-1, 1, samples)
    # High frequency noise
    high_noise = noise.copy()
    for i in range(1, len(high_noise)):
        high_noise[i] = (high_noise[i] + high_noise[i-1]) / 2

    freq = np.linspace(1000, 200, samples)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    wave = high_noise * 0.7 + tone * 0.3
    envelope = np.exp(-t * 12)
    audio = (wave * envelope * 0.2 * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.music_timer = 0
        self.invader_step = 0
        self._generate_all_sounds()
        self.music_enabled = True
        self.sfx_enabled = True

    def _generate_all_sounds(self):
        print("Generating sounds...")
        self.sounds['shoot'] = generate_laser_sound()
        self.sounds['enemy_shoot'] = generate_enemy_laser_sound()
        self.sounds['explosion_small'] = generate_explosion_sound('small')
        self.sounds['explosion_medium'] = generate_explosion_sound('medium')
        self.sounds['explosion_large'] = generate_explosion_sound('large')
        self.sounds['powerup'] = generate_powerup_sound()
        self.sounds['bomb'] = generate_bomb_sound()
        self.sounds['ufo'] = generate_ufo_sound()
        self.sounds['game_over'] = generate_game_over_sound()
        self.sounds['level_up'] = generate_level_up_sound()
        self.sounds['menu_select'] = generate_menu_select_sound()
        self.sounds['hit'] = generate_hit_sound()
        self.sounds['shield_break'] = generate_shield_break_sound()
        self.sounds['invader_move'] = [generate_invader_move_sound(i) for i in range(4)]
        print("Sounds generated!")

    def play(self, sound_name, loops=0):
        if not self.sfx_enabled:
            return
        if sound_name in self.sounds:
            if sound_name == 'invader_move':
                self.sounds[sound_name][self.invader_step % 4].play(loops=loops)
                self.invader_step += 1
            else:
                self.sounds[sound_name].play(loops=loops)

    def play_invader_move(self):
        if self.sfx_enabled:
            self.sounds['invader_move'][self.invader_step % 4].play()
            self.invader_step += 1

    def toggle_music(self):
        self.music_enabled = not self.music_enabled

    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled

    def stop_all(self):
        pygame.mixer.stop()

# Global sound manager
sound_manager = SoundManager()

# ============================================================
# GAME CLASSES
# ============================================================

def load_high_scores():
    try:
        with open("high_scores.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_high_score(score, level):
    scores = load_high_scores()
    scores.append({"score": score, "level": level, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:10]
    with open("high_scores.json", "w") as f:
        json.dump(scores, f)
    return scores

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed, size, lifetime):
        super().__init__()
        self.image = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size, size), size)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = 0.1

    def update(self):
        self.vy += self.gravity
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.lifetime -= 1
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.image.set_alpha(alpha)
        if self.lifetime <= 0:
            self.kill()

class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = random.randint(1, 3)
        self.image = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        brightness = random.randint(150, 255)
        pygame.draw.circle(self.image, (brightness, brightness, brightness), (self.size, self.size), self.size)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH)
        self.rect.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.2, 1.5)
        self.twinkle_speed = random.uniform(0.02, 0.05)
        self.twinkle_offset = random.uniform(0, 2*math.pi)

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > SCREEN_HEIGHT:
            self.rect.y = -5
            self.rect.x = random.randint(0, SCREEN_WIDTH)
        alpha = int(150 + 105 * math.sin(pygame.time.get_ticks() * self.twinkle_speed + self.twinkle_offset))
        self.image.set_alpha(alpha)

class PowerUp(pygame.sprite.Sprite):
    TYPES = {
        "rapid_fire": {"color": CYAN, "duration": 300, "symbol": "R"},
        "shield": {"color": BLUE, "duration": 400, "symbol": "S"},
        "multi_shot": {"color": PURPLE, "duration": 250, "symbol": "M"},
        "speed_boost": {"color": ORANGE, "duration": 300, "symbol": "+"},
        "bomb": {"color": RED, "duration": 1, "symbol": "B"},
        "life": {"color": PINK, "duration": 1, "symbol": "♥"},
    }

    def __init__(self, x, y, power_type=None):
        super().__init__()
        self.power_type = power_type or random.choice(list(self.TYPES.keys()))
        info = self.TYPES[self.power_type]
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, info["color"], (15, 15), 14)
        pygame.draw.circle(self.image, WHITE, (15, 15), 14, 2)
        text = small_font.render(info["symbol"], True, WHITE)
        text_rect = text.get_rect(center=(15, 15))
        self.image.blit(text, text_rect)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 2
        self.bob_offset = random.uniform(0, 2*math.pi)

    def update(self):
        self.rect.y += self.speed
        self.rect.x += math.sin(pygame.time.get_ticks() * 0.003 + self.bob_offset) * 0.5
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = pygame.Surface((50, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.base_image, GREEN, [(25, 0), (45, 30), (35, 35), (25, 25), (15, 35), (5, 30)])
        pygame.draw.polygon(self.base_image, CYAN, [(25, 5), (40, 28), (35, 30), (25, 20), (15, 30), (10, 28)])
        pygame.draw.rect(self.base_image, YELLOW, (22, 25, 6, 10))
        pygame.draw.ellipse(self.base_image, ORANGE, (18, 32, 14, 8))

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.base_speed = 5
        self.speed = self.base_speed
        self.lives = 3
        self.max_lives = 5
        self.shield = False
        self.shield_timer = 0
        self.rapid_fire = False
        self.rapid_timer = 0
        self.multi_shot = False
        self.multi_timer = 0
        self.invincible = 0
        self.shoot_cooldown = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield = False

        if self.rapid_timer > 0:
            self.rapid_timer -= 1
            if self.rapid_timer <= 0:
                self.rapid_fire = False

        if self.multi_timer > 0:
            self.multi_timer -= 1
            if self.multi_timer <= 0:
                self.multi_shot = False

        if self.invincible > 0:
            self.invincible -= 1
            if self.invincible % 10 < 5:
                self.image = self.base_image.copy()
            else:
                self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        else:
            self.image = self.base_image.copy()

        if self.shield:
            shield_surface = pygame.Surface((70, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surface, (*BLUE[:3], 100), (0, 0, 70, 60))
            pygame.draw.ellipse(shield_surface, BLUE, (0, 0, 70, 60), 2)
            self.image = self.base_image.copy()
            self.image.blit(shield_surface, (-10, -10))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self):
        if self.shoot_cooldown > 0:
            return []

        bullets = []
        cooldown = 12 if self.rapid_fire else 20
        self.shoot_cooldown = cooldown

        if self.multi_shot:
            bullets.append(Bullet(self.rect.centerx, self.rect.top, -10, YELLOW, 0))
            bullets.append(Bullet(self.rect.centerx - 12, self.rect.top, -10, YELLOW, -0.4))
            bullets.append(Bullet(self.rect.centerx + 12, self.rect.top, -10, YELLOW, 0.4))
        else:
            bullets.append(Bullet(self.rect.centerx, self.rect.top, -10, YELLOW, 0))

        sound_manager.play('shoot')
        return bullets

    def activate_powerup(self, power_type):
        if power_type == "shield":
            self.shield = True
            self.shield_timer = PowerUp.TYPES["shield"]["duration"]
        elif power_type == "rapid_fire":
            self.rapid_fire = True
            self.rapid_timer = PowerUp.TYPES["rapid_fire"]["duration"]
        elif power_type == "multi_shot":
            self.multi_shot = True
            self.multi_timer = PowerUp.TYPES["multi_shot"]["duration"]
        elif power_type == "speed_boost":
            self.speed = self.base_speed * 1.5
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000)
        elif power_type == "life":
            self.lives = min(self.lives + 1, self.max_lives)
        elif power_type == "bomb":
            return "bomb"
        return None

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=-8, color=YELLOW, angle=0):
        super().__init__()
        self.image = pygame.Surface((6, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, color, (0, 0, 6, 18))
        pygame.draw.ellipse(self.image, WHITE, (1, 1, 4, 16))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed
        self.angle = angle
        self.vx = math.sin(angle) * abs(speed) * 0.5
        self.vy = math.cos(angle) * speed

    def update(self):
        self.rect.y += self.vy
        self.rect.x += self.vx
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class Invader(pygame.sprite.Sprite):
    ROW_COLORS = [RED, ORANGE, YELLOW, GREEN, CYAN]

    def __init__(self, x, y, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.color = self.ROW_COLORS[row % len(self.ROW_COLORS)]
        self.base_image = pygame.Surface((45, 35), pygame.SRCALPHA)
        self.draw_invader(0)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = 1
        self.direction = 1
        self.drop_distance = 25
        self.animation_frame = 0
        self.animation_timer = 0
        self.points = (5 - row) * 10

    def draw_invader(self, frame):
        self.base_image.fill((0,0,0,0))
        color = self.color
        pygame.draw.ellipse(self.base_image, color, (5, 5, 35, 22))
        eye_color = WHITE
        pygame.draw.circle(self.base_image, eye_color, (16, 14), 5)
        pygame.draw.circle(self.base_image, eye_color, (29, 14), 5)
        pygame.draw.circle(self.base_image, BLACK, (16, 14), 3)
        pygame.draw.circle(self.base_image, BLACK, (29, 14), 3)
        if frame == 0:
            pygame.draw.line(self.base_image, color, (8, 22), (3, 30), 3)
            pygame.draw.line(self.base_image, color, (37, 22), (42, 30), 3)
        else:
            pygame.draw.line(self.base_image, color, (8, 22), (13, 30), 3)
            pygame.draw.line(self.base_image, color, (37, 22), (32, 30), 3)
        pygame.draw.line(self.base_image, color, (18, 5), (15, 0), 2)
        pygame.draw.line(self.base_image, color, (27, 5), (30, 0), 2)

    def update(self):
        self.rect.x += self.speed_x * self.direction
        self.animation_timer += 1
        if self.animation_timer > 20:
            self.animation_timer = 0
            self.animation_frame = 1 - self.animation_frame
            self.draw_invader(self.animation_frame)
            self.image = self.base_image.copy()

    def drop_down(self):
        self.rect.y += self.drop_distance
        self.direction *= -1

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.bottom, speed=random.randint(3, 6), color=RED, angle=random.uniform(-0.1, 0.1))
        sound_manager.play('enemy_shoot')
        return bullet

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size=40, color=None):
        super().__init__()
        self.size = size
        self.image = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.lifetime = 15
        self.max_lifetime = 15
        self.color = color or ORANGE

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        else:
            self.image.fill((0, 0, 0, 0))
            progress = 1 - (self.lifetime / self.max_lifetime)
            radius = int(progress * self.size)
            alpha = int(255 * (1 - progress))
            color_with_alpha = (*self.color[:3], alpha)
            pygame.draw.circle(self.image, color_with_alpha, (self.size, self.size), radius)
            pygame.draw.circle(self.image, (*WHITE[:3], alpha//2), (self.size, self.size), radius//2)

class Barrier(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((70, 50), pygame.SRCALPHA)
        self.image.fill(GREEN)
        pygame.draw.rect(self.image, (0,0,0,0), (20, 0, 30, 25))
        pygame.draw.rect(self.image, (0,0,0,0), (0, 0, 70, 10))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 8
        self.max_health = 8

    def hit(self):
        self.health -= 1
        alpha = int(255 * (self.health / self.max_health))
        temp = pygame.Surface((70, 50), pygame.SRCALPHA)
        temp.fill(GREEN)
        pygame.draw.rect(temp, (0,0,0,0), (20, 0, 30, 25))
        pygame.draw.rect(temp, (0,0,0,0), (0, 0, 70, 10))
        temp.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        self.image = temp
        if self.health <= 0:
            self.kill()
            return True
        return False

class UFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((60, 25), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, RED, (0, 8, 60, 17))
        pygame.draw.ellipse(self.image, (255, 100, 100), (10, 0, 40, 12))
        pygame.draw.ellipse(self.image, (255, 200, 200), (20, 3, 20, 6))
        for i in range(4):
            color = random.choice([RED, YELLOW, GREEN])
            pygame.draw.circle(self.image, color, (10 + i*13, 16), 3)
        self.rect = self.image.get_rect()
        self.rect.y = 35
        self.speed = random.choice([-4, 4])
        self.rect.x = -60 if self.speed > 0 else SCREEN_WIDTH
        self.points = random.choice([50, 100, 150, 200, 300])
        self.light_timer = 0
        self.sound_timer = 0

    def update(self):
        self.rect.x += self.speed
        self.light_timer += 1
        self.sound_timer += 1

        # Play UFO hum periodically
        if self.sound_timer > 20:
            self.sound_timer = 0
            sound_manager.play('ufo')

        if self.light_timer > 10:
            self.light_timer = 0
            for i in range(4):
                color = random.choice([RED, YELLOW, GREEN, CYAN])
                pygame.draw.circle(self.image, color, (10 + i*13, 16), 3)
        if self.rect.right < -20 or self.rect.left > SCREEN_WIDTH + 20:
            self.kill()

def create_invaders(level=1):
    invaders = pygame.sprite.Group()
    rows = min(5 + level // 3, 8)
    cols = 11
    for row in range(rows):
        for col in range(cols):
            x = 80 + col * 60
            y = 60 + row * 45
            invader = Invader(x, y, row, col)
            invaders.add(invader)
    return invaders

def create_barriers():
    barriers = pygame.sprite.Group()
    for i in range(4):
        x = 100 + i * 220
        y = SCREEN_HEIGHT - 140
        barriers.add(Barrier(x, y))
    return barriers

def create_stars():
    stars = pygame.sprite.Group()
    for _ in range(100):
        stars.add(Star())
    return stars

def show_text(text, font, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
    return rect

def show_shaking_text(text, font, color, x, y, intensity=3):
    offset_x = random.randint(-intensity, intensity)
    offset_y = random.randint(-intensity, intensity)
    show_text(text, font, color, x + offset_x, y + offset_y)

def draw_health_bar(x, y, current, maximum, width=150, height=15):
    ratio = current / maximum
    pygame.draw.rect(screen, GRAY, (x, y, width, height))
    if ratio > 0.6:
        color = GREEN
    elif ratio > 0.3:
        color = YELLOW
    else:
        color = RED
    pygame.draw.rect(screen, color, (x, y, int(width * ratio), height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)

def draw_powerup_indicators(player, x, y):
    indicators = []
    if player.shield:
        indicators.append(("SHIELD", BLUE, player.shield_timer / PowerUp.TYPES["shield"]["duration"]))
    if player.rapid_fire:
        indicators.append(("RAPID", CYAN, player.rapid_timer / PowerUp.TYPES["rapid_fire"]["duration"]))
    if player.multi_shot:
        indicators.append(("MULTI", PURPLE, player.multi_timer / PowerUp.TYPES["multi_shot"]["duration"]))

    for i, (name, color, ratio) in enumerate(indicators):
        bar_x = x
        bar_y = y + i * 20
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, 80, 15))
        pygame.draw.rect(screen, color, (bar_x, bar_y, int(80 * ratio), 15))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, 80, 15), 1)
        show_text(name, small_font, WHITE, bar_x + 40, bar_y + 7)

def title_screen():
    waiting = True
    stars = create_stars()
    title_y = 150
    direction = 1

    # Background ambient sound
    ambient = generate_tone(60, 2.0, volume=0.05, wave_type='sine', fade_out=False)
    ambient_channel = None

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sound_manager.play('menu_select')
                    if ambient_channel:
                        ambient_channel.stop()
                    return True
                if event.key == pygame.K_h:
                    sound_manager.play('menu_select')
                    show_high_scores()
                if event.key == pygame.K_m:
                    sound_manager.toggle_sfx()
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.fill(BLACK)
        stars.update()
        stars.draw(screen)

        title_y += 0.3 * direction
        if title_y > 170 or title_y < 130:
            direction *= -1

        show_text("SPACE INVADERS", large_font, GREEN, SCREEN_WIDTH//2, int(title_y))
        show_text("ENHANCED EDITION", medium_font, CYAN, SCREEN_WIDTH//2, 220)

        if pygame.time.get_ticks() % 1000 < 500:
            show_text("Press SPACE to Start", font, WHITE, SCREEN_WIDTH//2, 350)

        show_text("H - High Scores", small_font, GRAY, SCREEN_WIDTH//2, 420)
        show_text("M - Toggle Sound", small_font, GRAY, SCREEN_WIDTH//2, 445)
        show_text("ESC - Quit", small_font, GRAY, SCREEN_WIDTH//2, 470)

        sfx_status = "ON" if sound_manager.sfx_enabled else "OFF"
        show_text(f"Sound: {sfx_status}", small_font, GREEN if sound_manager.sfx_enabled else RED, SCREEN_WIDTH//2, 500)

        show_text("CONTROLS:", small_font, YELLOW, SCREEN_WIDTH//2, 540)
        show_text("← → or A/D : Move    SPACE : Shoot", small_font, WHITE, SCREEN_WIDTH//2, 565)
        show_text("P : Pause    ESC : Menu    M : Toggle Sound", small_font, WHITE, SCREEN_WIDTH//2, 590)

        pygame.display.flip()
        clock.tick(FPS)
    return False

def show_high_scores():
    scores = load_high_scores()
    waiting = True

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                sound_manager.play('menu_select')
                waiting = False

        screen.fill(BLACK)
        show_text("HIGH SCORES", large_font, GOLD, SCREEN_WIDTH//2, 80)

        if not scores:
            show_text("No scores yet!", font, WHITE, SCREEN_WIDTH//2, 250)
        else:
            for i, entry in enumerate(scores):
                y_pos = 160 + i * 40
                rank_color = GOLD if i == 0 else (GRAY if i == 1 else (ORANGE if i == 2 else WHITE))
                show_text(f"{i+1}.", font, rank_color, 250, y_pos, center=False)
                show_text(f"{entry['score']}", font, WHITE, 400, y_pos, center=False)
                show_text(f"Level {entry['level']}", font, GRAY, 550, y_pos, center=False)
                show_text(entry['date'], small_font, GRAY, 700, y_pos, center=False)

        show_text("Press any key to return", font, WHITE, SCREEN_WIDTH//2, 620)
        pygame.display.flip()
        clock.tick(FPS)

def pause_screen():
    paused = True
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)

    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_SPACE:
                    sound_manager.play('menu_select')
                    paused = False
                if event.key == pygame.K_m:
                    sound_manager.toggle_sfx()
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.blit(overlay, (0, 0))
        show_text("PAUSED", large_font, YELLOW, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80)
        show_text("Press P or SPACE to resume", font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        show_text("M - Toggle Sound", font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40)
        show_text("ESC to quit to menu", font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80)

        sfx_status = "ON" if sound_manager.sfx_enabled else "OFF"
        show_text(f"Sound: {sfx_status}", small_font, GREEN if sound_manager.sfx_enabled else RED, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120)

        pygame.display.flip()
        clock.tick(FPS)
    return True

def game_over_screen(score, level, won=False):
    save_high_score(score, level)
    scores = load_high_scores()
    rank = next((i+1 for i, s in enumerate(scores) if s["score"] == score and s["level"] == level), None)

    sound_manager.play('game_over')

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sound_manager.play('menu_select')
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.fill(BLACK)
        if won:
            show_shaking_text("YOU WIN!", large_font, GREEN, SCREEN_WIDTH//2, 150, 2)
        else:
            show_shaking_text("GAME OVER", large_font, RED, SCREEN_WIDTH//2, 150, 3)

        show_text(f"Score: {score}", large_font, WHITE, SCREEN_WIDTH//2, 250)
        show_text(f"Level Reached: {level}", font, YELLOW, SCREEN_WIDTH//2, 320)

        if rank and rank <= 10:
            show_text(f"NEW HIGH SCORE! Rank #{rank}", medium_font, GOLD, SCREEN_WIDTH//2, 380)

        show_text("Press SPACE to play again", font, WHITE, SCREEN_WIDTH//2, 480)
        show_text("Press ESC for main menu", font, GRAY, SCREEN_WIDTH//2, 520)

        show_text("Top Scores:", font, GRAY, SCREEN_WIDTH//2, 580)
        for i, entry in enumerate(scores[:5]):
            color = GOLD if i == 0 else WHITE
            show_text(f"{i+1}. {entry['score']} (L{entry['level']})", small_font, color, SCREEN_WIDTH//2, 610 + i*25)

        pygame.display.flip()
        clock.tick(FPS)
    return False

def create_particles(x, y, color, count=15, speed=4, size=3, lifetime=30):
    particles = pygame.sprite.Group()
    for _ in range(count):
        particles.add(Particle(x, y, color, random.uniform(1, speed), random.randint(1, size), random.randint(10, lifetime)))
    return particles

def main():
    if not title_screen():
        pygame.quit()
        return

    running = True
    game_active = True

    player = Player()
    player_group = pygame.sprite.Group(player)

    invaders = create_invaders()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    barriers = create_barriers()
    ufos = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    stars = create_stars()

    score = 0
    level = 1
    invader_speed = 1
    move_down = False
    ufo_timer = 0
    combo = 0
    combo_timer = 0
    max_combo = 0
    wave_clear_bonus = 0

    move_timer = 0
    move_interval = 35

    shake_intensity = 0
    shake_duration = 0

    while running:
        if not game_active:
            result = game_over_screen(score, level, won=(len(invaders) == 0 and player.lives > 0))
            if result:
                player = Player()
                player_group = pygame.sprite.Group(player)
                invaders = create_invaders()
                bullets = pygame.sprite.Group()
                enemy_bullets = pygame.sprite.Group()
                explosions = pygame.sprite.Group()
                barriers = create_barriers()
                ufos = pygame.sprite.Group()
                powerups = pygame.sprite.Group()
                particles = pygame.sprite.Group()
                stars = create_stars()
                score = 0
                level = 1
                invader_speed = 1
                move_down = False
                ufo_timer = 0
                combo = 0
                combo_timer = 0
                max_combo = 0
                move_timer = 0
                move_interval = 35
                shake_intensity = 0
                game_active = True
            else:
                if not title_screen():
                    running = False
                else:
                    player = Player()
                    player_group = pygame.sprite.Group(player)
                    invaders = create_invaders()
                    bullets = pygame.sprite.Group()
                    enemy_bullets = pygame.sprite.Group()
                    explosions = pygame.sprite.Group()
                    barriers = create_barriers()
                    ufos = pygame.sprite.Group()
                    powerups = pygame.sprite.Group()
                    particles = pygame.sprite.Group()
                    stars = create_stars()
                    score = 0
                    level = 1
                    invader_speed = 1
                    move_down = False
                    ufo_timer = 0
                    combo = 0
                    combo_timer = 0
                    max_combo = 0
                    move_timer = 0
                    move_interval = 35
                    shake_intensity = 0
                    game_active = True
                continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    new_bullets = player.shoot()
                    bullets.add(new_bullets)
                if event.key == pygame.K_p:
                    if not pause_screen():
                        if not title_screen():
                            running = False
                        else:
                            game_active = True
                            player = Player()
                            player_group = pygame.sprite.Group(player)
                            invaders = create_invaders()
                            bullets = pygame.sprite.Group()
                            enemy_bullets = pygame.sprite.Group()
                            explosions = pygame.sprite.Group()
                            barriers = create_barriers()
                            ufos = pygame.sprite.Group()
                            powerups = pygame.sprite.Group()
                            particles = pygame.sprite.Group()
                            stars = create_stars()
                            score = 0
                            level = 1
                            invader_speed = 1
                            move_down = False
                            ufo_timer = 0
                            combo = 0
                            combo_timer = 0
                            max_combo = 0
                            move_timer = 0
                            move_interval = 35
                            shake_intensity = 0
                if event.key == pygame.K_ESCAPE:
                    if not title_screen():
                        running = False
                    else:
                        game_active = True
                        player = Player()
                        player_group = pygame.sprite.Group(player)
                        invaders = create_invaders()
                        bullets = pygame.sprite.Group()
                        enemy_bullets = pygame.sprite.Group()
                        explosions = pygame.sprite.Group()
                        barriers = create_barriers()
                        ufos = pygame.sprite.Group()
                        powerups = pygame.sprite.Group()
                        particles = pygame.sprite.Group()
                        stars = create_stars()
                        score = 0
                        level = 1
                        invader_speed = 1
                        move_down = False
                        ufo_timer = 0
                        combo = 0
                        combo_timer = 0
                        max_combo = 0
                        move_timer = 0
                        move_interval = 35
                        shake_intensity = 0
            if event.type == pygame.USEREVENT + 1:
                player.speed = player.base_speed

        if combo_timer > 0:
            combo_timer -= 1
            if combo_timer <= 0:
                combo = 0

        if shake_duration > 0:
            shake_duration -= 1
            shake_intensity = max(0, shake_intensity - 0.5)

        player_group.update()
        bullets.update()
        enemy_bullets.update()
        explosions.update()
        ufos.update()
        powerups.update()
        particles.update()
        stars.update()

        # Invader movement with sound
        move_timer += 1 + (level * 0.15)
        current_interval = max(3, move_interval - level)
        if move_timer >= current_interval:
            move_timer = 0

            edge_hit = False
            for invader in invaders:
                if invader.rect.right >= SCREEN_WIDTH - 10 or invader.rect.left <= 10:
                    edge_hit = True
                    break

            if edge_hit and not move_down:
                move_down = True
                for invader in invaders:
                    invader.drop_down()
                move_down = False
                invader_speed += 0.15
                sound_manager.play_invader_move()
            else:
                for invader in invaders:
                    invader.speed_x = invader_speed
                    invader.update()
                sound_manager.play_invader_move()

        # Random enemy shooting
        if len(invaders) > 0 and random.random() < 0.025 + (level * 0.008):
            shooter = random.choice(invaders.sprites())
            enemy_bullets.add(shooter.shoot())

        # UFO spawning
        ufo_timer += 1
        if ufo_timer > 500 and len(ufos) == 0 and random.random() < 0.008:
            ufos.add(UFO())
            ufo_timer = 0

        # Power-up spawning
        if random.random() < 0.003 and len(powerups) < 2:
            powerups.add(PowerUp(random.randint(50, SCREEN_WIDTH-50), -30))

        # Collision detection - player bullets vs invaders
        hits = pygame.sprite.groupcollide(invaders, bullets, True, True)
        for invader in hits:
            combo += 1
            combo_timer = 90
            if combo > max_combo:
                max_combo = combo

            combo_multiplier = min(combo, 5)
            points = invader.points * combo_multiplier
            score += points

            # Sound based on combo
            if combo >= 5:
                sound_manager.play('explosion_large')
            elif combo >= 3:
                sound_manager.play('explosion_medium')
            else:
                sound_manager.play('explosion_small')

            explosions.add(Explosion(invader.rect.centerx, invader.rect.centery, size=35, color=invader.color))
            particles.add(create_particles(invader.rect.centerx, invader.rect.centery, invader.color, count=10))

            if random.random() < 0.12:
                powerups.add(PowerUp(invader.rect.centerx, invader.rect.centery))

            shake_intensity = 3
            shake_duration = 5

        # Collision - player bullets vs barriers
        barrier_hits = pygame.sprite.groupcollide(barriers, bullets, False, True)
        for barrier in barrier_hits:
            if barrier.hit():
                sound_manager.play('explosion_small')
                particles.add(create_particles(barrier.rect.centerx, barrier.rect.centery, GREEN, count=8))

        enemy_barrier_hits = pygame.sprite.groupcollide(barriers, enemy_bullets, False, True)
        for barrier in enemy_barrier_hits:
            if barrier.hit():
                sound_manager.play('explosion_small')
                particles.add(create_particles(barrier.rect.centerx, barrier.rect.centery, GREEN, count=8))

        # Collision - player bullets vs UFO
        ufo_hits = pygame.sprite.groupcollide(ufos, bullets, True, True)
        for ufo in ufo_hits:
            score += ufo.points
            sound_manager.play('explosion_large')
            explosions.add(Explosion(ufo.rect.centerx, ufo.rect.centery, size=60, color=RED))
            particles.add(create_particles(ufo.rect.centerx, ufo.rect.centery, RED, count=20, speed=6))
            shake_intensity = 6
            shake_duration = 10

        # Collision - enemy bullets vs player
        if pygame.sprite.spritecollide(player, enemy_bullets, True):
            if player.shield:
                player.shield = False
                player.shield_timer = 0
                sound_manager.play('shield_break')
                explosions.add(Explosion(player.rect.centerx, player.rect.centery, size=40, color=BLUE))
                particles.add(create_particles(player.rect.centerx, player.rect.centery, BLUE, count=15))
            elif player.invincible <= 0:
                player.lives -= 1
                player.invincible = 120
                sound_manager.play('hit')
                explosions.add(Explosion(player.rect.centerx, player.rect.centery, size=50, color=GREEN))
                particles.add(create_particles(player.rect.centerx, player.rect.centery, GREEN, count=20, speed=5))
                shake_intensity = 8
                shake_duration = 15
                if player.lives <= 0:
                    game_active = False

        # Collision - power-ups vs player
        powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in powerup_hits:
            result = player.activate_powerup(powerup.power_type)
            if result == "bomb":
                sound_manager.play('bomb')
                for invader in invaders:
                    explosions.add(Explosion(invader.rect.centerx, invader.rect.centery, size=30, color=RED))
                    particles.add(create_particles(invader.rect.centerx, invader.rect.centery, RED, count=8))
                    score += invader.points
                invaders.empty()
                shake_intensity = 10
                shake_duration = 20
            else:
                sound_manager.play('powerup')
                explosions.add(Explosion(powerup.rect.centerx, powerup.rect.centery, size=25, color=PowerUp.TYPES[powerup.power_type]["color"]))
                particles.add(create_particles(powerup.rect.centerx, powerup.rect.centery, PowerUp.TYPES[powerup.power_type]["color"], count=12))

        # Collision - invaders vs player
        if pygame.sprite.spritecollide(player, invaders, False):
            if player.invincible <= 0:
                player.lives = 0
                game_active = False

        # Check if invaders reached bottom
        for invader in invaders:
            if invader.rect.bottom >= SCREEN_HEIGHT - 60:
                game_active = False
                break

        # Check win condition
        if len(invaders) == 0:
            level += 1
            wave_bonus = 500 * level
            score += wave_bonus
            wave_clear_bonus = 60

            invaders = create_invaders(level)
            invader_speed = 1 + (level * 0.25)
            move_interval = max(3, 35 - level * 2)
            barriers = create_barriers()

            sound_manager.play('level_up')

            for _ in range(30):
                particles.add(Particle(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, GOLD, random.uniform(2, 6), random.randint(2, 5), 60))

            screen.fill(BLACK)
            stars.draw(screen)
            show_text(f"LEVEL {level}", large_font, GREEN, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30)
            show_text(f"Wave Clear Bonus: +{wave_bonus}", font, GOLD, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30)
            pygame.display.flip()
            pygame.time.wait(2000)

        # Drawing
        screen.fill(BLACK)

        shake_x = random.randint(-int(shake_intensity), int(shake_intensity)) if shake_duration > 0 else 0
        shake_y = random.randint(-int(shake_intensity), int(shake_intensity)) if shake_duration > 0 else 0

        stars.draw(screen)

        for sprite in bullets:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in enemy_bullets:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in explosions:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in powerups:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in particles:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in barriers:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in invaders:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in ufos:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))
        for sprite in player_group:
            screen.blit(sprite.image, (sprite.rect.x + shake_x, sprite.rect.y + shake_y))

        # HUD
        show_text(f"Score: {score}", font, WHITE, 15, 15, center=False)

        lives_text = "♥ " * player.lives
        show_text(lives_text, font, RED, SCREEN_WIDTH - 150, 15, center=False)

        show_text(f"Level: {level}", font, YELLOW, SCREEN_WIDTH//2, 15, center=True)

        if combo > 1:
            combo_colors = [WHITE, YELLOW, ORANGE, RED, PURPLE, GOLD]
            combo_color = combo_colors[min(combo, len(combo_colors)-1)]
            show_text(f"COMBO x{combo}!", medium_font, combo_color, SCREEN_WIDTH//2, 60)

        if wave_clear_bonus > 0:
            wave_clear_bonus -= 1
            show_text(f"+{500 * (level-1)} Bonus!", font, GOLD, SCREEN_WIDTH//2, 100)

        draw_powerup_indicators(player, 15, 55)

        draw_health_bar(15, SCREEN_HEIGHT - 30, player.lives, player.max_lives, width=120, height=12)

        sfx_status = "🔊" if sound_manager.sfx_enabled else "🔇"
        show_text(sfx_status, font, WHITE, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 30, center=True)

        show_text("←→ Move | SPACE Shoot | P Pause | ESC Menu | M Sound", small_font, GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 12, center=True)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
