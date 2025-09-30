🐍 Hand-Tracking Snake Game

A modern twist on the classic Snake Game, powered by OpenCV, CVZone, and AI-based Hand Tracking.
Control the snake using your index finger via a webcam and progress through multiple levels with increasing challenges.

✨ Features

🎮 Hand Tracking Control – Play without a keyboard, just move your finger.

🍩 Food Collection – Collect food to grow longer and increase your score.

🔄 Smooth Movement – The snake head follows your finger with motion smoothing.

🚀 Level System

Level 1–2: Static food with different difficulty.
Level 3: Food starts moving randomly.
Level 4+: Obstacles appear on the board.

💀 Collision Detection – Game ends if you hit your body or obstacles.

🖼️ UI Overlay – Displays score, level, and game over screen.

🛠️ Tech Stack

Python 3.x

OpenCV

 – For image processing & game display
 
CVZone

 – For overlays & hand tracking
 
NumPy

 – For calculations
Math & Random Libraries – For movement & collision logic

📂 Project Structure

📁 HandTracking-SnakeGame/

│── main.py           # Main game script

│── Donut.png         # Food image 

│── README.md         # Project documentation

🎮 Controls

🖐️ Show your index finger to control the snake.

🔄 R – Restart after game over.

❌ Q – Quit the game.
