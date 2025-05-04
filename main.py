import sys
import sqlite3
import csv
import requests
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from dotenv import load_dotenv, set_key
from pathlib import Path

# Load the .env file if it exists
env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

# Initialize the Genius API token
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")


class GeniusFeatureGame(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Genius Feature Game")
        self.setGeometry(100, 100, 400, 500)
        self.current_artist = None
        self.artist_cache = {}
        self.collaborations_cache = {}
        self.pixmap = None
        self.current_player = 1
        self.starting_player = 1  # Player 1 starts by default
        self.player1_name = "Player 1"
        self.player2_name = "Player 2"
        self.player1_score = 0  # Player 1's score
        self.player2_score = 0  # Player 2's score
        self.db_connection = sqlite3.connect("collaborations.db")  # SQLite database
        self.setup_database()
        self.import_csv_to_db("c:\\Users\\samue\\Datascrape\\rapmap\\edges.csv")  # Import CSV data
        self.setup_ui()

    def setup_database(self):
        """Initialize the database and create the collaborations table if it doesn't exist."""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaborations (
                artist_id TEXT,
                collaborator_name TEXT
            )
        """)
        self.db_connection.commit()

    def import_csv_to_db(self, csv_file_path):
        """Import data from a CSV file into the database."""
        cursor = self.db_connection.cursor()
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                source = row["Source"].strip().lower()
                target = row["Target"].strip().lower()
                # Insert both directions (source -> target and target -> source)
                cursor.execute("INSERT OR IGNORE INTO collaborations (artist_id, collaborator_name) VALUES (?, ?)", (source, target))
                cursor.execute("INSERT OR IGNORE INTO collaborations (artist_id, collaborator_name) VALUES (?, ?)", (target, source))
        self.db_connection.commit()

    def fetch_collaborations(self, artist_id):
        """Fetch all credited artists across the artist's entire discography."""
        # Check the database for cached collaborations
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT collaborator_name FROM collaborations WHERE artist_id = ?", (artist_id,))
        rows = cursor.fetchall()

        if rows:
            # Return cached collaborations
            collaborations = {row[0].lower() for row in rows}
            return collaborations

        # Fetch collaborations from the Genius API
        collaborations = set()
        page = 1  # Start with the first page of results

        while True:
            url = f"https://api.genius.com/artists/{artist_id}/songs?page={page}"
            headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Error fetching collaborations: {response.status_code} - {response.text}")
                break

            data = response.json()
            if "response" not in data or "songs" not in data["response"]:
                print("Unexpected response structure:", data)
                break

            songs = data["response"]["songs"]

            for song in songs:
                try:
                    # Add featured artists and primary artist to collaborations
                    for artist in song.get("featured_artists", []):
                        collaborations.add(artist["name"].lower())
                    collaborations.add(song["primary_artist"]["name"].lower())
                except KeyError as e:
                    print(f"KeyError while processing song data: {e}")

            # Check if there is a next page
            if not data["response"].get("next_page"):
                break
            page += 1

        # Save collaborations to the database
        for collaborator in collaborations:
            cursor.execute("INSERT OR IGNORE INTO collaborations (artist_id, collaborator_name) VALUES (?, ?)", (artist_id, collaborator))
        self.db_connection.commit()

        return collaborations

    def fetch_artist_data(self, artist_name):
        """Fetch artist data from Genius and cache it."""
        if artist_name.lower() in self.artist_cache:
            return self.artist_cache[artist_name.lower()]

        url = f"https://api.genius.com/search?q={artist_name}"
        headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data["response"]["hits"]:
                artist = data["response"]["hits"][0]["result"]["primary_artist"]
                artist_data = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "image_url": artist.get("image_url", None)  # Get the artist's image URL
                }
                self.artist_cache[artist_name.lower()] = artist_data
                return artist_data

        return None

    def set_player_names(self, player1_name, player2_name):
        """Set the names of Player 1 and Player 2."""
        self.player1_name = player1_name if player1_name else "Player 1"
        self.player2_name = player2_name if player2_name else "Player 2"
        self.score_label.setText(f"{self.player1_name}: 0 | {self.player2_name}: 0")
        self.label.setText(f"{self.player1_name}, choose an artist:")

    def closeEvent(self, event):
        """Close the database connection when the application exits."""
        self.db_connection.close()
        event.accept()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Add a horizontal layout for the score label
        score_layout = QHBoxLayout()
        self.score_label = QLabel("Player 1: 0 | Player 2: 0")
        self.score_label.setAlignment(Qt.AlignRight)
        score_layout.addStretch(1)
        score_layout.addWidget(self.score_label)

        # Add the score layout to the main layout
        layout.addLayout(score_layout)

        # Add image display above the label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)  # Center the image
        self.image_label.setStyleSheet("border: none;")  # Remove any border
        self.image_label.setFixedSize(400, 400)  # Set an initial size for the image
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # Add the label below the image
        self.label = QLabel("Player 1, choose an artist:")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Create a horizontal layout for the input and button
        input_button_layout = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setFixedWidth(300)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedWidth(150)

        input_button_layout.addStretch(1)
        input_button_layout.addWidget(self.input)
        input_button_layout.addWidget(self.submit_button)
        input_button_layout.addStretch(1)

        # Add the input and button layout to the main layout
        layout.addLayout(input_button_layout)

        # Add stretch to push everything upwards if the window is resized
        layout.addStretch(1)

        self.setLayout(layout)
        self.submit_button.clicked.connect(self.process_input)

    def process_input(self):
        artist_name = self.input.text().strip()
        if not artist_name:
            QMessageBox.warning(self, "Input Error", "Please enter an artist name.")
            return

        artist_data = self.fetch_artist_data(artist_name)
        if not artist_data:
            QMessageBox.warning(self, "Artist Not Found", f"The artist '{artist_name}' does not exist. Please try again.")
            self.input.clear()
            return

        # Update the artist's image
        if artist_data["image_url"]:
            self.update_artist_image(artist_data["image_url"])
        else:
            self.image_label.clear()  # Clear the image if no image URL is available

        if self.current_artist is None:
            self.current_artist = artist_name
            self.label.setText(f"{self.player2_name if self.current_player == 1 else self.player1_name}, name an artist that features with {self.current_artist}:")
        else:
            current_artist_data = self.fetch_artist_data(self.current_artist)
            if not current_artist_data:
                QMessageBox.warning(self, "Error", f"Failed to fetch data for {self.current_artist}.")
                self.reset_game()
                return

            current_artist_id = current_artist_data["id"]
            input_artist_id = artist_data["id"]

            current_artist_collaborations = self.fetch_collaborations(current_artist_id)
            input_artist_collaborations = self.fetch_collaborations(input_artist_id)

            if artist_name.lower() in current_artist_collaborations or self.current_artist.lower() in input_artist_collaborations:
                QMessageBox.information(self, "Correct", f"Correct! {artist_name} is a valid artist.")
                self.current_artist = artist_name
                next_player = self.player1_name if self.current_player == 2 else self.player2_name
                self.label.setText(f"{next_player}, name an artist that features with {self.current_artist}:")
                self.current_player = 1 if self.current_player == 2 else 2
            else:
                # Award 1 point to the player who caused the mistake
                if self.current_player == 1:
                    self.player2_score += 1
                else:
                    self.player1_score += 1

                QMessageBox.information(self, "Game Over", f"Incorrect! {artist_name} does not feature with {self.current_artist}. Starting a new round!")
                self.update_score_label()
                self.reset_game()

        self.input.clear()

    def update_score_label(self):
        """Update the score label to display the scores for both players."""
        self.score_label.setText(f"{self.player1_name}: {self.player1_score} | {self.player2_name}: {self.player2_score}")
    
    def update_artist_image(self, image_url):
        """Update the image label with the artist's image."""
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_label.setPixmap(
                    pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
            else:
                self.image_label.clear()
        except Exception:
            self.image_label.clear()

    def reset_game(self):
        self.current_artist = None

        # Alternate the starting player
        self.starting_player = 1 if self.starting_player == 2 else 2
        self.current_player = self.starting_player

        starting_player_name = self.player1_name if self.starting_player == 1 else self.player2_name
        self.label.setText(f"{starting_player_name}, choose an artist:")

    def resizeEvent(self, event):
        """Handle window resizing to adjust the image size proportionally to the window."""
        base_font_size = max(10, self.width() // 50)
        font = f"""
            QLabel {{
                font-size: {base_font_size}px;
            }}
            QLineEdit {{
                font-size: {base_font_size}px;
            }}
            QPushButton {{
                font-size: {base_font_size}px;
            }}
        """
        self.setStyleSheet(font)

        # Adjust the image label size proportionally to the window size
        window_width = self.width()
        window_height = self.height()

        # Set the image size to be proportional to the window size (e.g., 40% of width and height)
        image_width = int(window_width * 0.4)
        image_height = int(window_height * 0.4)

        # Apply the new size and position to the image label
        self.image_label.setGeometry(0, 0, image_width, image_height)

        super().resizeEvent(event)


class MainMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title Label
        title_label = QLabel("RAP BATTLE")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Start Game Button
        start_button = QPushButton("Start Game")
        start_button.setFixedSize(200, 50)
        start_button.clicked.connect(self.start_game)

        # Instructions Button
        instructions_button = QPushButton("Instructions")
        instructions_button.setFixedSize(200, 50)
        instructions_button.clicked.connect(self.show_instructions)

        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.setFixedSize(200, 50)
        quit_button.clicked.connect(self.quit_game)

        # Add widgets to the layout
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(start_button, alignment=Qt.AlignCenter)
        layout.addWidget(instructions_button, alignment=Qt.AlignCenter)
        layout.addWidget(quit_button, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        self.setLayout(layout)

    def start_game(self):
        # Test the Genius API connection
        if not self.test_genius_api_connection():
            # Prompt the user to enter their Genius API token
            token_dialog = GeniusApiTokenDialog(self)
            if token_dialog.exec_() == QDialog.Accepted:
                new_token = token_dialog.get_api_token()
                if new_token:
                    global GENIUS_API_TOKEN
                    GENIUS_API_TOKEN = new_token

                    # Retry the connection
                    if not self.test_genius_api_connection():
                        QMessageBox.critical(self, "Error", "Failed to connect to the Genius API. Please check your token.")
                        return
                else:
                    QMessageBox.warning(self, "Error", "No API token provided. Cannot start the game.")
                    return

        # Switch to the game interface
        self.parent.switch_to_game()

    def test_genius_api_connection(self):
        """Test the connection to the Genius API."""
        try:
            headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
            response = requests.get("https://api.genius.com/search?q=test", headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    def show_instructions(self):
        # Show a pop-up dialog with instructions
        QMessageBox.information(self, "Instructions", 
            "Welcome to the Genius Feature Game!\n\n"
            "1. Player 1 starts by choosing an artist.\n"
            "2. Player 2 must name an artist that features with the chosen artist.\n"
            "3. Players alternate turns until someone makes a mistake.\n"
            "4. The player who causes the mistake earns 1 point.\n"
            "5. The game resets, and the next round begins.\n\n"
            "Good luck and have fun!")

    def quit_game(self):
        # Exit the application
        QApplication.quit()


class PlayerNameDialog(QDialog):
    """Dialog to collect Player 1 and Player 2 names."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Player Names")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        # Input for Player 1
        self.player1_input = QLineEdit()
        self.player1_input.setPlaceholderText("Enter Player 1's name")
        layout.addWidget(QLabel("Player 1:"))
        layout.addWidget(self.player1_input)

        # Input for Player 2
        self.player2_input = QLineEdit()
        self.player2_input.setPlaceholderText("Enter Player 2's name")
        layout.addWidget(QLabel("Player 2:"))
        layout.addWidget(self.player2_input)

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def get_player_names(self):
        """Return the entered player names."""
        return self.player1_input.text().strip(), self.player2_input.text().strip()


class GeniusApiTokenDialog(QDialog):
    """Dialog to collect the Genius API token."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Genius API Token")
        self.setGeometry(100, 100, 400, 150)

        layout = QVBoxLayout()

        # Input for Genius API token
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter your Genius API token")
        layout.addWidget(QLabel("Genius API Token:"))
        layout.addWidget(self.token_input)

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def get_api_token(self):
        """Return the entered API token."""
        return self.token_input.text().strip()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAP BATTLE")
        self.setGeometry(100, 100, 800, 600)

        # Check if the Genius API token is available
        global GENIUS_API_TOKEN
        if not GENIUS_API_TOKEN:
            self.prompt_for_api_token()

        self.stack = QStackedWidget()
        self.main_menu = MainMenu(self)
        self.game = GeniusFeatureGame(self)

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.game)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)
        self.stack.setCurrentWidget(self.main_menu)

    def prompt_for_api_token(self):
        """Prompt the user to enter their Genius API token."""
        global GENIUS_API_TOKEN

        # If the token is already loaded from the .env file, skip prompting
        if GENIUS_API_TOKEN:
            return

        token_dialog = GeniusApiTokenDialog(self)
        if token_dialog.exec_() == QDialog.Accepted:
            new_token = token_dialog.get_api_token()
            if new_token:
                # Save the token to the .env file
                set_key(env_path, "GENIUS_API_TOKEN", new_token)
                GENIUS_API_TOKEN = new_token
            else:
                QMessageBox.critical(self, "Error", "No API token provided. Exiting the application.")
                sys.exit(-1)

    def switch_to_game(self):
        dialog = PlayerNameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            player1_name, player2_name = dialog.get_player_names()
            self.game.set_player_names(player1_name, player2_name)
            self.stack.setCurrentWidget(self.game)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())