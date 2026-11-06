#!/usr/bin/env python3
"""
Mahjong Riichi - Web Application
Flask-based web UI for mobile responsiveness
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os
import random

# Import game modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.leaderboard import get_database, Database, User
from engine.game_state import GameState
from engine.slot_engine import get_engine, GameMode
from engine.casino_admin import get_admin_system
from engine.casino_admin_api import admin_bp
from core.tiles import Tile, tiles_to_counts
from ai.advanced_ai import AdvancedAI

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Register admin blueprint
app.register_blueprint(admin_bp)

# CORS support for session cookies
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin', '')
    allowed_origins = ['http://192.168.8.155:5000', 'http://localhost:5000']
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

# Game state storage (in-memory for demo, use Redis for production)
active_games = {}


# =============================================================================
# AUTH ROUTES
# =============================================================================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('lobby'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """Login API"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing credentials'})

    db = get_database()
    user = db.verify_user(username, password)

    if user:
        session['user_id'] = user.user_id
        session['username'] = user.username
        return jsonify({'success': True, 'username': user.username})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})


@app.route('/api/register', methods=['POST'])
def api_register():
    """Register API"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing fields'})

    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Username too short'})

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password too short'})

    db = get_database()
    user = db.create_user(username, password)

    if user:
        session['user_id'] = user.user_id
        session['username'] = user.username
        return jsonify({'success': True, 'username': user.username})
    else:
        return jsonify({'success': False, 'error': 'Username already exists'})


@app.route('/api/logout')
def api_logout():
    """Logout API"""
    session.clear()
    return jsonify({'success': True})


# =============================================================================
# LOBBY ROUTES
# =============================================================================

@app.route('/lobby')
def lobby():
    """Game lobby"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_database()
    leaderboard = db.get_leaderboard(10)
    user_stats = db.get_player_stats(session['user_id'])

    return render_template('lobby.html',
                          username=session['username'],
                          leaderboard=leaderboard,
                          stats=user_stats)


@app.route('/api/leaderboard')
def api_leaderboard():
    """Get leaderboard API"""
    db = get_database()
    leaderboard = db.get_leaderboard(20)
    return jsonify({'success': True, 'leaderboard': leaderboard})


# =============================================================================
# SLOT GAME ROUTES
# =============================================================================

@app.route('/slot')
def slot():
    """Slot game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('slot.html', username=session['username'])


@app.route('/api/slot/save_balance', methods=['POST'])
def api_save_slot_balance():
    """Save slot balance to database"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json
    balance = data.get('balance', 0)

    # Update user's slot balance in database
    # For now just return success
    return jsonify({'success': True})


# =============================================================================
# BLACKJACK GAME ROUTES
# =============================================================================

@app.route('/blackjack')
def blackjack():
    """Blackjack game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('blackjack.html', username=session['username'])


# =============================================================================
# ROULETTE GAME ROUTES
# =============================================================================

@app.route('/roulette')
def roulette():
    """Roulette game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('roulette.html', username=session['username'])


# =============================================================================
# BACCARAT GAME ROUTES
# =============================================================================

@app.route('/baccarat')
def baccarat():
    """Baccarat game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('baccarat.html', username=session['username'])


# =============================================================================
# WOLF GOLD SLOT ROUTES
# =============================================================================

@app.route('/wolf_gold')
def wolf_gold():
    """Wolf Gold slot game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('wolf_gold.html', username=session['username'])


# =============================================================================
# BIG BASS BONANZA SLOT ROUTES
# =============================================================================

@app.route('/big_bass_bonanza')
def big_bass_bonanza():
    """Big Bass Bonanza slot game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('big_bass_bonanza.html', username=session['username'])


# =============================================================================
# SWEET BONANZA SLOT ROUTES
# =============================================================================

@app.route('/sweet_bonanza')
def sweet_bonanza():
    """Sweet Bonanza slot game page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('sweet_bonanza.html', username=session['username'])


# =============================================================================
# ADMIN PANEL ROUTE
# =============================================================================

@app.route('/admin')
def admin_panel():
    """Admin control panel"""
    # Check for admin session
    if not session.get('is_admin'):
        return render_template('admin_panel.html', logged_in=False)
    return render_template('admin_panel.html', logged_in=True)


# =============================================================================
# SLOT GAMES API (Sweet Bonanza, Wolf Gold, etc.)
# =============================================================================

# In-memory balance storage per session
slot_balances = {}


@app.route('/api/slots/games')
def api_slot_games():
    """Get available slot games"""
    games = [
        {
            'id': 'sweet_bonanza',
            'name': 'Sweet Bonanza',
            'emoji': '🍬',
            'theme': 'Candy',
            'rtp': '96.48%',
            'max_win': '21,175x',
            'features': ['Tumble', 'Multiplier Bombs', 'Free Spins'],
            'is_new': True
        },
        {
            'id': 'wolf_gold',
            'name': 'Wolf Gold',
            'emoji': '🦬',
            'theme': 'Wild West',
            'rtp': '96.01%',
            'max_win': '2,500x',
            'features': ['Money Respin', 'Jackpot', 'Free Spins'],
            'is_hot': True
        },
        {
            'id': 'big_bass',
            'name': 'Big Bass Bonanza',
            'emoji': '🎣',
            'theme': 'Fishing',
            'rtp': '96.71%',
            'max_win': '2,100x',
            'features': ['Fisherman Wild', 'Collect Fish', 'Free Spins'],
            'is_hot': True
        },
        {
            'id': 'starlight',
            'name': 'Starlight Princess',
            'emoji': '👸',
            'theme': 'Anime Fantasy',
            'rtp': '96.50%',
            'max_win': '5,000x',
            'features': ['Multiplier Symbols', 'Tumble', 'Free Spins'],
            'is_new': True
        },
        {
            'id': 'gates_of_olympus',
            'name': 'Gates of Olympus',
            'emoji': '⚡',
            'theme': 'Greek Mythology',
            'rtp': '96.50%',
            'max_win': '5,000x',
            'features': ['Multiplier System', 'Tumble', 'Free Spins'],
            'is_hot': True
        }
    ]
    return jsonify({'success': True, 'games': games})


@app.route('/api/slots/init', methods=['POST'])
def api_slot_init():
    """Initialize slot game for user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json or {}
    game_id = data.get('game_id', 'sweet_bonanza')

    # Initialize balance
    user_id = session['user_id']
    balance_key = f"{user_id}_{game_id}"

    if balance_key not in slot_balances:
        slot_balances[balance_key] = 10000  # Starting balance

    return jsonify({
        'success': True,
        'balance': slot_balances[balance_key],
        'game_id': game_id
    })


@app.route('/api/slots/spin', methods=['POST'])
def api_slot_spin():
    """Perform slot spin with admin control"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json or {}
    game_id = data.get('game_id', 'sweet_bonanza')
    bet = int(data.get('bet', 100))
    spin_id = data.get('spin_id') or secrets.token_hex(8)

    user_id = session['user_id']
    username = session.get('username', 'Unknown')
    balance_key = f"{user_id}_{game_id}"

    # Initialize balance if needed
    if balance_key not in slot_balances:
        slot_balances[balance_key] = 10000

    # Check balance
    if slot_balances[balance_key] < bet:
        return jsonify({
            'success': False,
            'error': 'Insufficient balance',
            'balance': slot_balances[balance_key]
        })

    # Deduct bet
    slot_balances[balance_key] -= bet

    # Record bet in analytics
    from engine.casino_admin import get_admin_system
    admin = get_admin_system()
    admin.record_bet(user_id, username, bet, game_id)

    # Check for spin override first
    override = admin.get_spin_override(spin_id)

    if override:
        # Admin override - force specific outcome
        if override.exact_payout is not None:
            payout = override.exact_payout
        elif override.force_win:
            payout = int(bet * random.uniform(2, 10))  # Random big win
        elif override.force_lose:
            payout = 0
        else:
            # Normal spin
            engine = get_engine(game_id, bet)
            result = engine.spin()
            payout = result.total_payout
            result_data = result
    else:
        # Normal spin with admin RTP control
        engine = get_engine(game_id, bet)
        result = engine.spin()

        # Get base payout
        base_payout = result.total_payout

        # Apply admin RTP control
        should_win, adjusted_payout = admin.should_player_win(
            user_id, game_id, base_payout
        )

        if should_win and base_payout > 0:
            payout = adjusted_payout
        else:
            payout = 0

        result_data = result

    # Apply AI engagement adjustment if enabled
    if payout > 0:
        payout = admin.adjust_result_for_engagement(user_id, payout, bet)

    # Update balance
    slot_balances[balance_key] += payout

    # Record win/loss in analytics
    if payout > bet:
        admin.record_win(user_id, username, payout, bet)
    elif payout < bet:
        admin.record_loss(user_id, username, bet)
    else:
        # Push - record as bet
        admin.record_bet(user_id, username, 0, game_id)

    return jsonify({
        'success': True,
        'balance': slot_balances[balance_key],
        'bet': bet,
        'payout': payout,
        'net': payout - bet,
        'is_win': payout > bet,
        'reels': result_data.reels,
        'winning_lines': result_data.winning_lines,
        'cascade_count': result_data.cascade_count,
        'multipliers': result_data.multipliers,
        'bonus_triggered': result_data.bonus_triggered,
        'bonus_type': result_data.bonus_type,
        'spin_id': spin_id
    })


@app.route('/api/slots/balance')
def api_slot_balance():
    """Get slot balance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.args
    game_id = data.get('game_id', 'sweet_bonanza')

    user_id = session['user_id']
    balance_key = f"{user_id}_{game_id}"

    if balance_key not in slot_balances:
        slot_balances[balance_key] = 10000

    return jsonify({
        'success': True,
        'balance': slot_balances[balance_key],
        'game_id': game_id
    })


@app.route('/api/slots/deposit', methods=['POST'])
def api_slot_deposit():
    """Deposit to slot balance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json or {}
    game_id = data.get('game_id', 'sweet_bonanza')
    amount = int(data.get('amount', 1000))

    user_id = session['user_id']
    balance_key = f"{user_id}_{game_id}"

    if balance_key not in slot_balances:
        slot_balances[balance_key] = 10000

    slot_balances[balance_key] += amount

    return jsonify({
        'success': True,
        'balance': slot_balances[balance_key],
        'deposited': amount
    })


@app.route('/api/slots/withdraw', methods=['POST'])
def api_slot_withdraw():
    """Withdraw from slot balance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json or {}
    game_id = data.get('game_id', 'sweet_bonanza')
    amount = int(data.get('amount', 0))

    user_id = session['user_id']
    balance_key = f"{user_id}_{game_id}"

    if balance_key not in slot_balances:
        slot_balances[balance_key] = 10000

    if slot_balances[balance_key] < amount:
        return jsonify({
            'success': False,
            'error': 'Insufficient balance'
        })

    slot_balances[balance_key] -= amount

    return jsonify({
        'success': True,
        'balance': slot_balances[balance_key],
        'withdrawn': amount
    })


# =============================================================================
# GAME ROUTES
# =============================================================================

@app.route('/game')
def game():
    """Game page - redirect to existing game or create new"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Check for existing game in session
    existing_game = session.get('current_game_id')
    if existing_game and existing_game in active_games:
        return redirect(url_for('game_with_id', game_id=existing_game))

    # Create new game automatically
    game_id = secrets.token_hex(8)
    game_state = GameState(
        player_names=[session['username'], 'CPU-1', 'CPU-2', 'CPU-3'],
        seed=None
    )
    game_state.start_new_round()
    game_state.deal_initial_hands()

    ai_players = {}
    for i in range(1, 4):
        ai_players[i] = AdvancedAI(i, 2)

    active_games[game_id] = {
        'game_state': game_state,
        'ai_players': ai_players,
        'current_player': 0,
        'human_player_id': 0
    }

    session['current_game_id'] = game_id
    return render_template('game.html', username=session['username'], game_id=game_id)


@app.route('/game/<game_id>')
def game_with_id(game_id):
    """Game page with specific game ID"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if game_id not in active_games:
        # Game not found, redirect to lobby
        return redirect(url_for('lobby'))

    session['current_game_id'] = game_id
    return render_template('game.html', username=session['username'], game_id=game_id)


@app.route('/api/game/create', methods=['POST'])
def api_create_game():
    """Create new game"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    data = request.json or {}
    player_count = min(4, max(1, data.get('player_count', 4)))
    ai_level = data.get('ai_level', 2)

    # Create game
    game_id = secrets.token_hex(8)
    ai_names = [f"CPU-{i}" for i in range(1, player_count)]
    game_state = GameState(
        player_names=[session['username']] + ai_names,
        seed=None
    )
    game_state.start_new_round()
    game_state.deal_initial_hands()

    # Create AI players
    ai_players = {}
    for i in range(1, player_count):
        ai_players[i] = AdvancedAI(i, ai_level)

    active_games[game_id] = {
        'game_state': game_state,
        'ai_players': ai_players,
        'current_player': 0,
        'human_player_id': 0,
        'created_by': session['user_id']
    }

    # Store in session
    session['current_game_id'] = game_id

    return jsonify({
        'success': True,
        'game_id': game_id
    })


def get_current_game_id():
    """Helper to get game_id from session or return None"""
    return session.get('current_game_id')


@app.route('/api/game/state')
def api_get_game_state():
    """Get game state for current session game"""
    game_id = get_current_game_id()
    if not game_id or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']

    # Serialize game state
    players_data = []
    for i, player in enumerate(gs.players):
        players_data.append({
            'id': i,
            'name': player.name,
            'score': player.score,
            'is_dealer': player.is_dealer,
            'is_tenpai': player.is_tenpai,
            'riichi_declared': player.riichi_declared,
            'hand_count': len(player.hand),
            'discards': [t.type for t in player.discards[-6:]]  # Last 6 discards
        })

    dora = [t.type for t in gs.dora_indicators]

    # Get human player's hand
    human_hand = []
    if game['human_player_id'] == gs.current_turn:
        human_hand = [t.type for t in gs.players[gs.current_turn].hand]

    # Get available actions for human player
    available_actions = {
        'discard': True,
        'riichi': not gs.players[0].riichi_declared and gs.players[0].is_tenpai,
        'tsumo': False,  # Check in game logic
        'ron': False     # Check in game logic
    }

    return jsonify({
        'success': True,
        'game': {
            'current_player': gs.current_turn,
            'round': gs.round_number,
            'honba': gs.honba,
            'deck_count': gs.deck.remaining if gs.deck else 0,
            'riichi_sticks': gs.riichi_sticks,
            'players': players_data,
            'dora': dora,
            'hand': human_hand,
            'discards': {
                'self': [t.type for t in gs.players[0].discards],
                'last': gs.last_discarded_tile.type if gs.last_discarded_tile else None
            },
            'game_over': gs.game_over,
            'winner': gs.winner,
            'available_actions': available_actions
        }
    })


@app.route('/api/game/<game_id>')
def api_get_game(game_id):
    """Get game state by game ID (legacy)"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']

    # Serialize game state
    players_data = []
    for i, player in enumerate(gs.players):
        players_data.append({
            'id': i,
            'name': player.name,
            'score': player.score,
            'is_dealer': player.is_dealer,
            'is_tenpai': player.is_tenpai,
            'riichi_declared': player.riichi_declared,
            'hand_count': len(player.hand),
            'discards': [t.type for t in player.discards[-6:]]  # Last 6 discards
        })

    dora = [t.type for t in gs.dora_indicators]

    # Get human player's hand
    human_hand = []
    if game['human_player_id'] == gs.current_turn:
        human_hand = [t.type for t in gs.players[gs.current_turn].hand]

    return jsonify({
        'success': True,
        'game': {
            'current_turn': gs.current_turn,
            'round_number': gs.round_number,
            'honba': gs.honba,
            'riichi_sticks': gs.riichi_sticks,
            'deck_remaining': gs.deck.remaining,
            'players': players_data,
            'dora': dora,
            'human_hand': human_hand,
            'is_game_over': gs.game_over,
            'winner': gs.winner
        }
    })


@app.route('/api/game/action', methods=['POST'])
@app.route('/api/game/<game_id>/action', methods=['POST'])
def api_game_action(game_id=None):
    """Perform game action - supports both session and explicit game_id"""
    # Get game_id from session if not provided
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']
    data = request.json or {}
    action = data.get('action')
    tile_idx = data.get('tile_index')

    result = {'success': True}

    # Process action
    if action == 'discard' and tile_idx is not None:
        player = gs.players[gs.current_turn]
        if 0 <= tile_idx < len(player.hand):
            tile = player.hand[tile_idx]
            gs.discard_tile(gs.current_turn, tile)
            result['discarded'] = tile.type
            result['hand'] = [t.type for t in gs.players[0].hand]

    elif action == 'call':
        call_type = data.get('call_type')
        if call_type in ['pon', 'chi', 'kan']:
            meld = gs.process_call(gs.current_turn, call_type)
            result['meld'] = str(meld) if meld else None

    # AI turn (if not human)
    if gs.current_turn != game['human_player_id'] and not gs.game_over:
        result['ai_turn'] = True
        result['ai_action'] = process_ai_turn(game, gs.current_turn)

    # Update hand for human player
    if gs.current_turn == game['human_player_id']:
        result['hand'] = [t.type for t in gs.players[0].hand]

    # Check for game end
    if gs.game_over:
        db = get_database()
        scores = [p.score for p in gs.players]
        player_ids = list(range(len(gs.players)))
        db.record_game(gs.winner, scores, player_ids)

        # Record best hand value if player won
        if gs.winner == game['human_player_id']:
            db.record_hand_value(session['user_id'], max(scores) // 1000)

        result['game_over'] = True
        result['final_scores'] = scores

    return jsonify(result)


# Additional game action routes for game.html template
@app.route('/api/game/discard', methods=['POST'])
@app.route('/api/game/<game_id>/discard', methods=['POST'])
def api_discard(game_id=None):
    """Discard a tile"""
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']
    data = request.json or {}
    tile_idx = data.get('tile_index')

    if tile_idx is None:
        return jsonify({'success': False, 'error': 'No tile selected'})

    player = gs.players[gs.current_turn]
    if 0 <= tile_idx < len(player.hand):
        tile = player.hand[tile_idx]
        gs.discard_tile(gs.current_turn, tile)

        # AI turn
        if gs.current_turn != game['human_player_id'] and not gs.game_over:
            process_ai_turn(game, gs.current_turn)

        return jsonify({
            'success': True,
            'hand': [t.type for t in gs.players[0].hand],
            'discards': {
                'self': [t.type for t in gs.players[0].discards],
                'last': gs.last_discard.type if gs.last_discard else None
            }
        })

    return jsonify({'success': False, 'error': 'Invalid tile index'})


@app.route('/api/game/ron', methods=['POST'])
@app.route('/api/game/<game_id>/call/ron', methods=['POST'])
def api_ron(game_id=None):
    """Call Ron (win on opponent's discard)"""
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']

    # Check for ron win
    if gs.last_discard:
        win = gs.check_win(game['human_player_id'], gs.last_discard, is_tsumo=False)
        if win:
            gs.handle_win(win)

    if gs.game_over:
        db = get_database()
        scores = [p.score for p in gs.players]
        player_ids = list(range(len(gs.players)))
        db.record_game(gs.winner, scores, player_ids)
        if gs.winner == game['human_player_id']:
            db.record_hand_value(session['user_id'], max(scores) // 1000)

    return jsonify({'success': True, 'game_over': gs.game_over})


@app.route('/api/game/tsumo', methods=['POST'])
@app.route('/api/game/<game_id>/call/tsumo', methods=['POST'])
def api_tsumo(game_id=None):
    """Call Tsumo (win on self-draw)"""
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']

    # Check for tsumo win
    player = gs.players[game['human_player_id']]
    if player.hand:
        win = gs.check_win(game['human_player_id'], player.hand[-1], is_tsumo=True)
        if win:
            gs.handle_win(win)

    if gs.game_over:
        db = get_database()
        scores = [p.score for p in gs.players]
        player_ids = list(range(len(gs.players)))
        db.record_game(gs.winner, scores, player_ids)
        if gs.winner == game['human_player_id']:
            db.record_hand_value(session['user_id'], max(scores) // 1000)

    return jsonify({'success': True, 'game_over': gs.game_over})


@app.route('/api/game/riichi', methods=['POST'])
@app.route('/api/game/<game_id>/riichi', methods=['POST'])
def api_riichi(game_id=None):
    """Declare Riichi"""
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    game = active_games[game_id]
    gs = game['game_state']
    player = gs.players[game['human_player_id']]

    # Check if player can declare riichi
    if not player.riichi_declared and player.is_tenpai:
        player.riichi_declared = True
        gs.riichi_sticks += 1
        return jsonify({'success': True, 'riichi_declared': True})

    return jsonify({'success': False, 'error': 'Cannot declare riichi'})


@app.route('/api/game/pass', methods=['POST'])
@app.route('/api/game/<game_id>/pass', methods=['POST'])
def api_pass(game_id=None):
    """Pass on a call"""
    if game_id is None:
        game_id = get_current_game_id()

    if game_id is None or game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'})

    return jsonify({'success': True})


def process_ai_turn(game, player_id):
    """Process AI player's turn"""
    gs = game['game_state']
    ai = game['ai_players'].get(player_id)

    if ai is None:
        gs.next_turn()
        return 'no_ai'

    # Draw
    drawn = gs.draw_tile(player_id)
    if not drawn:
        return 'exhausted'

    # Check for tenpai
    win = gs.check_win(player_id, drawn, is_tsumo=True)
    if win:
        gs.handle_win(win)
        return 'tsumo_win'

    # Discard
    tile = ai.decide_discard(gs)
    gs.discard_tile(player_id, tile)

    # Check for calls
    # (simplified - would need full call detection)

    gs.next_turn()
    return 'discarded'


# =============================================================================
# STATS ROUTES
# =============================================================================

@app.route('/api/stats')
def api_stats():
    """Get user stats"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    db = get_database()
    stats = db.get_player_stats(session['user_id'])
    return jsonify({'success': True, 'stats': stats})


# =============================================================================
# MAIN
# =============================================================================

def create_templates():
    """Create template files (only if they don't exist)"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Only create templates if they don't exist
    base_path = os.path.join(templates_dir, 'base.html')
    if os.path.exists(base_path):
        print("Templates already exist, skipping creation")
        return

    # Base template
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{% block title %}Mahjong Riichi{% endblock %}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: scale(1.05); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-danger { background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%); }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 16px;
            margin-bottom: 10px;
        }
        input::placeholder { color: rgba(255,255,255,0.5); }
        .tile {
            width: 40px;
            height: 56px;
            background: white;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin: 2px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .tile:hover { transform: translateY(-5px); }
        .tile.selected {
            transform: translateY(-15px);
            box-shadow: 0 5px 15px rgba(255,200,50,0.5);
        }
        .player-area {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .tile { width: 32px; height: 45px; font-size: 18px; }
        }
    </style>
    {% block extra_style %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% block extra_script %}{% endblock %}
</body>
</html>"""

    # Login template
    login_html = """{% extends "base.html" %}
{% block title %}Login - Mahjong{% endblock %}
{% block content %}
<div class="container" style="max-width: 400px; margin-top: 100px;">
    <h1 style="text-align: center; margin-bottom: 30px;">🀄 Mahjong Riichi</h1>
    <div class="card">
        <h2 style="margin-bottom: 20px;">Login</h2>
        <div id="error" style="color: #f5576c; margin-bottom: 10px; display: none;"></div>
        <input type="text" id="username" placeholder="Username">
        <input type="password" id="password" placeholder="Password">
        <button class="btn" onclick="login()" style="width: 100%;">Login</button>
        <p style="text-align: center; margin-top: 15px;">
            Don't have an account? <a href="#" onclick="showRegister()" style="color: #667eea;">Register</a>
        </p>
    </div>
    <div class="card" id="register-card" style="display: none;">
        <h2 style="margin-bottom: 20px;">Register</h2>
        <input type="text" id="reg-username" placeholder="Username">
        <input type="password" id="reg-password" placeholder="Password">
        <button class="btn" onclick="register()" style="width: 100%;">Register</button>
        <p style="text-align: center; margin-top: 15px;">
            Already have an account? <a href="#" onclick="showLogin()" style="color: #667eea;">Login</a>
        </p>
    </div>
</div>
<script>
function login() {
    fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        })
    }).then(r => r.json()).then(data => {
        if (data.success) window.location.href = '/lobby';
        else document.getElementById('error').style.display = 'block',
                     document.getElementById('error').textContent = data.error;
    });
}
function register() {
    fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('reg-username').value,
            password: document.getElementById('reg-password').value
        })
    }).then(r => r.json()).then(data => {
        if (data.success) window.location.href = '/lobby';
        else alert(data.error);
    });
}
function showRegister() {
    document.querySelector('.card').style.display = 'none';
    document.getElementById('register-card').style.display = 'block';
}
function showLogin() {
    document.querySelector('.card').style.display = 'block';
    document.getElementById('register-card').style.display = 'none';
}
</script>
{% endblock %}"""

    # Lobby template
    lobby_html = """{% extends "base.html" %}
{% block title %}Lobby - Mahjong{% endblock %}
{% block content %}
<div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1>🀄 Mahjong Riichi</h1>
        <div>
            <span>Welcome, {{ username }}</span>
            <button class="btn btn-danger" onclick="logout()">Logout</button>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
        <div class="card">
            <h2>Quick Play</h2>
            <p style="margin-bottom: 15px; color: #aaa;">Play against AI opponents</p>
            <button class="btn" onclick="startGame(4, 2)">Start Game (4 Players)</button>
            <button class="btn" onclick="startGame(2, 2)" style="margin-top: 10px;">2 Players</button>
        </div>

        <div class="card">
            <h2>Your Stats</h2>
            {% if stats %}
            <p>Rank: #{{ stats.rank or 'N/A' }}</p>
            <p>Games: {{ stats.games_played }}</p>
            <p>Win Rate: {{ stats.win_rate }}%</p>
            <p>Best Score: {{ stats.highest_score }}</p>
            {% else %}
            <p>No games played yet</p>
            {% endif %}
        </div>

        <div class="card" style="grid-column: 1 / -1;">
            <h2>🏆 Leaderboard</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.2);">
                        <th style="padding: 10px;">Rank</th>
                        <th style="padding: 10px;">Player</th>
                        <th style="padding: 10px;">Games</th>
                        <th style="padding: 10px;">Win Rate</th>
                        <th style="padding: 10px;">Total Score</th>
                    </tr>
                </thead>
                <tbody id="leaderboard-body">
                    {% for entry in leaderboard %}
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <td style="padding: 10px;">#{{ entry.rank }}</td>
                        <td style="padding: 10px;">{{ entry.username }}</td>
                        <td style="padding: 10px;">{{ entry.games_played }}</td>
                        <td style="padding: 10px;">{{ entry.win_rate }}%</td>
                        <td style="padding: 10px;">{{ entry.total_score }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
<script>
let currentGameId = null;

function startGame(players, aiLevel) {
    fetch('/api/game/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({player_count: players, ai_level: aiLevel})
    }).then(r => r.json()).then(data => {
        if (data.success) {
            currentGameId = data.game_id;
            window.location.href = '/game';
        }
    });
}

function logout() {
    fetch('/api/logout').then(() => window.location.href = '/login');
}
</script>
{% endblock %}"""

    # Game template
    game_html = """{% extends "base.html" %}
{% block title %}Game - Mahjong{% endblock %}
{% block extra_style %}
<style>
    .game-board {
        background: linear-gradient(135deg, #2d5a27 0%, #1e3d1a 100%);
        border-radius: 20px;
        padding: 20px;
        margin: 20px auto;
        max-width: 800px;
    }
    .player-info {
        background: rgba(0,0,0,0.3);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .discard-area {
        min-height: 80px;
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        padding: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .hand-area {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 5px;
        margin-top: 20px;
    }
    .dora-area {
        text-align: center;
        padding: 15px;
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
{% endblock %}
{% block content %}
<div class="container">
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <h2>Round <span id="round">1</span> - Honba: <span id="honba">0</span></h2>
        <div>
            <span id="deck">Deck: 136</span> | Riichi: <span id="riichi">0</span>
        </div>
    </div>

    <div class="game-board">
        <div class="dora-area">
            <small>DORA</small>
            <div id="dora" style="display: flex; gap: 5px; justify-content: center; margin-top: 5px;"></div>
        </div>

        <div id="opponents"></div>

        <div class="hand-area" id="hand"></div>

        <div style="margin-top: 15px; text-align: center;">
            <button class="btn" onclick="refreshGame()">Refresh</button>
        </div>
    </div>

    <div class="card" id="game-over" style="display: none; text-align: center;">
        <h2 id="winner-text">Game Over!</h2>
        <button class="btn" onclick="window.location.href='/lobby'">Back to Lobby</button>
    </div>
</div>

<script>
const TILE_CHARS = ['1P','2P','3P','4P','5P','6P','7P','8P','9P',
                    '1S','2S','3S','4S','5S','6S','7S','8S','9S',
                    '1M','2M','3M','4M','5M','6M','7M','8M','9M',
                    'E','S','W','N','白','發','中'];

let gameId = '{{ session.get("game_id", "") }}';

function refreshGame() {
    // In real implementation, fetch from /api/game/{game_id}
    // For demo, just refresh page
    location.reload();
}

function renderHand(tiles) {
    const handDiv = document.getElementById('hand');
    handDiv.innerHTML = tiles.map((t, i) =>
        `<div class="tile" onclick="selectTile(${i})">${TILE_CHARS[t]}</div>`
    ).join('');
}

function selectTile(idx) {
    document.querySelectorAll('.tile').forEach((el, i) => {
        el.classList.toggle('selected', i === idx);
    });
    // In real implementation, call /api/game/{game_id}/action
}
</script>
{% endblock %}"""

    # Write templates with UTF-8 encoding
    with open(os.path.join(templates_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_html)
    with open(os.path.join(templates_dir, 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login_html)
    with open(os.path.join(templates_dir, 'lobby.html'), 'w', encoding='utf-8') as f:
        f.write(lobby_html)
    with open(os.path.join(templates_dir, 'game.html'), 'w', encoding='utf-8') as f:
        f.write(game_html)


def init_app():
    """Initialize the application"""
    # Create templates if needed (won't overwrite existing ones)
    create_templates()

    # Initialize database
    db = get_database()

    # Create default user if not exists
    if db.get_user_by_username('player') is None:
        db.create_user('player', 'password123')
        print("Default user created: player / password123")

    print("Mahjong Web App initialized!")
    print("Open http://localhost:5000 in your browser")
    print("Login: player / password123")


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
