#!/usr/bin/env python3
"""
Admin API Routes for Casino Control System
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import secrets

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# In-memory admin credentials (use database in production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # Change in production!

# Simple auth decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'success': False, 'error': 'Admin access required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# AUTH ROUTES
# =============================================================================

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Admin logged in'})

    return jsonify({'success': False, 'error': 'Invalid credentials'})


@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('is_admin', None)
    return jsonify({'success': True})


# =============================================================================
# GLOBAL SETTINGS
# =============================================================================

@admin_bp.route('/settings/rtp', methods=['GET'])
@admin_required
def get_all_rtp():
    """Get RTP settings for all games"""
    from engine.casino_admin import get_admin_system
    admin = get_admin_system()

    return jsonify({
        'success': True,
        'settings': {
            'sweet_bonanza': admin.get_global_rtp('sweet_bonanza'),
            'wolf_gold': admin.get_global_rtp('wolf_gold'),
            'big_bass': admin.get_global_rtp('big_bass'),
            'starlight': admin.get_global_rtp('starlight'),
            'gates_of_olympus': admin.get_global_rtp('gates_of_olympus'),
        }
    })


@admin_bp.route('/settings/rtp', methods=['POST'])
@admin_required
def set_rtp():
    """Set RTP for a game"""
    from engine.casino_admin import get_admin_system

    data = request.json
    game_id = data.get('game_id')
    rtp = float(data.get('rtp', 0.96))

    if not game_id:
        return jsonify({'success': False, 'error': 'Game ID required'})

    if rtp < 0.80 or rtp > 1.0:
        return jsonify({'success': False, 'error': 'RTP must be between 0.80 and 1.0'})

    admin = get_admin_system()
    admin.set_global_rtp(game_id, rtp)

    return jsonify({
        'success': True,
        'message': f'RTP for {game_id} set to {rtp}'
    })


@admin_bp.route('/settings/ai', methods=['GET'])
@admin_required
def get_ai_settings():
    """Get AI engagement settings"""
    from engine.casino_admin import get_admin_system
    admin = get_admin_system()

    return jsonify({
        'success': True,
        'ai_enabled': admin.global_settings.ai_engagement_enabled,
        'engagement_threshold': admin.global_settings.ai_engagement_threshold,
        'churn_threshold': admin.global_settings.churn_risk_threshold,
    })


@admin_bp.route('/settings/ai', methods=['POST'])
@admin_required
def toggle_ai():
    """Enable/disable AI engagement"""
    from engine.casino_admin import get_admin_system

    data = request.json
    enabled = data.get('enabled', False)

    admin = get_admin_system()
    admin.global_settings.ai_engagement_enabled = enabled

    return jsonify({
        'success': True,
        'message': f'AI Engagement {"enabled" if enabled else "disabled"}'
    })


# =============================================================================
# PLAYER INTERVENTION
# =============================================================================

@admin_bp.route('/intervention/<int:user_id>', methods=['GET'])
@admin_required
def get_player_intervention(user_id):
    """Get intervention for a player"""
    from engine.casino_admin import get_admin_system
    admin = get_admin_system()

    intervention = admin.get_player_intervention(user_id)
    analytics = admin.get_player_stats(user_id)

    return jsonify({
        'success': True,
        'intervention': {
            'level': intervention.intervention_level.value if intervention else 'none',
            'custom_rtp': intervention.custom_rtp if intervention else None,
            'win_modifier': intervention.win_rate_modifier if intervention else 1.0,
            'reason': intervention.reason if intervention else '',
            'expires_at': intervention.expires_at.isoformat() if intervention and intervention.expires_at else None
        } if intervention else None,
        'player_stats': analytics
    })


@admin_bp.route('/intervention/<int:user_id>', methods=['POST'])
@admin_required
def set_player_intervention(user_id):
    """Set intervention for a player"""
    from engine.casino_admin import get_admin_system, InterventionLevel

    data = request.json
    level = data.get('level', 'none')
    custom_rtp = data.get('custom_rtp')
    win_modifier = data.get('win_modifier', 1.0)
    reason = data.get('reason', '')
    expires_hours = data.get('expires_hours')

    try:
        level_enum = InterventionLevel(level)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid intervention level'})

    admin = get_admin_system()
    admin.set_player_intervention(
        user_id=user_id,
        level=level_enum,
        custom_rtp=custom_rtp,
        win_modifier=win_modifier,
        reason=reason,
        expires_hours=expires_hours
    )

    return jsonify({
        'success': True,
        'message': f'Intervention set for user {user_id}: {level}'
    })


@admin_bp.route('/intervention/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_player_intervention(user_id):
    """Remove intervention for a player"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()
    admin.clear_player_intervention(user_id)

    return jsonify({
        'success': True,
        'message': f'Intervention removed for user {user_id}'
    })


@admin_bp.route('/interventions', methods=['GET'])
@admin_required
def get_all_interventions():
    """Get all active interventions"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()

    interventions = []
    for user_id, intervention in admin.player_interventions.items():
        analytics = admin.player_analytics.get(user_id)
        interventions.append({
            'user_id': user_id,
            'username': analytics.username if analytics else 'Unknown',
            'level': intervention.intervention_level.value,
            'custom_rtp': intervention.custom_rtp,
            'reason': intervention.reason,
            'expires_at': intervention.expires_at.isoformat() if intervention.expires_at else None
        })

    return jsonify({
        'success': True,
        'interventions': interventions
    })


# =============================================================================
# SPIN OVERRIDE
# =============================================================================

@admin_bp.route('/override', methods=['POST'])
@admin_required
def create_override():
    """Create a spin override"""
    from engine.casino_admin import get_admin_system

    data = request.json
    user_id = data.get('user_id')
    game_id = data.get('game_id')
    spin_id = data.get('spin_id') or secrets.token_hex(8)
    force_win = data.get('force_win', False)
    force_lose = data.get('force_lose', False)
    exact_payout = data.get('exact_payout')
    expires_minutes = data.get('expires_minutes', 5)

    if not user_id or not game_id:
        return jsonify({'success': False, 'error': 'user_id and game_id required'})

    admin = get_admin_system()
    admin.create_spin_override(
        user_id=user_id,
        game_id=game_id,
        spin_id=spin_id,
        force_win=force_win,
        force_lose=force_lose,
        exact_payout=exact_payout,
        expires_minutes=expires_minutes
    )

    return jsonify({
        'success': True,
        'spin_id': spin_id,
        'message': f'Override created for spin {spin_id}'
    })


@admin_bp.route('/override/<spin_id>', methods=['DELETE'])
@admin_required
def cancel_override(spin_id):
    """Cancel a pending override"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()
    if spin_id in admin.spin_overrides:
        del admin.spin_overrides[spin_id]
        return jsonify({'success': True, 'message': f'Override {spin_id} cancelled'})

    return jsonify({'success': False, 'error': 'Override not found'})


# =============================================================================
# PLAYER ANALYTICS
# =============================================================================

@admin_bp.route('/players', methods=['GET'])
@admin_required
def get_all_players():
    """Get all players with analytics"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()
    players = admin.get_all_player_stats()

    return jsonify({
        'success': True,
        'players': players
    })


@admin_bp.route('/player/<int:user_id>', methods=['GET'])
@admin_required
def get_player_full(user_id):
    """Get full player analytics and AI analysis"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()

    stats = admin.get_player_stats(user_id)
    if not stats:
        return jsonify({'success': False, 'error': 'Player not found'})

    ai_analysis = admin.analyze_player_engagement(user_id)
    intervention = admin.get_player_intervention(user_id)

    return jsonify({
        'success': True,
        'stats': stats,
        'ai_analysis': ai_analysis,
        'intervention': {
            'level': intervention.intervention_level.value if intervention else None,
            'custom_rtp': intervention.custom_rtp if intervention else None,
        } if intervention else None
    })


@admin_bp.route('/player/<int:user_id>/ai', methods=['POST'])
@admin_required
def run_ai_analysis(user_id):
    """Manually trigger AI analysis for a player"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()
    analysis = admin.analyze_player_engagement(user_id)

    return jsonify({
        'success': True,
        'analysis': analysis
    })


# =============================================================================
# DASHBOARD
# =============================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Get admin dashboard data"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()
    data = admin.get_admin_dashboard_data()

    return jsonify({
        'success': True,
        'dashboard': data
    })


@admin_bp.route('/high-risk', methods=['GET'])
@admin_required
def get_high_risk_players():
    """Get players at high risk of churning"""
    from engine.casino_admin import get_admin_system

    admin = get_admin_system()

    high_risk = []
    for user_id, analytics in admin.player_analytics.items():
        if analytics.churn_risk > admin.global_settings.churn_risk_threshold:
            ai_analysis = admin.analyze_player_engagement(user_id)
            high_risk.append({
                'user_id': user_id,
                'username': analytics.username,
                'churn_risk': analytics.churn_risk,
                'engagement': analytics.engagement_score,
                'ai_recommendation': ai_analysis['action'],
                'recommendations': ai_analysis['recommendations']
            })

    return jsonify({
        'success': True,
        'high_risk_players': high_risk
    })


# =============================================================================
# AI ENGAGEMENT ACTIONS
# =============================================================================

@admin_bp.route('/action/<int:user_id>', methods=['POST'])
@admin_required
def execute_ai_action(user_id):
    """Execute AI-recommended action for a player"""
    from engine.casino_admin import get_admin_system, InterventionLevel

    data = request.json
    action = data.get('action')
    custom_rtp = data.get('custom_rtp')
    expires_hours = data.get('expires_hours', 1)

    admin = get_admin_system()

    if action == 'RETAIN':
        admin.set_player_intervention(
            user_id=user_id,
            level=InterventionLevel.BOOSTED,
            custom_rtp=custom_rtp or 1.1,
            reason='AI Retention Action',
            expires_hours=expires_hours
        )
    elif action == 'CALM':
        admin.set_player_intervention(
            user_id=user_id,
            level=InterventionLevel.MODERATE,
            reason='AI Calm Action - Reduce volatility',
            expires_hours=expires_hours
        )
    elif action == 'REWARD':
        admin.set_player_intervention(
            user_id=user_id,
            level=InterventionLevel.BOOSTED,
            custom_rtp=custom_rtp or 1.15,
            reason='AI Reward Action',
            expires_hours=expires_hours
        )
    elif action == 'LOCK':
        admin.set_player_intervention(
            user_id=user_id,
            level=InterventionLevel.LOCKED,
            reason='Admin manual lock',
            expires_hours=expires_hours
        )
    elif action == 'JACKPOT':
        admin.set_player_intervention(
            user_id=user_id,
            level=InterventionLevel.JACKPOT_MODE,
            reason='Jackpot mode activated',
            expires_hours=expires_hours
        )
    else:
        admin.clear_player_intervention(user_id)

    return jsonify({
        'success': True,
        'message': f'Action {action} executed for user {user_id}'
    })
