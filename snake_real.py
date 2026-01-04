import random
import sys
import math
import threading
import os
import io
import wave
import pygame
import numpy as np

# Config
CELL_SIZE = 24
GRID_WIDTH = 28
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
# reserve space at top for HUD
HUD_HEIGHT = 44
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT + HUD_HEIGHT
FPS_DEFAULT = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (8, 10, 12)
GREEN = (34, 139, 34)
GREEN2 = (0, 160, 0)
RED = (200, 0, 0)
GRAY = (40, 40, 40)
ACCENT = (72, 61, 139)

# optional TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False


def speak_async(text):
    if not TTS_AVAILABLE:
        return

    def _run():
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def draw_segment(surface, pos, color):
    cx = pos[0] * CELL_SIZE + CELL_SIZE // 2
    cy = HUD_HEIGHT + pos[1] * CELL_SIZE + CELL_SIZE // 2
    radius = CELL_SIZE // 2 - 2
    pygame.draw.circle(surface, color, (cx, cy), radius)


def random_food_position(snake):
    while True:
        pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if pos not in snake:
            return pos


def show_text(surface, text, size, color, center):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    rect = img.get_rect(center=center)
    surface.blit(img, rect)


def make_sound(frequency=440, duration_ms=150, volume=0.2, sample_rate=44100):
    n_samples = int(sample_rate * duration_ms / 1000)
    if n_samples <= 0:
        return None
    t = np.linspace(0, duration_ms / 1000, n_samples, False)
    waveform = 0.5 * np.sin(2 * np.pi * frequency * t)
    audio = np.int16(waveform * 32767)
    stereo = np.column_stack((audio, audio))
    try:
        sound = pygame.sndarray.make_sound(stereo)
        sound.set_volume(volume)
        return sound
    except Exception:
        return None


def make_pygame_sound_from_freq(frequency=440, duration_ms=150, volume=0.2, sample_rate=44100):
    """Generate a WAV in-memory for a sine tone and load as pygame.mixer.Sound.
    Returns a `pygame.mixer.Sound` or None on failure.
    """
    try:
        n_samples = int(sample_rate * duration_ms / 1000)
        if n_samples <= 0:
            return None
        t = np.linspace(0, duration_ms / 1000, n_samples, False)
        waveform = np.sin(2 * np.pi * frequency * t) * volume
        audio = np.int16(waveform * 32767)
        stereo = np.column_stack((audio, audio)).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(stereo.tobytes())
        buf.seek(0)

        # Try loading via file-like object, fallback to buffer bytes
        try:
            return pygame.mixer.Sound(buf)
        except Exception:
            try:
                buf.seek(0)
                return pygame.mixer.Sound(buffer=buf.read())
            except Exception:
                return None
    except Exception:
        return None


def draw_watermark(surface, text='praveenkanth2805'):
    font = pygame.font.SysFont(None, 18)
    surf = font.render(text, True, (180, 180, 180))
    surf.set_alpha(140)
    rect = surf.get_rect()
    rect.bottomright = (SCREEN_WIDTH - 6, SCREEN_HEIGHT - 6)
    surface.blit(surf, rect)


def menu_select(screen):
    # Show attractive menu and speak the options
    clock = pygame.time.Clock()
    selected = 1  # 0: Easy,1:Medium,2:Hard
    options = ['Easy', 'Medium', 'Hard']
    speeds = {'Easy': 7, 'Medium': 11, 'Hard': 16}

    speak_async('Easy. Medium. Hard')

    show_instructions = False
    instructions_lines = [
        'Controls:',
        '- Arrow keys or WASD to move',
        '- P or Space to pause/resume',
        '- R to restart after game over',
        '- Q or Esc to quit',
        '',
        'Goal: Eat the red food to grow the snake. Avoid colliding with yourself.',
        'The snake wraps at the edges (classic behavior).',
    ]

    hovered = None

    # layout
    menu_top = SCREEN_HEIGHT // 2 - 90
    button_spacing = 70

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if show_instructions:
                    # close instructions with any key (Esc to be explicit)
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        show_instructions = False
                        speak_async('Back')
                else:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % 3
                        speak_async(options[selected])
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % 3
                        speak_async(options[selected])
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        speak_async(options[selected])
                        return options[selected], speeds[options[selected]]
                    elif event.key in (pygame.K_i,):
                        show_instructions = True
                        speak_async('Instructions')
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if show_instructions:
                    # Back button area
                    bx = SCREEN_WIDTH // 2 - 90
                    by = SCREEN_HEIGHT - 120
                    bw = 180
                    bh = 48
                    if bx <= mx <= bx + bw and by <= my <= by + bh:
                        show_instructions = False
                        speak_async('Back')
                else:
                    # compute button areas for difficulties
                    for i in range(3):
                        bx = SCREEN_WIDTH // 2 - 120
                        by = menu_top + i * button_spacing
                        bw = 240
                        bh = 56
                        if bx <= mx <= bx + bw and by <= my <= by + bh:
                            speak_async(options[i])
                            return options[i], speeds[options[i]]
                    # instructions opened via keyboard only; no clickable button
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if not show_instructions:
                    hovered = None
                    for i in range(3):
                        bx = SCREEN_WIDTH // 2 - 120
                        by = menu_top + i * button_spacing
                        bw = 240
                        bh = 56
                        if bx <= mx <= bx + bw and by <= my <= by + bh:
                            hovered = i
                            break

        # background gradient
        for i in range(SCREEN_HEIGHT):
            ratio = i / SCREEN_HEIGHT
            r = int(BLACK[0] * (1 - ratio) + ACCENT[0] * ratio)
            g = int(BLACK[1] * (1 - ratio) + ACCENT[1] * ratio)
            b = int(BLACK[2] * (1 - ratio) + ACCENT[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))

        # title
        show_text(screen, 'Snake — Classic', 56, WHITE, (SCREEN_WIDTH // 2, 80))
        show_text(screen, 'Choose Mode', 28, (220, 220, 220), (SCREEN_WIDTH // 2, 130))

        # buttons (centered, with hover/selected scaling)
        for i, opt in enumerate(options):
            bw = 240
            bh = 56
            by = menu_top + i * button_spacing
            base_x = SCREEN_WIDTH // 2
            is_active = (i == selected) or (hovered == i)
            scale = 1.06 if is_active and not show_instructions else 1.0
            w = int(bw * scale)
            h = int(bh * scale)
            rect = pygame.Rect(0, 0, w, h)
            rect.center = (base_x, by + bh // 2)
            color = (110, 110, 170) if i == selected else (70, 70, 110) if hovered == i else (60, 60, 100)
            pygame.draw.rect(screen, color, rect, border_radius=12)
            show_text(screen, opt, 28, WHITE, rect.center)

        # small hint (instructions accessible via 'I')
        hint_y = menu_top + 3 * button_spacing + 18
        show_text(screen, 'Press I for Instructions', 16, (200, 200, 200), (SCREEN_WIDTH // 2, hint_y))

        # watermark small
        draw_watermark(screen)

        # if instructions overlay active, draw modal
        if show_instructions:
            overlay = pygame.Surface((SCREEN_WIDTH - 120, SCREEN_HEIGHT - 160))
            overlay.fill((18, 20, 28))
            overlay.set_alpha(230)
            ox = 60
            oy = 80
            screen.blit(overlay, (ox, oy))

            # render instruction text lines
            for idx, line in enumerate(instructions_lines):
                y = oy + 24 + idx * 34
                show_text(screen, line, 22 if idx > 0 else 26, (230, 230, 230), (SCREEN_WIDTH // 2, y))

            # back button
            bx = SCREEN_WIDTH // 2 - 90
            by = SCREEN_HEIGHT - 120
            bw = 180
            bh = 48
            pygame.draw.rect(screen, (100, 60, 60), (bx, by, bw, bh), border_radius=10)
            show_text(screen, 'Back', 22, WHITE, (SCREEN_WIDTH // 2, by + bh // 2))

        pygame.display.flip()
        clock.tick(30)


def game_loop(difficulty='Medium', fps=FPS_DEFAULT):
    # Prefer a configured mixer before initializing pygame to improve audio reliability
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Snake (Python)')
    clock = pygame.time.Clock()

    # try to init mixer and create sounds
    eat_sound = None
    game_over_sound = None
    pause_sound = None
    try:
        pygame.mixer.init()
        # prefer user-provided WAVs under assets/sounds
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sounds')
        eat_path = os.path.join(base, 'eat.wav')
        pause_path = os.path.join(base, 'pause.wav')
        gameover_path = os.path.join(base, 'game_over.wav')

        if os.path.exists(eat_path):
            eat_sound = pygame.mixer.Sound(eat_path)
        else:
            eat_sound = make_pygame_sound_from_freq(900, 90, 0.15) or make_sound(900, 90, 0.15)

        if os.path.exists(pause_path):
            pause_sound = pygame.mixer.Sound(pause_path)
        else:
            pause_sound = make_pygame_sound_from_freq(600, 80, 0.12) or make_sound(600, 80, 0.12)

        if os.path.exists(gameover_path):
            game_over_sound = pygame.mixer.Sound(gameover_path)
        else:
            game_over_sound = make_pygame_sound_from_freq(150, 650, 0.22) or make_sound(150, 650, 0.22)
    except Exception:
        # fallback to synthesized sounds if mixer or files unavailable
        try:
            eat_sound = eat_sound or make_sound(frequency=900, duration_ms=90, volume=0.15)
            pause_sound = pause_sound or make_sound(frequency=600, duration_ms=80, volume=0.12)
            game_over_sound = game_over_sound or make_sound(frequency=150, duration_ms=650, volume=0.22)
        except Exception:
            eat_sound = pause_sound = game_over_sound = None

    # initialize snake
    start_x = GRID_WIDTH // 2
    start_y = GRID_HEIGHT // 2
    snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
    direction = (1, 0)
    food = random_food_position(snake)
    score = 0
    running = True
    game_over = False
    played_game_over_sound = False

    # map difficulty to speed
    speed = fps
    if difficulty == 'Easy':
        speed = 7
    elif difficulty == 'Medium':
        speed = 11
    elif difficulty == 'Hard':
        speed = 16

    paused = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_p, pygame.K_SPACE) and not game_over:
                    # toggle pause
                    paused = not paused
                    if pause_sound:
                        try:
                            pause_sound.play()
                        except Exception:
                            pass
                    continue
                if not game_over:
                    if event.key in (pygame.K_UP, pygame.K_w) and direction != (0, 1):
                        direction = (0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and direction != (0, -1):
                        direction = (0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and direction != (1, 0):
                        direction = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0):
                        direction = (1, 0)
                else:
                    if event.key == pygame.K_r:
                        return game_loop(difficulty, fps)
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False

        if not game_over and not paused:
            head_x, head_y = snake[0]
            dx, dy = direction
            # wrap around edges so snake stays within grid (classic behavior)
            new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)

            # self collision -> game over
            if new_head in snake:
                game_over = True

            if not game_over:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 1
                    if eat_sound:
                        try:
                            eat_sound.play()
                        except Exception:
                            pass
                    food = random_food_position(snake)
                else:
                    snake.pop()

        # draw background
        screen.fill((12, 14, 18))

        # top HUD bar (rounded translucent panel)
        hud_w = SCREEN_WIDTH - 20
        hud_h = HUD_HEIGHT
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        hud_surf.fill((20, 24, 40, 220))
        screen.blit(hud_surf, (10, 6))
        pygame.draw.rect(screen, (28, 32, 52), (10, 6, hud_w, hud_h), width=1, border_radius=8)
        show_text(screen, f'Score: {score}', 22, WHITE, (100, 28))
        show_text(screen, f'Difficulty: {difficulty}', 18, (200, 200, 200), (SCREEN_WIDTH - 140, 28))
        # small FPS display
        show_text(screen, f'FPS: {int(clock.get_fps())}', 14, (160, 160, 160), (SCREEN_WIDTH - 50, 14))

        # grid lines (subtle)
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (x, HUD_HEIGHT), (x, SCREEN_HEIGHT))
        for y in range(HUD_HEIGHT, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

        # draw pulsing food as circle (offset by HUD)
        fx = food[0] * CELL_SIZE + CELL_SIZE // 2
        fy = HUD_HEIGHT + food[1] * CELL_SIZE + CELL_SIZE // 2
        t = pygame.time.get_ticks() / 250.0
        pulse = int(math.sin(t) * 2.0)
        fradius = max(4, CELL_SIZE // 2 - 4 + pulse)
        pygame.draw.circle(screen, RED, (fx, fy), fradius)

        # draw snake segments
        for i, seg in enumerate(snake):
            color = GREEN if i == 0 else GREEN2
            draw_segment(screen, seg, color)

        # head eyes (apply HUD offset)
        head = snake[0]
        hx = head[0] * CELL_SIZE + CELL_SIZE // 2
        hy = HUD_HEIGHT + head[1] * CELL_SIZE + CELL_SIZE // 2
        eye_offset = CELL_SIZE // 3
        dx, dy = direction
        if dx > 0:
            eye1 = (hx + eye_offset // 2, hy - eye_offset // 3)
            eye2 = (hx + eye_offset // 2, hy + eye_offset // 3)
        elif dx < 0:
            eye1 = (hx - eye_offset // 2, hy - eye_offset // 3)
            eye2 = (hx - eye_offset // 2, hy + eye_offset // 3)
        elif dy > 0:
            eye1 = (hx - eye_offset // 3, hy + eye_offset // 2)
            eye2 = (hx + eye_offset // 3, hy + eye_offset // 2)
        else:
            eye1 = (hx - eye_offset // 3, hy - eye_offset // 2)
            eye2 = (hx + eye_offset // 3, hy - eye_offset // 2)
        pygame.draw.circle(screen, BLACK, eye1, max(1, CELL_SIZE // 10))
        pygame.draw.circle(screen, BLACK, eye2, max(1, CELL_SIZE // 10))

        # watermark
        draw_watermark(screen)

        if paused and not game_over:
            show_text(screen, 'PAUSED', 48, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        if game_over:
            if game_over_sound and not played_game_over_sound:
                try:
                    game_over_sound.play()
                except Exception:
                    pass
                played_game_over_sound = True
            show_text(screen, 'GAME OVER', 56, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            show_text(screen, f'Final Score: {score}', 32, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            show_text(screen, 'Press R to restart or Q to quit', 20, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 56))

        pygame.display.flip()
        clock.tick(speed)

    pygame.quit()
    sys.exit()


def start_game():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    difficulty, speed = menu_select(screen)
    game_loop(difficulty, speed)


if __name__ == '__main__':
    start_game()