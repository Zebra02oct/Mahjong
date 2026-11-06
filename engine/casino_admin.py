#!/usr/bin/env python3
"""
Casino Admin Control System
Advanced player management, AI engagement, and RTP control
"""

import random
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math


class InterventionLevel(Enum):
    """Level of admin intervention for a player"""
    NONE = "none"           # Normal gameplay
    MODERATE = "moderate"   # Slightly reduce wins
    HEAVY = "heavy"         # Significantly reduce wins
    LOCKED = "locked"       # Player cannot win
    BOOSTED = "boosted"     # Player gets extra wins
    JACKPOT_MODE = "jackpot"  # Player gets frequent jackpots


@dataclass
class GlobalSettings:
    """Global casino settings"""
    # RTP Settings (0.0 - 1.0)
    sweet_bonanza_rtp: float = 0.96
    wolf_gold_rtp: float = 0.96
    big_bass_rtp: float = 0.97
    starlight_rtp: float = 0.965
    gates_of_olympus_rtp: float = 0.965

    # AI Settings
    ai_engagement_enabled: bool = False
    ai_engagement_threshold: float = 0.5  # Below this = intervention needed
    churn_risk_threshold: float = 0.7      # Above this = retention needed

    # Engagement Settings
    min_big_win_interval: int = 300  # seconds between big wins (to keep hope)
    loss_streak_limit: int = 5        # Max losses before guaranteed small win
    big_win_probability: float = 0.3   # Base probability for big win

    # Feature Flags
    allow_edit_results: bool = True
    allow_player_override: bool = True
    allow_global_rtp: bool = True


@dataclass
class PlayerIntervention:
    """Per-player intervention settings"""
    user_id: int
    intervention_level: InterventionLevel = InterventionLevel.NONE
    custom_rtp: Optional[float] = None  # Override global RTP
    win_rate_modifier: float = 1.0      # Multiply win probability
    last_modified: datetime = field(default_factory=datetime.now)
    reason: str = ""
    expires_at: Optional[datetime] = None


@dataclass
class SpinOverride:
    """Override for a specific spin"""
    user_id: int
    game_id: str
    spin_id: str
    force_win: bool = False
    force_lose: bool = False
    exact_payout: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    used: bool = False


@dataclass
class PlayerAnalytics:
    """Comprehensive player analytics"""
    user_id: int
    username: str

    # Session Data
    current_session_start: Optional[datetime] = None
    session_count: int = 0
    total_play_time: int = 0  # minutes

    # Betting Patterns
    avg_bet: float = 0
    max_bet: float = 0
    min_bet: float = 0
    total_bets: int = 0
    total_wagered: int = 0

    # Win/Loss Data
    total_wins: int = 0
    total_losses: int = 0
    total_won: int = 0
    total_lost: int = 0
    current_streak: int = 0
    streak_type: str = "none"  # 'win', 'lose', 'none'

    # Big Wins
    big_wins_count: int = 0
    biggest_win: int = 0
    last_big_win: Optional[datetime] = None
    biggest_multiplier: float = 0

    # Engagement Metrics
    engagement_score: float = 1.0  # 0-1
    churn_risk: float = 0.0         # 0-1
    volatility_preference: str = "normal"  # 'low', 'normal', 'high'

    # Psychological Indicators
    is_on_tilt: bool = False       # Making irrational large bets
    is_frustrated: bool = False    # Losing a lot recently
    is_excited: bool = False        # Just had big win
    deposit_frequency: float = 0     # deposits per week

    # AI Analysis
    ai_recommended_action: str = "none"
    ai_confidence: float = 0.0
    last_ai_update: Optional[datetime] = None


class CasinoAdminSystem:
    """
    Advanced Casino Admin Control System

    Three-tier RTP Control:
    1. Global Settings - affects all players
    2. Per-Player Intervention - admin override per player
    3. Per-Spin Override - admin can edit specific spin results

    Priority: Spin Override > Player Intervention > Global Settings
    """

    def __init__(self):
        self.global_settings = GlobalSettings()

        # In-memory storage (use Redis/DB in production)
        self.player_interventions: Dict[int, PlayerIntervention] = {}
        self.spin_overrides: Dict[str, SpinOverride] = {}
        self.player_analytics: Dict[int, PlayerAnalytics] = {}

        # AI Analysis Cache
        self.ai_cache: Dict[int, Dict] = {}

    # =========================================================================
    # GLOBAL SETTINGS
    # =========================================================================

    def get_global_rtp(self, game_id: str) -> float:
        """Get global RTP for a game"""
        rtp_map = {
            'sweet_bonanza': self.global_settings.sweet_bonanza_rtp,
            'wolf_gold': self.global_settings.wolf_gold_rtp,
            'big_bass': self.global_settings.big_bass_rtp,
            'starlight': self.global_settings.starlight_rtp,
            'gates_of_olympus': self.global_settings.gates_of_olympus_rtp,
        }
        return rtp_map.get(game_id, 0.96)

    def set_global_rtp(self, game_id: str, rtp: float):
        """Set global RTP for a game (0.0 - 1.0)"""
        rtp = max(0.80, min(1.0, rtp))  # Clamp between 80% and 100%

        if game_id == 'sweet_bonanza':
            self.global_settings.sweet_bonanza_rtp = rtp
        elif game_id == 'wolf_gold':
            self.global_settings.wolf_gold_rtp = rtp
        elif game_id == 'big_bass':
            self.global_settings.big_bass_rtp = rtp
        elif game_id == 'starlight':
            self.global_settings.starlight_rtp = rtp
        elif game_id == 'gates_of_olympus':
            self.global_settings.gates_of_olympus_rtp = rtp

    def update_global_settings(self, settings: GlobalSettings):
        """Update all global settings"""
        self.global_settings = settings

    # =========================================================================
    # PLAYER INTERVENTION
    # =========================================================================

    def set_player_intervention(self, user_id: int, level: InterventionLevel,
                               custom_rtp: Optional[float] = None,
                               win_modifier: float = 1.0,
                               reason: str = "",
                               expires_hours: Optional[int] = None):
        """Set intervention for a specific player"""
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)

        self.player_interventions[user_id] = PlayerIntervention(
            user_id=user_id,
            intervention_level=level,
            custom_rtp=custom_rtp,
            win_rate_modifier=win_modifier,
            reason=reason,
            expires_at=expires_at
        )

    def get_player_intervention(self, user_id: int) -> Optional[PlayerIntervention]:
        """Get intervention for a player"""
        intervention = self.player_interventions.get(user_id)

        if intervention and intervention.expires_at:
            if datetime.now() > intervention.expires_at:
                # Expired
                del self.player_interventions[user_id]
                return None

        return intervention

    def clear_player_intervention(self, user_id: int):
        """Remove intervention for a player"""
        if user_id in self.player_interventions:
            del self.player_interventions[user_id]

    def get_effective_rtp(self, user_id: int, game_id: str) -> float:
        """Calculate effective RTP considering all factors"""
        # Start with global RTP
        rtp = self.get_global_rtp(game_id)

        # Check player intervention
        intervention = self.get_player_intervention(user_id)
        if intervention:
            # Custom RTP overrides
            if intervention.custom_rtp:
                rtp = intervention.custom_rtp
            else:
                # Apply win rate modifier
                rtp = rtp * intervention.win_rate_modifier

            # Intervention level adjustments
            if intervention.intervention_level == InterventionLevel.LOCKED:
                rtp = 0.0  # Player cannot win
            elif intervention.intervention_level == InterventionLevel.HEAVY:
                rtp = rtp * 0.5
            elif intervention.intervention_level == InterventionLevel.MODERATE:
                rtp = rtp * 0.8
            elif intervention.intervention_level == InterventionLevel.BOOSTED:
                rtp = min(1.0, rtp * 1.3)
            elif intervention.intervention_level == InterventionLevel.JACKPOT_MODE:
                rtp = min(1.0, rtp * 1.5)

        return max(0.0, min(1.0, rtp))

    # =========================================================================
    # SPIN OVERRIDE
    # =========================================================================

    def create_spin_override(self, user_id: int, game_id: str, spin_id: str,
                            force_win: bool = False, force_lose: bool = False,
                            exact_payout: Optional[int] = None,
                            expires_minutes: int = 5):
        """Create a one-time override for a specific spin"""
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)

        self.spin_overrides[spin_id] = SpinOverride(
            user_id=user_id,
            game_id=game_id,
            spin_id=spin_id,
            force_win=force_win,
            force_lose=force_lose,
            exact_payout=exact_payout,
            expires_at=expires_at
        )

    def get_spin_override(self, spin_id: str) -> Optional[SpinOverride]:
        """Get and consume a spin override"""
        override = self.spin_overrides.get(spin_id)

        if not override:
            return None

        if datetime.now() > override.expires_at:
            del self.spin_overrides[spin_id]
            return None

        if override.used:
            return None

        # Mark as used
        override.used = True
        return override

    def clear_expired_overrides(self):
        """Clean up expired overrides"""
        now = datetime.now()
        expired = [k for k, v in self.spin_overrides.items()
                   if now > v.expires_at or v.used]
        for k in expired:
            del self.spin_overrides[k]

    # =========================================================================
    # PLAYER ANALYTICS
    # =========================================================================

    def get_or_create_analytics(self, user_id: int, username: str) -> PlayerAnalytics:
        """Get or create analytics for a player"""
        if user_id not in self.player_analytics:
            self.player_analytics[user_id] = PlayerAnalytics(
                user_id=user_id,
                username=username
            )
        return self.player_analytics[user_id]

    def record_bet(self, user_id: int, username: str, bet_amount: int, game_id: str):
        """Record a bet from a player"""
        analytics = self.get_or_create_analytics(user_id, username)

        # Start session if not started
        if not analytics.current_session_start:
            analytics.current_session_start = datetime.now()
            analytics.session_count += 1

        # Update betting patterns
        analytics.total_bets += 1
        analytics.total_wagered += bet_amount
        analytics.avg_bet = analytics.total_wagered / analytics.total_bets
        analytics.max_bet = max(analytics.max_bet, bet_amount)
        analytics.min_bet = min(analytics.min_bet, bet_amount) if analytics.min_bet > 0 else bet_amount

    def record_win(self, user_id: int, username: str, payout: int, bet_amount: int):
        """Record a win from a player"""
        analytics = self.get_or_create_analytics(user_id, username)

        analytics.total_wins += 1
        analytics.total_won += payout
        analytics.current_streak += 1
        analytics.streak_type = "win"

        # Track big wins
        if payout >= bet_amount * 10:  # 10x or more
            analytics.big_wins_count += 1
            analytics.last_big_win = datetime.now()
            analytics.is_excited = True

            if payout > analytics.biggest_win:
                analytics.biggest_win = payout
                analytics.biggest_multiplier = payout / bet_amount if bet_amount > 0 else 0

    def record_loss(self, user_id: int, username: str, bet_amount: int):
        """Record a loss from a player"""
        analytics = self.get_or_create_analytics(user_id, username)

        analytics.total_losses += 1
        analytics.total_lost += bet_amount
        analytics.current_streak += 1
        analytics.streak_type = "lose"

        # Check for tilt/frustration
        if analytics.current_streak >= 5:
            analytics.is_on_tilt = True
            analytics.is_frustrated = True

    def update_session(self, user_id: int):
        """Update session duration"""
        analytics = self.get_or_create_analytics(user_id, "")

        if analytics.current_session_start:
            duration = (datetime.now() - analytics.current_session_start).total_seconds() / 60
            analytics.total_play_time += int(duration)
            analytics.current_session_start = datetime.now()

    def get_player_stats(self, user_id: int) -> Optional[Dict]:
        """Get player statistics"""
        analytics = self.player_analytics.get(user_id)
        if not analytics:
            return None

        total_games = analytics.total_wins + analytics.total_losses
        win_rate = analytics.total_wins / total_games if total_games > 0 else 0
        net_profit = analytics.total_won - analytics.total_lost

        return {
            'user_id': analytics.user_id,
            'username': analytics.username,
            'session_count': analytics.session_count,
            'total_play_time': analytics.total_play_time,
            'total_bets': analytics.total_bets,
            'total_wagered': analytics.total_wagered,
            'avg_bet': analytics.avg_bet,
            'win_rate': win_rate,
            'total_wins': analytics.total_wins,
            'total_losses': analytics.total_losses,
            'total_won': analytics.total_won,
            'total_lost': analytics.total_lost,
            'net_profit': net_profit,
            'big_wins': analytics.big_wins_count,
            'biggest_win': analytics.biggest_win,
            'current_streak': analytics.current_streak,
            'streak_type': analytics.streak_type,
            'engagement_score': analytics.engagement_score,
            'churn_risk': analytics.churn_risk,
            'is_on_tilt': analytics.is_on_tilt,
            'is_frustrated': analytics.is_frustrated,
            'is_excited': analytics.is_excited,
        }

    # =========================================================================
    # AI ENGAGEMENT SYSTEM
    # =========================================================================

    def analyze_player_engagement(self, user_id: int) -> Dict:
        """AI-powered engagement analysis"""
        analytics = self.player_analytics.get(user_id)
        if not analytics:
            return {'action': 'none', 'confidence': 0, 'reasoning': 'No data'}

        reasons = []
        recommendations = []

        # Calculate engagement score
        engagement = 1.0
        churn_risk = 0.0

        # 1. Session Length Analysis
        if analytics.total_play_time < 30:
            engagement *= 0.8
            churn_risk += 0.1
            reasons.append("Short play time")
        elif analytics.total_play_time > 300:
            engagement *= 1.1  # Engaged player

        # 2. Betting Pattern Analysis
        if analytics.avg_bet > 1000:
            engagement *= 1.2  # High roller
        elif analytics.avg_bet < 50:
            engagement *= 0.9
            churn_risk += 0.1

        # 3. Win/Loss Streak Analysis
        if analytics.is_on_tilt:
            recommendations.append("DETECT_TILT: Player betting erratically")
            churn_risk += 0.3

        if analytics.is_frustrated:
            recommendations.append("DETECT_FRUSTRATION: Consider small guaranteed win")
            churn_risk += 0.2

        # 4. Time Since Last Big Win
        if analytics.last_big_win:
            hours_since = (datetime.now() - analytics.last_big_win).total_seconds() / 3600
            if hours_since > 2:
                churn_risk += 0.2
                recommendations.append(f"No big win in {hours_since:.1f} hours - consider triggering")
            elif hours_since < 0.5:
                recommendations.append("RECENT_BIG_WIN: Player is excited, leverage momentum")

        # 5. Net Profit Analysis
        net = analytics.total_won - analytics.total_lost
        if net < -analytics.total_wagered * 0.5:  # Lost more than 50%
            churn_risk += 0.3
            recommendations.append("HEAVY_LOSSES: High churn risk, consider intervention")
        elif net > analytics.total_wagered * 0.3:  # Winning a lot
            recommendations.append("PLAYER_WINNING: Consider adjusting for house edge")

        # 6. Betting Volatility
        if analytics.max_bet > analytics.avg_bet * 5:
            recommendations.append("HIGH_VOLATILITY: Player takes big risks")

        # 7. Session Count
        if analytics.session_count > 10 and analytics.avg_bet < 100:
            recommendations.append("REGULAR_LOW_BETTER: Loyal but conservative")

        # Determine recommended action
        if churn_risk > 0.7:
            action = "RETAIN"
            confidence = min(0.95, 0.5 + churn_risk * 0.5)
        elif analytics.is_on_tilt:
            action = "CALM"
            confidence = 0.8
        elif analytics.is_frustrated:
            action = "REWARD"
            confidence = 0.75
        elif churn_risk > 0.4:
            action = "ENGAGE"
            confidence = 0.6
        else:
            action = "NONE"
            confidence = 0.9

        return {
            'action': action,
            'confidence': confidence,
            'engagement_score': max(0, min(1, engagement)),
            'churn_risk': min(1.0, churn_risk),
            'reasons': reasons,
            'recommendations': recommendations
        }

    def get_ai_intervention_modifier(self, user_id: int) -> float:
        """Get AI-suggested win rate modifier"""
        if not self.global_settings.ai_engagement_enabled:
            return 1.0

        analysis = self.analyze_player_engagement(user_id)
        action = analysis['action']

        if action == "RETAIN":
            return 1.3  # Boost wins to keep player
        elif action == "CALM":
            return 0.9  # Slightly reduce volatility
        elif action == "REWARD":
            return 1.2  # Give small wins
        elif action == "ENGAGE":
            return 1.1  # Slightly boost engagement

        return 1.0  # Normal

    # =========================================================================
    # SLOT RESULT GENERATOR
    # =========================================================================

    def calculate_final_rtp(self, user_id: int, game_id: str) -> float:
        """Calculate final RTP with all factors considered"""
        # Start with effective RTP
        rtp = self.get_effective_rtp(user_id, game_id)

        # Apply AI modifier if enabled
        if self.global_settings.ai_engagement_enabled:
            ai_modifier = self.get_ai_intervention_modifier(user_id)
            rtp = rtp * ai_modifier

        return max(0.0, min(1.0, rtp))

    def should_player_win(self, user_id: int, game_id: str, base_payout: int) -> Tuple[bool, int]:
        """
        Determine if player should win this spin
        Returns: (should_win, final_payout)
        """
        # Check for spin override first
        # Note: spin_id would be generated before spin and checked after

        # Calculate effective RTP
        rtp = self.calculate_final_rtp(user_id, game_id)

        # Check intervention level
        intervention = self.get_player_intervention(user_id)

        if intervention:
            if intervention.intervention_level == InterventionLevel.LOCKED:
                return False, 0
            elif intervention.intervention_level == InterventionLevel.JACKPOT_MODE:
                return True, int(base_payout * 5)  # 5x jackpot payout

        # Determine win based on RTP
        should_win = random.random() < rtp

        if should_win:
            # Apply variance
            variance = random.uniform(0.8, 1.5)
            final_payout = int(base_payout * variance)

            # Ensure minimum win above bet
            if final_payout < base_payout * 0.5:
                final_payout = int(base_payout * 0.5)
        else:
            final_payout = 0

        return should_win, final_payout

    def adjust_result_for_engagement(self, user_id: int, current_result: int,
                                     bet_amount: int) -> int:
        """Adjust result based on AI engagement analysis"""
        if not self.global_settings.ai_engagement_enabled:
            return current_result

        analytics = self.player_analytics.get(user_id)
        if not analytics:
            return current_result

        # If player hasn't won in a while and is at risk of churning
        if analytics.current_streak >= self.global_settings.loss_streak_limit:
            # Guaranteed small win
            return int(bet_amount * random.uniform(1.2, 2.0))

        # If player is on tilt, give them a break with a win
        if analytics.is_on_tilt and random.random() < 0.3:
            return int(bet_amount * random.uniform(1.5, 3.0))

        return current_result

    # =========================================================================
    # ADMIN PANEL DATA
    # =========================================================================

    def get_admin_dashboard_data(self) -> Dict:
        """Get all data needed for admin panel"""
        # Calculate overall stats
        total_players = len(self.player_analytics)
        total_wagered = sum(a.total_wagered for a in self.player_analytics.values())
        total_won = sum(a.total_won for a in self.player_analytics.values())
        total_lost = sum(a.total_lost for a in self.player_analytics.values())

        # Find high-risk players
        high_risk_players = []
        for user_id, analytics in self.player_analytics.items():
            if analytics.churn_risk > 0.5:
                high_risk_players.append({
                    'user_id': user_id,
                    'username': analytics.username,
                    'churn_risk': analytics.churn_risk,
                    'engagement': analytics.engagement_score,
                    'reason': 'High churn risk'
                })

        # Players with interventions
        intervened_players = []
        for user_id, intervention in self.player_interventions.items():
            analytics = self.player_analytics.get(user_id)
            intervened_players.append({
                'user_id': user_id,
                'username': analytics.username if analytics else 'Unknown',
                'level': intervention.intervention_level.value,
                'custom_rtp': intervention.custom_rtp,
                'reason': intervention.reason,
                'expires_at': intervention.expires_at.isoformat() if intervention.expires_at else None
            })

        return {
            'global_settings': {
                'ai_enabled': self.global_settings.ai_engagement_enabled,
                'rtp_sweet_bonanza': self.global_settings.sweet_bonanza_rtp,
                'rtp_wolf_gold': self.global_settings.wolf_gold_rtp,
                'rtp_big_bass': self.global_settings.big_bass_rtp,
                'churn_threshold': self.global_settings.churn_risk_threshold,
                'loss_streak_limit': self.global_settings.loss_streak_limit,
            },
            'overview': {
                'total_players': total_players,
                'total_wagered': total_wagered,
                'total_won': total_won,
                'total_lost': total_lost,
                'net_house_profit': total_lost - total_won,
                'house_margin': (total_lost - total_won) / total_wagered if total_wagered > 0 else 0
            },
            'high_risk_players': high_risk_players,
            'intervened_players': intervened_players,
            'pending_overrides': len(self.spin_overrides)
        }

    def get_all_player_stats(self) -> List[Dict]:
        """Get stats for all players"""
        return [self.get_player_stats(uid) for uid in self.player_analytics.keys()]


# Singleton instance
_admin_system: Optional[CasinoAdminSystem] = None

def get_admin_system() -> CasinoAdminSystem:
    """Get or create admin system singleton"""
    global _admin_system
    if _admin_system is None:
        _admin_system = CasinoAdminSystem()
    return _admin_system
