from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random
import string
import os

app = Flask(__name__)
# Enable CORS for Svelte frontend
CORS(app)

games = {}

def load_word_list():
    """Load words from wordlist.txt into a set for fast lookup"""
    word_set = set()
    wordlist_path = os.path.join(os.path.dirname(__file__), 'wordlist.txt')
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    word_set.add(word)
        return word_set
    except FileNotFoundError:
        print(f"Warning: wordlist.txt not found at {wordlist_path}")
        print("Falling back to empty word list. Please add wordlist.txt to the project directory.")
        return set()
    except Exception as e:
        print(f"Error loading wordlist.txt: {e}")
        return set()

VALID_WORDS = load_word_list()

class BoggleGame:
    def __init__(self, game_id):
        self.game_id = game_id
        self.board = self.generate_board()
        self.found_words = []
        self.score = 0
    
    def generate_board(self):
        """Generate a 4x4 grid with random letters"""
        board = []
        for _ in range(4):
            row = []
            for _ in range(4):
                letter = random.choice(string.ascii_uppercase)
                row.append(letter)
            board.append(row)
        return board
    
    def is_valid_path(self, positions):
        """Check if positions form a valid connected path"""
        if len(positions) < 3:
            return False
        
        # Check for duplicates
        position_tuples = [tuple(pos) for pos in positions]
        if len(position_tuples) != len(set(position_tuples)):
            return False
        
        # Check if all positions are within bounds
        for r, c in positions:
            if not (0 <= r < 4 and 0 <= c < 4):
                return False
        
        # Check if all consecutive positions are adjacent (horizontal, vertical, or diagonal)
        for i in range(len(positions) - 1):
            r1, c1 = positions[i]
            r2, c2 = positions[i + 1]
            
            dr = abs(r1 - r2)
            dc = abs(c1 - c2)
            
            # Must be adjacent (max distance of 1 in both directions)
            if dr > 1 or dc > 1:
                return False
        
        return True
    
    def get_word_from_path(self, positions):
        """Get the word formed by the path"""
        word = ''
        for r, c in positions:
            if 0 <= r < 4 and 0 <= c < 4:
                letter = self.board[r][c]
                word += letter.lower()
        return word
    
    def is_valid_word(self, word):
        """Check if word is a valid English word using wordlist.txt"""
        return word.lower() in VALID_WORDS
    
    def validate_word(self, positions):
        """Validate if the word is valid"""
        # Get the word from path first (even if path is invalid, to show what was attempted)
        word = self.get_word_from_path(positions)
        
        if not self.is_valid_path(positions):
            return False, "Invalid path - letters must be directly connected", word
        
        if len(word) < 3:
            return False, "Word must be at least 3 letters", word
        
        if not self.is_valid_word(word):
            return False, "Not a valid English word", word
        
        if word in self.found_words:
            return False, "Word already found", word
        
        return True, word, word
    
    def add_word(self, word):
        """Add a found word and update score"""
        self.found_words.append(word)
        # Scoring: 3-4 letters = 1 point, 5 = 2, 6 = 3, 7 = 5, 8+ = 11
        length = len(word)
        if length <= 4:
            points = 1
        elif length == 5:
            points = 2
        elif length == 6:
            points = 3
        elif length == 7:
            points = 5
        else:
            points = 11
        self.score += points
        return points

@app.route('/')
def index():
    """Main page (optional - for testing)"""
    return jsonify({'message': 'Boggle API is running. Use /api endpoints for Svelte frontend.'})

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new game"""
    game_id = str(random.randint(1000, 9999))
    game = BoggleGame(game_id)
    games[game_id] = game
    return jsonify({
        'game_id': game_id,
        'board': game.board,
        'score': 0,
        'found_words': []
    })

@app.route('/api/validate_word', methods=['POST'])
def validate_word():
    """Validate a word submission"""
    data = request.json
    game_id = data.get('game_id')
    positions = data.get('positions')  # List of [row, col] pairs
    
    if not game_id or not positions:
        return jsonify({'error': 'Missing game_id or positions'}), 400
    
    if game_id not in games:
        return jsonify({'error': 'Invalid game ID'}), 400
    
    game = games[game_id]
    is_valid, result, attempted_word = game.validate_word(positions)
    
    if is_valid:
        word = result
        points = game.add_word(word)
        return jsonify({
            'valid': True,
            'word': word,
            'points': points,
            'score': game.score,
            'found_words': game.found_words
        })
    else:
        return jsonify({
            'valid': False,
            'error': result,
            'attempted_word': attempted_word
        })

@app.route('/api/game_state', methods=['GET'])
def game_state():
    """Get current game state"""
    game_id = request.args.get('game_id')
    if not game_id or game_id not in games:
        return jsonify({'error': 'Invalid game ID'}), 400
    
    game = games[game_id]
    return jsonify({
        'board': game.board,
        'score': game.score,
        'found_words': game.found_words
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)