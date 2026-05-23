import pytest
from unittest.mock import patch
from src.analysis.mispricing import find_mispricing


MOCK_PROP = {
    'player': 'Test Player',
    'line': 25.5,
    'over_odds': -110,
    'under_odds': -110
}


def mock_find_impliedvol_high_gap_over(player_name, season, stat_category, prop, player_team=None, opponent_team=None):
    # MC over 75%, empirical over 70%, market over 50% — large gap, both agree, over underpriced
    return 0.75, 0.25, 0.70, 0.30, 0.50, 0.50, 0.3, 25.0, 25.5, [25.0] * 10000


def mock_find_impliedvol_no_edge(player_name, season, stat_category, prop, player_team=None, opponent_team=None):
    # MC over 52%, market over 50% — gap below threshold
    return 0.52, 0.48, 0.51, 0.49, 0.50, 0.50, 0.3, 25.0, 25.5, [25.0] * 10000


def mock_find_impliedvol_overpriced(player_name, season, stat_category, prop, player_team=None, opponent_team=None):
    # MC over 35%, market over 50% — over overpriced, fade over
    return 0.35, 0.65, 0.30, 0.70, 0.50, 0.50, 0.3, 25.0, 25.5, [25.0] * 10000


def mock_find_impliedvol_mc_only(player_name, season, stat_category, prop, player_team=None, opponent_team=None):
    # MC over 60%, empirical over 48%, market over 50% — MC flags edge, empirical does not
    return 0.60, 0.40, 0.48, 0.52, 0.50, 0.50, 0.3, 25.0, 25.5, [25.0] * 10000


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_high_gap_over)
def test_high_gap_over_flagged(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert len(results) == 1
    assert results[0]['side'] == 'over'
    assert results[0]['direction'] == 'underpriced'


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_no_edge)
def test_no_edge_returns_empty(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert len(results) == 0


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_overpriced)
def test_overpriced_over_flagged(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert len(results) == 1
    assert results[0]['direction'] == 'overpriced'


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_high_gap_over)
def test_high_confidence_both_agree(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert results[0]['confidence'] == 'high'


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_mc_only)
def test_moderate_confidence_mc_only(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert results[0]['confidence'] == 'moderate'


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_high_gap_over)
def test_result_contains_required_keys(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    required_keys = ['player', 'line', 'side', 'mc_prob', 'empirical_prob', 'market_prob', 'mc_gap', 'direction', 'confidence', 'realized_vol', 'rolling_avg', 'simulations']
    for key in required_keys:
        assert key in results[0]


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_high_gap_over)
def test_mc_prob_rounded_to_four_decimals(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert len(str(results[0]['mc_prob']).split('.')[-1]) <= 4


@patch('src.analysis.mispricing.find_impliedvol', side_effect=mock_find_impliedvol_high_gap_over)
def test_larger_gap_side_selected(mock_iv):
    results = find_mispricing('Test Player', '2025-26', 'points', MOCK_PROP)
    assert results[0]['mc_gap'] == round(0.75 - 0.50, 4)