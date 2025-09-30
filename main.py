import math
import random
import cvzone
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)

# Moving food for level 3+
class MovingFood:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.target_x, self.target_y = x, y
        self.speed = 2
        self.change_direction_timer = 0

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
        self.points, self.lengths = [], []
        self.currentLength, self.allowedLength = 0, 150
        self.previousHead = (0, 0)
        self.smoothedHead = None

        # Food
        self.foodImg = cv2.imread(foodPath, cv2.IMREAD_UNCHANGED)
        if self.foodImg is None:
            self.foodImg = np.zeros((60, 60, 3), dtype=np.uint8)
            cv2.circle(self.foodImg, (30, 30), 25, (0, 255, 255), -1)
        self.originalFoodSize = (60, 60)
        self.hFood, self.wFood = self.originalFoodSize
        self.foodPoint = (0, 0)
        self.movingFood = None

        # Game state
        self.score, self.level = 0, 1
        self.gameOver = False
        self.smoothing_factor = 0.2
        self.food_size_multiplier = 1.0
        self.obstacles = []

        self.randomFoodLocation()
        self.updateLevelSettings()

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

        dist = math.hypot(cx - px, cy - py)
        if dist > 2:
            self.points.append([cx, cy])
            self.lengths.append(dist)
            self.currentLength += dist
            self.previousHead = (cx, cy)

        while self.currentLength > self.allowedLength and self.lengths:
            self.currentLength -= self.lengths[0]
            self.lengths.pop(0)
            self.points.pop(0)

        return cx, cy

    def checkFoodCollision(self, cx, cy):
        rx, ry = self.foodPoint
        food_hitbox = max(20, int(self.wFood * 0.7))

        if math.hypot(cx - rx, cy - ry) < food_hitbox:
            self.randomFoodLocation()
            self.allowedLength += 50
            self.score += 1
            self.checkLevelUp()
            print(f"Score: {self.score}, Level: {self.level}")

    def checkCollisions(self, cx, cy, px, py):
        # Obstacle collision
        if self.level >= 4 and self.checkObstacleCollision(cx, cy):
            print("Hit obstacle!")
            self.gameOver = True

        # Self-collision
        if len(self.points) >= 6:
            hand_speed = math.hypot(cx - px, cy - py)
            neck_size = 6 if hand_speed < 5 else (8 if hand_speed < 15 else 12)

            pts = np.array(self.points[:-neck_size], np.int32).reshape((-1, 1, 2))
            if len(pts) > 0:
                minDist = cv2.pointPolygonTest(pts, (cx, cy), True)
                tolerance = 2 if hand_speed < 10 else 5
                if -tolerance <= minDist <= tolerance:
                    print("Hit snake body!")
                    self.gameOver = True

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
                self.movingFood = MovingFood(*self.foodPoint)
        elif self.level >= 4:
            self.smoothing_factor, self.food_size_multiplier = 0.25, 0.8
            self.generateObstacles()

        new_h = int(self.originalFoodSize[0] * self.food_size_multiplier)
        new_w = int(self.originalFoodSize[1] * self.food_size_multiplier)
        self.hFood, self.wFood = new_h, new_w
        self.foodImg = cv2.resize(self.foodImg, (new_w, new_h))

    def generateObstacles(self):
        self.obstacles = []
        num_obs = min(3 + (self.level - 4), 8)
        for _ in range(num_obs):
            x, y = random.randint(150, 1100), random.randint(150, 550)
            w, h = random.randint(40, 80), random.randint(40, 80)
            self.obstacles.append((x, y, w, h))

    def randomFoodLocation(self):
        for _ in range(50):
            x, y = random.randint(100, 1100), random.randint(100, 600)
            valid = True
            for ox, oy, ow, oh in self.obstacles:
                if ox <= x <= ox + ow and oy <= y <= oy + oh:
                    valid = False
                    break
            if valid:
                self.foodPoint = (x, y)
                if self.movingFood:
                    self.movingFood.x, self.movingFood.y = x, y
                break

    def checkLevelUp(self):
        if self.score >= self.level * 3 and self.level < 10:
            self.level += 1
            self.updateLevelSettings()
            print(f"Level Up! Now at Level {self.level}")

    def checkObstacleCollision(self, x, y):
        return any(ox <= x <= ox + ow and oy <= y <= oy + oh for ox, oy, ow, oh in self.obstacles)

    def resetGame(self):
        self.points, self.lengths = [], []
        self.currentLength, self.allowedLength = 0, 150
        self.previousHead = (0, 0)
        self.smoothedHead = None
        self.score, self.level = 0, 1
        self.gameOver = False
        self.movingFood = None
        self.randomFoodLocation()
        self.updateLevelSettings()

    # ---------------- DRAWING ---------------- #
    def drawUI(self, imgMain):
        # Obstacles
        if self.level >= 4:
            for ox, oy, ow, oh in self.obstacles:
                cv2.rectangle(imgMain, (ox, oy), (ox + ow, oy + oh), (0, 0, 255), -1)
                cv2.rectangle(imgMain, (ox, oy), (ox + ow, oy + oh), (255, 255, 255), 2)

        # Snake
        if self.points:
            for i in range(1, len(self.points)):
                cv2.line(imgMain, self.points[i - 1], self.points[i], (0, 0, 255), 20)
            cv2.circle(imgMain, self.points[-1], 20, (0, 255, 0), cv2.FILLED)

        # Food
        rx, ry = self.foodPoint
        try:
            imgMain = cvzone.overlayPNG(imgMain, self.foodImg,
                                        (rx - self.wFood // 2, ry - self.hFood // 2))
        except:
            cv2.circle(imgMain, (rx, ry), self.wFood // 2, (0, 255, 255), -1)

        # Score & Level
        cvzone.putTextRect(imgMain, f'Score: {self.score}', [50, 80],
                           scale=3, thickness=3, offset=10)
        cvzone.putTextRect(imgMain, f'Level: {self.level}', [50, 130],
                           scale=2, thickness=2, offset=8)

        return imgMain

    def update(self, imgMain, currentHead):
        if self.gameOver:
            cvzone.putTextRect(imgMain, "Game Over", [400, 300],
                               scale=7, thickness=5, offset=20)
            cvzone.putTextRect(imgMain, f'Your Score: {self.score}', [400, 400],
                               scale=4, thickness=3, offset=15)
            cvzone.putTextRect(imgMain, f'Level Reached: {self.level}', [400, 470],
                               scale=3, thickness=3, offset=15)
            cvzone.putTextRect(imgMain, "Press 'R' to restart", [400, 540],
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
print("🐍 Refactored Snake Game Started!")
print("Controls: Use your index finger to control the snake")
print("Press 'R' to restart, 'Q' to quit")

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

    cv2.imshow("Refactored Snake Game", img)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('r') and game.gameOver:
        game.resetGame()
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
