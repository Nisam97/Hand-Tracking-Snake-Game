# **🐍 Hand-Tracking Snake Game using OpenCV & Python**

An interactive Snake Game controlled using real-time hand tracking via a webcam.
The player controls the snake using their index finger, making gameplay intuitive and immersive without keyboard input.

## **🚀 Features**

🖐 Hand Tracking Control

Uses webcam & index finger movement

No keyboard controls for movement

🌈 Rainbow Snake Animation

Smooth body movement with color transitions

🍩 Dynamic Food System

Static food (early levels)

Moving food in higher levels

⛽ Fuel / Hunger System

Fuel drains over time

Eating food refills fuel

Game over when fuel reaches zero

🚧 Obstacles (Level 4+)

Randomly generated obstacles

Collision leads to game over

🧠 Level-Based Difficulty

Increasing speed & complexity

Smaller food & more challenges

🏆 High Score System

High score saved locally (highscore.txt)

💥 Visual Effects

Screen flash on food collection

Game Over overlay screen

## **📈 Level Progression**
| Level | New Challenge                 |
| ----- | ----------------------------- |
| 1     | Basic snake & food            |
| 2     | Faster movement               |
| 3     | Moving food                   |
| 4+    | Obstacles + higher difficulty |

💀 Collision Detection – Game ends if you hit your body or obstacles.

🖼️ UI Overlay – Displays score, level, and game over screen.

## **🛠️ Tech Stack**

Python 3.x

MediaPipe (via cvzone)

OpenCV

 – For image processing & game display
 
CVZone

 – For overlays & hand tracking
 
NumPy

 – For calculations
Math & Random Libraries – For movement & collision logic

## **📂 Project Structure**

📁 HandTracking-SnakeGame/

│── main.py           # Main game script

│── Donut.png         # Food image 

│── README.md         # Project documentation

## **🎮 How to Play**

✋ Show your hand to the camera

👉 Move your index finger to control the snake

🍩 Eat food to grow and gain fuel

🚧 Avoid obstacles and your own body

⛽ Keep an eye on the fuel bar

🔁 Press R to restart after Game Over

❌ Press Q to quit
