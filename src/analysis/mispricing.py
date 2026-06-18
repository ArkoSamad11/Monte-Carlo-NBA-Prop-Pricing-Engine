from src.analysis.implied_vol import find_impliedvol


def find_mispricing(player_name, season, stat_category, prop, player_team=None, opponent_team=None, threshold=0.03, bookmaker='DraftKings'):
    """
    Identifies whether or not there is discrepancy between Monte Carlo and Weighted Empirical probability and that of the market in 
    a specified direction (over/under).

    Args:
        Args:
        player_name: Name of the player (String).
        season: Name of the season in the format 20XX-YY passed into the NBA Stats API (String).
        stat_category: The selected stat for the player prop (String).
        prop: Dictionary containing the prop line and market odds. Must include
              'line', 'over_odds', and 'under_odds' keys (Dict).
        player_team: Initialized to None. The team that the selected player is on (String).
        opponent_team: Initialized to None. The team that the selected player is playing against (String).
        threshold: Initialized to 0.03. Minimum absolute gap between Monte Carlo probability and
                   devigged market probability required to flag a signal. Below this threshold
                   the model considers the prop fairly priced and returns nothing (Float).
        bookmaker: Initialized to DraftKings. Affects produced probabilities as sportsbook hit
                   requirements differ between sportsbooks and prediction markets (String).
    Returns:
        results: A list containing at most one signal dictionary. Empty list if no edge is detected.
                 Each signal contains:
                     player: Player name (String).
                     line: The prop line (Float).
                     side: the side (over/under) with the larger absolute percentage point gap (String).
                     mc_prob: Monte Carlo probability for the flagged side (Float).
                     empirical_prob: Weighted empirical probability for the flagged side (Float).
                     market_prob: Market probability for the flagged side (Float).
                     mc_gap: Gap between mc_prob and market_prob. Positive means underpriced,
                             negative means overpriced (Float).
                     direction: 'underpriced' if mc_gap > 0, 'overpriced' if mc_gap < 0 (String).
                     confidence: 'high' if both Monte Carlo and empirical models agree on a direction
                                 and shared edge. 'moderate' otherwise (String).
                     realized_vol: Log Return Std. Dev. of the player's L10 performance. Logged
                                   to the database for post-hoc analysis (Float).
                     rolling_avg: Raw unweighted rolling average for the player in the selected
                                  stat without pace or DRTG adjustment (Float).
                     simulations: List of 10,000 simulated outcomes for dashboard visualization (List).
    """
    
    mc_prob_over, mc_prob_under, empirical_prob_over, empirical_prob_under, fair_over, fair_under, realized_vol, S, K, 
    simulations = find_impliedvol(player_name, season, stat_category, prop, player_team=player_team, opponent_team=opponent_team, bookmaker=bookmaker)

    results = []

    mc_over_gap = mc_prob_over - fair_over
    mc_under_gap = mc_prob_under - fair_under
    emp_over_gap = empirical_prob_over - fair_over
    emp_under_gap = empirical_prob_under - fair_under

    # Assigns values for either over or under, whichever direction has the larger gap for that player and prop.
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
        
    # Checks if the difference between the Monte Carlo probability and Market probability is exceeds 3% threshold.
    if abs(primary_mc_gap) > threshold:
        if primary_mc_gap > 0:
            direction = 'underpriced'
        else:
            direction = 'overpriced'

        both_agree = (
            (primary_mc_gap > 0 and primary_emp_gap > 0) or
            (primary_mc_gap < 0 and primary_emp_gap < 0))

        emp_gap_significant = abs(primary_emp_gap) > threshold
        # Decides between high or moderate confidence level
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
