import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import time
import math
import os
import sys


WIDTH, HEIGHT = 800, 600
GAME_DURATION = 30
SHOOT_COOLDOWN = 0.5
FPS = 30

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Shooter")
clock = pygame.time.Clock()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

shoot_sound = None
try:
    pygame.mixer.init()
    shoot_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'shoot.wav'))
except pygame.error as e:
    print("Audio disabled:", e)


def load_image_cv(path, size=None, alpha=False):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED if alpha else cv2.IMREAD_COLOR)
    if size:
        img = cv2.resize(img, size)
    return img

def cvimg_to_pygame(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA if img.shape[2] == 4 else cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(img.tobytes(), img.shape[1::-1], 'RGBA' if img.shape[2] == 4 else 'RGB')

background_cv = load_image_cv(os.path.join(ASSETS_DIR, 'bg.jpg'), (WIDTH, HEIGHT))
enemy_cv = load_image_cv(os.path.join(ASSETS_DIR, 'enemy.png'), (100, 100), alpha=True)
crosshair_cv = load_image_cv(os.path.join(ASSETS_DIR, 'crosshair.png'), (60, 60), alpha=True)

background = cvimg_to_pygame(background_cv)
enemy_img = cvimg_to_pygame(enemy_cv)
crosshair = cvimg_to_pygame(crosshair_cv)

enemy_rect = enemy_img.get_rect()
enemy_rect.topleft = (random.randint(0, WIDTH - enemy_rect.width), random.randint(0, HEIGHT - enemy_rect.height))


def get_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def handle_gesture(landmarks):
    index_tip = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_tip = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    wrist = landmarks.landmark[mp_hands.HandLandmark.WRIST]
    middle_mcp = landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

    
    pinch_distance = get_distance(index_tip, thumb_tip)
    palm_size = get_distance(wrist, middle_mcp) + 1e-6

    is_pinch = pinch_distance / palm_size < 0.3

    pos = (int(index_tip.x * WIDTH), int(index_tip.y * HEIGHT))
    return is_pinch, pos


gesture_control_enabled = False
score, health = 0, 5
last_shot_time = 0
start_time = time.time()
mouse_x, mouse_y = WIDTH // 2, HEIGHT // 2


cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.3, max_num_hands=1)


running = True
while running:
    clock.tick(FPS)
    elapsed = time.time() - start_time
    shoot = False
    gesture = "NO ACTION"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                gesture_control_enabled = not gesture_control_enabled

    if gesture_control_enabled:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)
            if results.multi_hand_landmarks:
                shoot, (mouse_x, mouse_y) = handle_gesture(results.multi_hand_landmarks[0])
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


cap.release()
hands.close()
if shoot_sound:
    shoot_sound.stop()
    pygame.mixer.quit()


screen.fill((0, 0, 0))
font = pygame.font.SysFont(None, 72)
screen.blit(font.render("GAME OVER", True, (255, 0, 0)), (WIDTH//2 - 180, HEIGHT//2 - 60))
screen.blit(font.render(f"Final Score: {score}", True, (255, 255, 255)), (WIDTH//2 - 180, HEIGHT//2 + 10))
pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
sys.exit()
