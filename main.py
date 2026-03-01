import math
import random
import cvzone
import cv2
import numpy as np
import time
from collections import deque
from cvzone.HandTrackingModule import HandDetector
import os

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)


# Moving food class (for level 3+)
class MovingObject:
    def __init__(self, x, y, speed=2, is_obstacle=False):
        self.x, self.y = x, y
        self.target_x, self.target_y = x, y
        self.speed = speed
        self.change_direction_timer = 0
        self.is_obstacle = is_obstacle

    def update(self):
        self.change_direction_timer += 1
        if self.change_direction_timer > 60:
            self.target_x = random.randint(100, 1000)
            self.target_y = random.randint(100, 600)
            self.change_direction_timer = 0

        dx, dy = self.target_x - self.x, self.target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > self.speed:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        return int(self.x), int(self.y)


class SnakeGame:
    def __init__(self, foodPath="Donut.png"):
        self.points = deque(maxlen=2000)
        self.lengths = deque(maxlen=2000)
        self.currentLength, self.allowedLength = 0, 150
        self.previousHead = (0, 0)
        self.smoothedHead = None

        # FEATURE: High Score System
        self.high_score = 0
        self.loadHighScore()

        # FEATURE: Screen Flash Effect
        self.flash_timer = 0

        # Food
        self.foodImg = cv2.imread(foodPath, cv2.IMREAD_UNCHANGED)
        if self.foodImg is None:
            self.foodImg = np.zeros((60, 60, 3), dtype=np.uint8)
            cv2.circle(self.foodImg, (30, 30), 25, (0, 255, 255), -1)

        self.originalFoodSize = (60, 60)
        self.hFood, self.wFood = self.originalFoodSize
        self.foodPoint = (0, 0)
        self.movingFood = None
        self.currentFoodImg = self.foodImg

        # Game state
        self.score, self.level = 0, 1
        self.gameOver = False
        self.gameOverReason = ""
        self.smoothing_factor = 0.2
        self.food_size_multiplier = 1.0
        self.obstacles = []

        # Hunger/Fuel System
        self.max_hunger = 300
        self.current_hunger = self.max_hunger
        self.last_time = time.time()

        self.generateObstacles()  # Initialize obstacles list
        self.randomFoodLocation()
        self.updateLevelSettings()

    def loadHighScore(self):
        if os.path.exists("highscore.txt"):
            with open("highscore.txt", "r") as f:
                try:
                    self.high_score = int(f.read())
                except:
                    self.high_score = 0

    def saveHighScore(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))

    # ---------------- GAME LOGIC ---------------- #
    def moveSnake(self, currentHead):
        px, py = self.previousHead
        cx, cy = currentHead

        if self.smoothedHead is None:
            self.smoothedHead = [cx, cy]
        else:
            alpha = self.smoothing_factor
            self.smoothedHead[0] = int(self.smoothedHead[0] * (1 - alpha) + cx * alpha)
            self.smoothedHead[1] = int(self.smoothedHead[1] * (1 - alpha) + cy * alpha)
            cx, cy = self.smoothedHead

        dx, dy = cx - px, cy - py
        dist_sq = dx * dx + dy * dy

        if dist_sq > 4:
            dist = math.sqrt(dist_sq)
            self.points.append([cx, cy])
            self.lengths.append(dist)
            self.currentLength += dist
            self.previousHead = (cx, cy)

        while self.currentLength > self.allowedLength and self.lengths:
            self.currentLength -= self.lengths[0]
            self.lengths.popleft()
            self.points.popleft()

        return cx, cy

    def updateHunger(self, imgMain):
        if self.gameOver: return imgMain

        current_time = time.time()
        if current_time - self.last_time > 0.1:
            drain_amount = 1.0 + (self.level * 0.1)
            self.current_hunger -= drain_amount
            self.last_time = current_time

        if self.current_hunger <= 0:
            self.current_hunger = 0
            self.gameOver = True
            self.gameOverReason = "Out of Fuel!"

        # Draw Fuel Bar
        bar_x, bar_y = 850, 50
        bar_w, bar_h = 300, 30
        fill_ratio = max(0, self.current_hunger / self.max_hunger)
        fill_w = int(bar_w * fill_ratio)

        if self.current_hunger > self.max_hunger * 0.5:
            color = (0, 255, 0)
        elif self.current_hunger > self.max_hunger * 0.2:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        cv2.rectangle(imgMain, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), 3)
        cv2.rectangle(imgMain, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), color, -1)
        cvzone.putTextRect(imgMain, "Fuel", [bar_x, bar_y - 10], scale=1.5, thickness=2, offset=5)

        return imgMain

    def checkFoodCollision(self, cx, cy):
        rx, ry = self.foodPoint
        food_hitbox = max(20, int(self.wFood * 0.7))

        if math.hypot(cx - rx, cy - ry) < food_hitbox:
            self.randomFoodLocation()
            self.allowedLength += 50
            self.score += 1

            # Update High Score
            if self.score > self.high_score:
                self.high_score = self.score
                self.saveHighScore()

            # Trigger Flash Effect
            self.flash_timer = 3

            # Refill Hunger
            self.current_hunger = min(self.max_hunger, self.current_hunger + 80)

            self.checkLevelUp()
            print(f"Score: {self.score}, Level: {self.level}")

    def checkCollisions(self, cx, cy, px, py):
        # Obstacle
        if self.level >= 4 and self.checkObstacleCollision(cx, cy):
            self.gameOver = True
            self.gameOverReason = "Hit Obstacle!"

        # Self
        if len(self.points) >= 6:
            hand_speed = math.hypot(cx - px, cy - py)
            neck_size = 6 if hand_speed < 5 else (8 if hand_speed < 15 else 12)
            pts_list = list(self.points)
            pts = np.array(pts_list[:-neck_size], np.int32).reshape((-1, 1, 2))

            if len(pts) > 0:
                minDist = cv2.pointPolygonTest(pts, (cx, cy), True)
                tolerance = 2 if hand_speed < 10 else 5
                if -tolerance <= minDist <= tolerance:
                    self.gameOver = True
                    self.gameOverReason = "Bit Yourself!"

    # ---------------- LEVEL / GAME STATE ---------------- #
    def updateLevelSettings(self):
        if self.level == 1:
            self.smoothing_factor, self.food_size_multiplier = 0.1, 1.0
            self.obstacles, self.movingFood = [], None
        elif self.level == 2:
            self.smoothing_factor, self.food_size_multiplier = 0.2, 0.6
            self.obstacles, self.movingFood = [], None
        elif self.level == 3:
            self.smoothing_factor, self.food_size_multiplier = 0.2, 0.7
            self.obstacles = []
            if self.movingFood is None:
                self.movingFood = MovingObject(*self.foodPoint)
        elif self.level >= 4:
            self.smoothing_factor, self.food_size_multiplier = 0.25, 0.8
            self.generateObstacles()

        new_h = int(self.originalFoodSize[0] * self.food_size_multiplier)
        new_w = int(self.originalFoodSize[1] * self.food_size_multiplier)
        self.hFood, self.wFood = new_h, new_w
        self.currentFoodImg = cv2.resize(self.foodImg, (new_w, new_h))

    def generateObstacles(self):
        self.obstacles = []
        num_obs = min(3 + (self.level - 4), 8)
        for _ in range(num_obs):
            x, y = random.randint(150, 1100), random.randint(150, 550)
            w, h = random.randint(40, 80), random.randint(40, 80)
            self.obstacles.append((x, y, w, h))

    def randomFoodLocation(self):
        # Exclusion Zones (Score Area and Fuel Area)
        zone_score = (0, 0, 450, 200)  # Increased slightly for high score text
        zone_fuel = (800, 0, 1280, 150)

        for _ in range(100):
            x = random.randint(100, 1100)
            y = random.randint(100, 600)
            valid = True

            for ox, oy, ow, oh in self.obstacles:
                if ox - 20 <= x <= ox + ow + 20 and oy - 20 <= y <= oy + oh + 20:
                    valid = False;
                    break

            if valid:
                if (zone_score[0] <= x <= zone_score[2] and zone_score[1] <= y <= zone_score[3]) or \
                        (zone_fuel[0] <= x <= zone_fuel[2] and zone_fuel[1] <= y <= zone_fuel[3]):
                    valid = False

            if valid:
                self.foodPoint = (x, y)
                if self.movingFood:
                    self.movingFood.x, self.movingFood.y = x, y
                return
        self.foodPoint = (640, 360)

    def checkLevelUp(self):
        if self.score >= self.level * 3 and self.level < 10:
            self.level += 1
            self.updateLevelSettings()

    def checkObstacleCollision(self, x, y):
        return any(ox <= x <= ox + ow and oy <= y <= oy + oh for ox, oy, ow, oh in self.obstacles)

    def resetGame(self):
        self.points = deque(maxlen=2000)
        self.lengths = deque(maxlen=2000)
        self.currentLength, self.allowedLength = 0, 150
        self.previousHead = (0, 0)
        self.smoothedHead = None
        self.score, self.level = 0, 1
        self.gameOver = False
        self.gameOverReason = ""
        self.movingFood = None
        self.current_hunger = self.max_hunger
        self.last_time = time.time()
        self.randomFoodLocation()
        self.updateLevelSettings()

    # ---------------- DRAWING ---------------- #
    def drawUI(self, imgMain):
        # Obstacles
        if self.level >= 4:
            for ox, oy, ow, oh in self.obstacles:
                cv2.rectangle(imgMain, (ox, oy), (ox + ow, oy + oh), (0, 0, 255), -1)
                cv2.rectangle(imgMain, (ox, oy), (ox + ow, oy + oh), (255, 255, 255), 2)

        # FEATURE: Rainbow Snake
        if self.points:
            pts_list = list(self.points)
            for i in range(1, len(pts_list)):
                # Calculate rainbow color based on index
                hue = int((i * 10 + self.score * 5) % 180)
                color_hsv = np.uint8([[[hue, 255, 255]]])
                color_bgr = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2BGR)[0][0]
                color_tuple = (int(color_bgr[0]), int(color_bgr[1]), int(color_bgr[2]))

                cv2.line(imgMain, tuple(pts_list[i - 1]), tuple(pts_list[i]), color_tuple, 20)

            # Head
            cv2.circle(imgMain, tuple(pts_list[-1]), 20, (0, 255, 0), cv2.FILLED)

        # Food
        rx, ry = self.foodPoint
        try:
            imgMain = cvzone.overlayPNG(imgMain, self.currentFoodImg,
                                        (rx - self.wFood // 2, ry - self.hFood // 2))
        except:
            cv2.circle(imgMain, (rx, ry), self.wFood // 2, (0, 255, 255), -1)

        # Score, Level, & High Score
        cvzone.putTextRect(imgMain, f'Score: {self.score}', [50, 80],
                           scale=3, thickness=3, offset=10)
        cvzone.putTextRect(imgMain, f'Level: {self.level}', [50, 130],
                           scale=2, thickness=2, offset=8)

        # Draw High Score
        cvzone.putTextRect(imgMain, f'Best: {self.high_score}', [50, 180],
                           scale=2, thickness=2, offset=8, colorR=(200, 200, 0))

        # Fuel Bar
        self.updateHunger(imgMain)

        # FEATURE: Screen Flash
        if self.flash_timer > 0:
            overlay = imgMain.copy()
            cv2.rectangle(overlay, (0, 0), (1280, 720), (255, 255, 255), -1)
            cv2.addWeighted(overlay, 0.3, imgMain, 0.7, 0, imgMain)
            self.flash_timer -= 1

        return imgMain

    def update(self, imgMain, currentHead):
        if self.gameOver:
            cvzone.putTextRect(imgMain, "Game Over", [400, 250],
                               scale=7, thickness=5, offset=20, colorR=(0, 0, 255))
            cvzone.putTextRect(imgMain, f'{self.gameOverReason}', [450, 350],
                               scale=3, thickness=3, offset=10, colorR=(0, 0, 0))
            cvzone.putTextRect(imgMain, f'Score: {self.score}', [400, 430],
                               scale=4, thickness=3, offset=15)
            cvzone.putTextRect(imgMain, f'Best: {self.high_score}', [800, 430],
                               scale=4, thickness=3, offset=15, colorR=(200, 200, 0))
            cvzone.putTextRect(imgMain, "Press 'R' to restart", [400, 520],
                               scale=3, thickness=3, offset=15)
            return imgMain

        px, py = self.previousHead
        cx, cy = self.moveSnake(currentHead)

        if self.level >= 3 and self.movingFood:
            self.foodPoint = self.movingFood.update()

        self.checkFoodCollision(cx, cy)
        self.checkCollisions(cx, cy, px, py)
        return self.drawUI(imgMain)


# ---------------- MAIN LOOP ---------------- #
game = SnakeGame("Donut.png")
print("Ultimate Snake Game Started!")
print("Controls: Index finger to move.")
print("Features: Fuel Bar, Rainbow Snake, Moving Obstacles, High Score Save.")

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)

    hands, img = detector.findHands(img, flipType=False)
    if hands:
        pointIndex = hands[0]['lmList'][8][0:2]
        img = game.update(img, pointIndex)
    else:
        cvzone.putTextRect(img, "Show your hand to start!", [400, 360],
                           scale=3, thickness=3, offset=15)

    cv2.imshow("Snake Game", img)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('r') and game.gameOver:
        game.resetGame()
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
