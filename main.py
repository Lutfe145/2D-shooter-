import pygame
import random
import time
import math
import os
import sys


WIDTH, HEIGHT = 800, 600
GAME_DURATION = 30
SHOOT_COOLDOWN = 0.5
FPS = 30

pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Shooter")
clock = pygame.time.Clock()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

shoot_sound = None
sound_path = os.path.join(ASSETS_DIR, 'shoot.wav')
if os.path.isfile(sound_path):
    try:
        pygame.mixer.init()
        shoot_sound = pygame.mixer.Sound(sound_path)
    except (OSError, pygame.error) as error:
        print("Audio disabled:", error)


def load_image(filename, size, fallback, *, alpha=False):
    try:
        image = pygame.image.load(os.path.join(ASSETS_DIR, filename))
    except (OSError, pygame.error):
        return fallback(size)
    image = image.convert_alpha() if alpha else image.convert()
    return pygame.transform.smoothscale(image, size)


def make_background(size):
    surface = pygame.Surface(size)
    surface.fill((18, 29, 43))
    width, height = size
    grid_color = (29, 46, 63)
    for x in range(0, width, 50):
        pygame.draw.line(surface, grid_color, (x, 0), (x, height - 1))
    for y in range(0, height, 50):
        pygame.draw.line(surface, grid_color, (0, y), (width - 1, y))
    return surface


def make_target(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    center = surface.get_rect().center
    radius = min(size) // 2
    pygame.draw.circle(surface, (245, 112, 91), center, radius - 4, 4)
    pygame.draw.circle(surface, (193, 52, 79), center, radius * 2 // 3)
    pygame.draw.circle(surface, (255, 226, 159), center, radius // 4)
    return surface


def make_crosshair(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    x, y = surface.get_rect().center
    radius = min(size) // 3
    color = (145, 244, 255)
    pygame.draw.circle(surface, color, (x, y), radius, 2)
    pygame.draw.line(surface, color, (x - radius - 5, y), (x + radius + 5, y), 2)
    pygame.draw.line(surface, color, (x, y - radius - 5), (x, y + radius + 5), 2)
    return surface


background = load_image('bg.jpg', (WIDTH, HEIGHT), make_background)
enemy_img = load_image('enemy.png', (100, 100), make_target, alpha=True)
crosshair = load_image('crosshair.png', (60, 60), make_crosshair, alpha=True)

enemy_rect = enemy_img.get_rect()
enemy_rect.topleft = (random.randint(0, WIDTH - enemy_rect.width), random.randint(0, HEIGHT - enemy_rect.height))


def get_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)


def handle_gesture(landmarks, hand_landmark):
    index_tip = landmarks.landmark[hand_landmark.INDEX_FINGER_TIP]
    thumb_tip = landmarks.landmark[hand_landmark.THUMB_TIP]
    wrist = landmarks.landmark[hand_landmark.WRIST]
    middle_mcp = landmarks.landmark[hand_landmark.MIDDLE_FINGER_MCP]

    
    pinch_distance = get_distance(index_tip, thumb_tip)
    palm_size = get_distance(wrist, middle_mcp) + 1e-6

    is_pinch = pinch_distance / palm_size < 0.3

    pos = (int(index_tip.x * WIDTH), int(index_tip.y * HEIGHT))
    return is_pinch, pos


def open_gesture_input():
    try:
        import cv2
        import mediapipe as mp

        hands_api = mp.solutions.hands
    except (ImportError, AttributeError, OSError) as error:
        print(f"Gesture mode unavailable. See the README for setup: {error}")
        return None

    camera = None
    try:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise RuntimeError("Could not open webcam 0.")
        detector = hands_api.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.3,
            max_num_hands=1,
        )
    except (cv2.error, OSError, RuntimeError, ValueError) as error:
        if camera is not None:
            camera.release()
        print(f"Gesture mode unavailable: {error}")
        return None
    return cv2, camera, hands_api.HandLandmark, detector


def close_gesture_input(gesture_input):
    _, camera, _, detector = gesture_input
    camera.release()
    detector.close()


gesture_input = None
score, health = 0, 5
last_shot_time = 0
start_time = time.time()
mouse_x, mouse_y = WIDTH // 2, HEIGHT // 2


running = True
while running:
    clock.tick(FPS)
    elapsed = time.time() - start_time
    shoot = False
    gesture = "NO ACTION"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            if gesture_input is None:
                gesture_input = open_gesture_input()
            else:
                close_gesture_input(gesture_input)
                gesture_input = None

    gesture_control_enabled = gesture_input is not None
    if gesture_input is not None:
        cv2, camera, hand_landmark, detector = gesture_input
        ret, frame = camera.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            if results.multi_hand_landmarks:
                shoot, (mouse_x, mouse_y) = handle_gesture(
                    results.multi_hand_landmarks[0], hand_landmark
                )
                if shoot:
                    gesture = "SHOOT"
    else:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        shoot = pygame.mouse.get_pressed()[0]
        if shoot:
            gesture = "SHOOT"

    
    now = time.time()
    if shoot and now - last_shot_time > SHOOT_COOLDOWN:
        if enemy_rect.collidepoint(mouse_x, mouse_y):
            score += 1
            enemy_rect.topleft = (random.randint(0, WIDTH - enemy_rect.width), random.randint(0, HEIGHT - enemy_rect.height))
        else:
            health -= 1
        last_shot_time = now
        if shoot_sound:
            shoot_sound.play()

    if health <= 0 or elapsed >= GAME_DURATION:
        running = False

   
    screen.blit(background, (0, 0))
    screen.blit(enemy_img, enemy_rect)
    screen.blit(crosshair, (mouse_x - 30, mouse_y - 30))

    font = pygame.font.SysFont(None, 36)
    screen.blit(font.render(f"Gesture: {gesture}", True, (0, 255, 0)), (10, 10))
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 40))
    screen.blit(font.render(f"Health: {health}", True, (0, 100, 255)), (10, 70))
    screen.blit(font.render(f"Time: {max(0, GAME_DURATION - elapsed):.1f}s", True, (255, 255, 0)), (10, 100))
    screen.blit(font.render(f"Gesture Mode: {gesture_control_enabled}", True, (255, 255, 0)), (WIDTH - 300, 10))

    pygame.display.flip()


if gesture_input is not None:
    close_gesture_input(gesture_input)
if shoot_sound:
    shoot_sound.stop()
if pygame.mixer.get_init():
    pygame.mixer.quit()


screen.fill((0, 0, 0))
font = pygame.font.SysFont(None, 72)
screen.blit(font.render("GAME OVER", True, (255, 0, 0)), (WIDTH//2 - 180, HEIGHT//2 - 60))
screen.blit(font.render(f"Final Score: {score}", True, (255, 255, 255)), (WIDTH//2 - 180, HEIGHT//2 + 10))
pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
sys.exit()
