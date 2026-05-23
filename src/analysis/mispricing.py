<<<<<<< HEAD
from src.analysis.implied_vol import find_impliedvol


def find_mispricing(player_name, season, stat_category, prop, player_team=None, opponent_team=None, threshold=0.03):
    mc_prob_over, mc_prob_under, empirical_prob_over, empirical_prob_under, fair_over, fair_under, realized_vol, S, K, simulations = find_impliedvol(
        player_name, season, stat_category, prop,
        player_team=player_team,
        opponent_team=opponent_team
    )

    results = []

    mc_over_gap = mc_prob_over - fair_over
    mc_under_gap = mc_prob_under - fair_under
    emp_over_gap = empirical_prob_over - fair_over
    emp_under_gap = empirical_prob_under - fair_under

    if abs(mc_over_gap) >= abs(mc_under_gap):
        primary_side = 'over'
        primary_mc_gap = mc_over_gap
        primary_emp_gap = emp_over_gap
        mc_prob = mc_prob_over
        emp_prob = empirical_prob_over
        market_prob = fair_over
    else:
        primary_side = 'under'
        primary_mc_gap = mc_under_gap
        primary_emp_gap = emp_under_gap
        mc_prob = mc_prob_under
        emp_prob = empirical_prob_under
        market_prob = fair_under

    if abs(primary_mc_gap) > threshold:
        if primary_mc_gap > 0:
            direction = 'underpriced'
        else:
            direction = 'overpriced'

        both_agree = (
            (primary_mc_gap > 0 and primary_emp_gap > 0) or
            (primary_mc_gap < 0 and primary_emp_gap < 0)
        )

        emp_gap_significant = abs(primary_emp_gap) > threshold
        if both_agree and emp_gap_significant:
            confidence = 'high'
        else:
            confidence = 'moderate'

        results.append({
            'player': player_name,
            'line': prop['line'],
            'side': primary_side,
            'mc_prob': round(mc_prob, 4),
            'empirical_prob': round(emp_prob, 4),
            'market_prob': round(market_prob, 4),
            'mc_gap': round(primary_mc_gap, 4),
            'direction': direction,
            'confidence': confidence,
            'realized_vol': round(realized_vol, 4),
            'rolling_avg': round(S, 2),
            'simulations': simulations
        })

    return results
=======
from src.analysis.implied_vol import find_impliedvol


def find_mispricing(player_name, season, stat_category, prop, player_team=None, opponent_team=None, threshold=0.03):
    mc_prob_over, mc_prob_under, empirical_prob_over, empirical_prob_under, fair_over, fair_under, realized_vol, S, K, simulations = find_impliedvol(
        player_name, season, stat_category, prop,
        player_team=player_team,
        opponent_team=opponent_team
    )

    results = []

    mc_over_gap = mc_prob_over - fair_over
    mc_under_gap = mc_prob_under - fair_under
    emp_over_gap = empirical_prob_over - fair_over
    emp_under_gap = empirical_prob_under - fair_under

    if abs(mc_over_gap) >= abs(mc_under_gap):
        primary_side = 'over'
        primary_mc_gap = mc_over_gap
        primary_emp_gap = emp_over_gap
        mc_prob = mc_prob_over
        emp_prob = empirical_prob_over
        market_prob = fair_over
    else:
        primary_side = 'under'
        primary_mc_gap = mc_under_gap
        primary_emp_gap = emp_under_gap
        mc_prob = mc_prob_under
        emp_prob = empirical_prob_under
        market_prob = fair_under

    if abs(primary_mc_gap) > threshold:
        if primary_mc_gap > 0:
            direction = 'underpriced'
        else:
            direction = 'overpriced'

        both_agree = (
            (primary_mc_gap > 0 and primary_emp_gap > 0) or
            (primary_mc_gap < 0 and primary_emp_gap < 0)
        )

        emp_gap_significant = abs(primary_emp_gap) > threshold
        if both_agree and emp_gap_significant:
            confidence = 'high'
        else:
            confidence = 'moderate'

        results.append({
            'player': player_name,
            'line': prop['line'],
            'side': primary_side,
            'mc_prob': round(mc_prob, 4),
            'empirical_prob': round(emp_prob, 4),
            'market_prob': round(market_prob, 4),
            'mc_gap': round(primary_mc_gap, 4),
            'direction': direction,
            'confidence': confidence,
            'realized_vol': round(realized_vol, 4),
            'rolling_avg': round(S, 2),
            'simulations': simulations
        })

    return results
>>>>>>> 4ebe7d745d0e4970ddf29786bc1a0d1bc8d07616
