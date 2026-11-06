# 🎰 MegaWin X KUDO777 - Online Casino Platform

Japanese Riichi Mahjong game + Pragmatic Play-style casino games.

## 🎮 Overview

Platform casino online dengan game **Mahjong Riichi** dan berbagai **slot games** ala Pragmatic Play dengan sistem admin control dan AI engagement.

## 🎯 Features

### Core Games
- **🀄 Mahjong Riichi**: Game.tile Jepang dengan AI opponents
- **🎰 Slot Games**: Gates of Olympus, Sweet Bonanza, Wolf Gold, Big Bass Bonanza
- **🃏 Blackjack**: Classic card game
- **🎡 Roulette**: European wheel
- **✨ Baccarat**: James Bond's favorite

### Admin Control System (Lanjutan Development)
- **Global RTP Control**: Set RTP per game (80%-100%)
- **Per-Player Intervention**: Override hasil per player
- **Spin Override**: Edit hasil spin secara real-time
- **AI Engagement System**: Prediksi churn & engagement player

### AI Player Psychology
- **Engagement Scoring**: 0-1 scale
- **Churn Risk Detection**: Prediksi player yang mau berhenti
- **Behavioral Analysis**: Betting patterns, win/loss streaks
- **Intervention Recommendations**: AI-suggested actions

## 📁 Project Structure

```
mahjong_riichi/
├── core/                  # Core game logic
│   ├── tiles.py          # Tile class (34 types)
│   ├── deck.py           # Deck management
│   ├── meld.py           # Meld detection
│   ├── shanten.py        # Shanten calculator
│   ├── yaku.py           # Yaku detector
│   └── score.py          # Score calculator
├── engine/               # Game engine
│   ├── player.py         # Player class
│   ├── game_state.py     # Game state manager
│   ├── slot_engine.py     # Slot games engine
│   ├── multiplier_system.py # Sweet Bonanza multipliers (NEW!)
│   ├── casino_admin.py   # Admin control system
│   └── casino_admin_api.py # Admin API routes
├── ai/                   # AI players
│   ├── base_ai.py        # Base AI interface
│   ├── random_ai.py      # Level 1: Random
│   ├── basic_ai.py       # Level 2: Shanten-aware
│   ├── advanced_ai.py    # Level 3: Defense+Offense
│   ├── expert_ai.py      # Level 4: Expert strategy
│   └── tournament.py      # AI comparison
├── database/              # Database
│   └── leaderboard.py     # MySQL user management
├── templates/             # HTML templates
│   ├── login.html         # Login page (casino theme)
│   ├── lobby.html        # Game lobby
│   ├── game.html         # Mahjong game
│   ├── slot.html         # Gates of Olympus
│   ├── sweet_bonanza.html # Sweet Bonanza
│   ├── blackjack.html     # Blackjack
│   ├── roulette.html     # Roulette
│   └── baccarat.html     # Baccarat
├── web_app.py             # Flask web application
└── main.py               # Entry point
```

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 🎰 Usage

### Start Web Server
```bash
python web_app.py
# Open http://localhost:5000
# Login: player / password123
```

### Admin Panel
```bash
# Access admin panel at /api/admin/...
# Default credentials: admin / admin123
```

## 📊 Admin Control System

### Three-Tier RTP Control

```
┌─────────────────────────────────────────────────────────┐
│                    PRIORITY ORDER                        │
├─────────────────────────────────────────────────────────┤
│  1. SPIN OVERRIDE (Highest)                             │
│     - Force win/lose per spin                           │
│     - Set exact payout amount                            │
│                                                         │
│  2. PLAYER INTERVENTION                                 │
│     - Lock player (0% RTP)                              │
│     - Boost player (150% RTP)                           │
│     - Custom RTP per player                             │
│     - Jackpot mode                                      │
│                                                         │
│  3. GLOBAL SETTINGS (Base)                              │
│     - Default RTP per game (80%-100%)                   │
│     - AI Engagement toggle                               │
│     - Loss streak limits                                │
└─────────────────────────────────────────────────────────┘
```

### Intervention Levels

| Level | Effect | Use Case |
|-------|--------|----------|
| `NONE` | Normal gameplay | Default |
| `MODERATE` | 80% of normal wins | Slight control |
| `HEAVY` | 50% of normal wins | Problem players |
| `LOCKED` | 0% wins | Banned/exploiter |
| `BOOSTED` | 130% wins | Retention |
| `JACKPOT_MODE` | 150% + frequent big wins | VIP retention |

### AI Engagement System

```python
# AI analyzes player behavior and suggests interventions
Player Analysis:
├── Engagement Score (0-1)
├── Churn Risk (0-1)
├── Betting Patterns
├── Win/Loss Streaks
└── Session Duration

AI Actions:
├── RETAIN   → Boost winning to keep player
├── CALM     → Reduce volatility for tilted players
├── REWARD   → Small guaranteed wins for frustrated
├── ENGAGE   → Increase engagement
└── NONE     → No intervention needed
```

## 🎮 Game List

| Game | URL | Features |
|------|-----|----------|
| Mahjong | `/game` | 4-player, AI opponents |
| Sweet Bonanza | `/sweet_bonanza` | Tumble, Candy Bombs, Hybrid Multipliers |
| Gates of Olympus | `/slot` | Multipliers, Free Spins |
| Wolf Gold | - | Money Respin, Jackpot |
| Big Bass Bonanza | - | Fisherman Wild |
| Blackjack | `/blackjack` | Hit, Stand, Double |
| Roulette | `/roulette` | European wheel |
| Baccarat | `/baccarat` | Player/Banker/Tie |

### 🎰 Sweet Bonanza Multiplier System

**Hybrid Multiplier System Implementation:**

1. **Candy Bombs** (💥)
   - Muncul secara random di grid (3-5% chance)
   - Konservatif range: 2x - 10x

2. **Global Accumulator**
   - Multiplier menambah setiap cascade
   - Berlaku untuk semua win di chain tersebut

3. **Payout Table:**
   | Symbol | 8x | 10x | 12x | 15x | 20x |
   |--------|-----|------|------|------|------|
   | 🍭🍬🧁 | 0.25x | 0.65x | 1.00x | 1.60x | 2.00x |
   | 🍩🍎 | 0.50x | 1.30x | 1.95x | 3.90x | 5.20x |
   | 🍇 | 1.00x | 2.25x | 3.25x | 7.15x | 9.75x |
   | 🍌 | 1.55x | 3.25x | 5.20x | 10.40x | 15.60x |

4. **Stats:**
   - Win Rate: ~35-40%
   - RTP: ~100-150% (high variance slot)
   - Max Multiplier: 10x

## 🔧 API Endpoints

### Slot API
- `POST /api/slots/spin` - Perform spin
- `GET /api/slots/balance` - Get balance
- `POST /api/slots/deposit` - Deposit

### Admin API
- `POST /api/admin/login` - Admin login
- `GET /api/admin/dashboard` - Dashboard data
- `POST /api/admin/settings/rtp` - Set game RTP
- `POST /api/admin/intervention/<user_id>` - Player intervention
- `POST /api/admin/override` - Create spin override

## 📋 Roadmap

### Phase 1: Core Platform ✅
- [x] Mahjong Riichi engine
- [x] Web UI dengan Flask
- [x] User authentication
- [x] Leaderboard system

### Phase 2: Casino Games ✅
- [x] Gates of Olympus slot
- [x] Sweet Bonanza slot
- [x] Blackjack
- [x] Roulette
- [x] Baccarat
- [ ] Wolf Gold (UI)
- [ ] Big Bass Bonanza (UI)

### Phase 3: Admin Control ✅
- [x] Global RTP settings
- [x] Per-player intervention
- [x] Spin override system
- [x] Player analytics
- [ ] Admin web UI panel

### Phase 4: AI Engagement (In Progress)
- [x] Basic engagement scoring
- [x] Churn risk detection
- [x] Behavioral patterns
- [ ] Advanced ML predictions
- [ ] Psychological triggers
- [ ] Retention automation

### Phase 5: Advanced Features (Planned)
- [ ] Progressive jackpot system
- [ ] Tournament system
- [ ] VIP tiers
- [ ] Daily challenges
- [ ] Social features
- [ ] Real payment integration

## 🔐 Security Notes

> ⚠️ **Development Mode Only**
>
> - Admin credentials: `admin / admin123`
> - Default slot balance: $10,000
> - In-memory storage (resets on restart)
>
> **For Production:**
> - Use PostgreSQL/MySQL with proper indexing
> - Implement JWT authentication
> - Add rate limiting
> - Use encrypted session storage
> - Implement proper payment gateway

## 👥 Credits

- Mahjong rules: Japanese Riichi Mahjong
- Slot game mechanics: Pragmatic Play inspiration
- UI Theme: MegaWin X KUDO777 brand

## 📄 License

MIT License
