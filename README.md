# RAP BATTLE: Genius Feature Game 🎤

RAP BATTLE is a fun and interactive two-player game where players test their knowledge of musical collaborations. The game is powered by the Genius API, allowing players to explore artists and their featured collaborations in a competitive and engaging way.

---

## How to Play 

1. **Start the Game**:
   - Enter the names of Player 1 and Player 2.
   - Player 1 starts by choosing an artist.

2. **Take Turns**:
   - Players alternate turns, naming an artist that has collaborated with the previously mentioned artist.
   - The game fetches collaboration data from the Genius API to validate the answers.

3. **Make a Mistake**:
   - If a player names an artist that has not collaborated with the current artist, the round ends.
   - The other player earns 1 point, and a new round begins.

4. **Win the Game**:
   - The game continues until players decide to quit. The player with the highest score wins!

---

## Features 

- **Dynamic Gameplay**:
  - Fetches real-time collaboration data using the Genius API.
  - Automatically validates player inputs.

- **Score Tracking**:
  - Keeps track of scores for both players across multiple rounds.

- **Interactive UI**:
  - Built with PyQt5 for a smooth and user-friendly experience.

- **Customizable**:
  - Players can input their own Genius API token to access the Genius database.

- **Error Handling**:
  - Handles invalid artist names, API errors, and unexpected scenarios gracefully.

---

## Requirements 🛠️

- Python 3.10 or higher
- Genius API token (required for fetching artist data)

### Python Libraries:
- `PyQt5`
- `requests`
- `python-dotenv`

Install the required libraries using:
```bash
pip install -r requirements.txt
```

---

## Setup 🚀

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/rap-battle.git
   cd rap-battle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Genius API token:
   - When you run the game for the first time, you will be prompted to enter your Genius API token.
   - The token will be saved in a .env file for future use.

4. Run the game:
   ```bash
   python indgame.py
   ```

---

## Contributing 

Contributions are welcome! Feel free to open issues or submit pull requests to improve the game.

---

## License 

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 🔽 Download

**[Click here to download Rap Battle for Windows](https://github.com/maniiaak/RapBattle/releases/download/windows/RapBattle.zip)**

---
Enjoy the game and test your music knowledge! 