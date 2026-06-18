
from dotenv import load_dotenv
import requests
import os


def american_to_implied(odds):
     """
    Converts American odds to an implied probability.

    Args:
        odds: American odds for one side of a prop (Integer).
              Negative odds indicate the favorite (e.g. -110).
              Positive odds indicate the underdog (e.g. +130).
    Returns:
        A float representing the raw implied probability including the sportsbook's
        vig.
        
    Raises:
        AssertionError: If odds is not an integer.
        ValueError: If odds is 0, which is not a valid American odds value.
    """
    
    assert type(odds) == int
    if odds == 0:
        raise ValueError('Odds cannot be equivalent to 0')
    if odds < 0:
        return (abs(odds)) / (abs(odds)+100)
    elif odds > 0:
        return (100) / (odds + 100)
    

def remove_vigorish(over_implied, under_implied):
    pythondef remove_vigorish(over_implied, under_implied):
    """
    Removes the sportsbook's margin (vig) from raw implied probabilities so both
    sides sum to exactly 1.0, producing the sportsbook's true believed probability
    for each side of the prop.

    Args:
        over_implied: Raw implied probability of the over derived from American odds (Float).
        under_implied: Raw implied probability of the under derived from American odds (Float).
    Returns:
        A tuple of two floats:
            fair_over: Devigged probability of the over hitting (Float).
            fair_under: Devigged probability of the under hitting (Float).
        Both values sum to exactly 1.0.
    """
    
    fair_over = (over_implied) / (over_implied + under_implied)
    fair_under = (under_implied) / (over_implied + under_implied)
    return fair_over, fair_under


load_dotenv()
def get_events_ids():
     """
    Fetches all available NBA game events from the Odds API.
    Originally used to automatically populate game selection and prop lines
    in the dashboard. Replaced by manual prop entry after the Odds API
    integration was removed from the product.

    Returns:
        A list of dictionaries, each containing:
            id: Unique event identifier used to fetch props via get_odds (String).
            display: Human-readable matchup string in the format
                     'Away Team vs Home Team' used to populate the
                     game selection dropdown in the dashboard (String).
    """
    
    events_list = []
    API_KEY = os.getenv('ODDS_API_KEY')
    response = requests.get('https://api.the-odds-api.com/v4/sports/basketball_nba/events', params={'apiKey': API_KEY})
    for event in response.json():
        events_list.append({'id': event['id'], 'display': f"{event['away_team']} vs {event['home_team']}"})
    return events_list


def get_market(stat_category):
    """
    Maps a user-facing stat category string to the corresponding Odds API market key.

    Args:
        stat_category: The selected stat for the player prop. Must be one of:
                       'points', 'rebounds', 'assists', 'steals', 'blocks',
                       'threes', 'turnovers' (String).
    Returns:
        A string representing the Odds API market key for the selected stat category
        (e.g. 'points' maps to 'player_points').
        
    Raises:
        ValueError: If stat_category is not one of the seven supported categories.
    """
    
    stat_category = stat_category.lower().replace(' ', '')
    markets = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists',
        'steals': 'player_steals', 'blocks': 'player_blocks', 'threes': 'player_threes', 'turnovers': 'player_turnovers'}
    if stat_category not in markets:
        raise ValueError('Invalid stat category. Options are points, rebounds, assists, steals, blocks, threes, turnovers.')
    return markets[stat_category]


def get_odds(event_id, stat_category):
    """
    Fetches American odds for a specific NBA game event and stat category from the Odds API.

    Args:
        event_id: Unique event identifier returned by get_events_ids (String).
        stat_category: The selected stat for the player prop. Must be one of:
                       'points', 'rebounds', 'assists', 'steals', 'blocks',
                       'threes', 'turnovers' (String).
    Returns:
        A JSON response from the Odds API containing bookmaker odds for the
        selected event and stat category in American odds format.
    Raises:
        AssertionError: If event_id is not a string.
    """
    
    assert type(event_id) == str
    API_KEY = os.getenv('ODDS_API_KEY')
    market = get_market(stat_category)
    response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds',
        params={ 'apiKey': API_KEY, 'regions': 'us', 'markets': market,'oddsFormat': 'american'})
    return response.json()


def parse_props(response):
    """
    Parses the raw Odds API response into a structured list of player props,
    matching over and under outcomes by player name and prop line.

    Args:
        response: Raw JSON response from get_odds containing bookmaker odds (Dict).
        
    Returns:
        A list of dictionaries, each representing a matched over/under prop containing:
            player: Player name (String).
            line: The prop line (Float).
            over_odds: American odds for the over (Integer).
            under_odds: American odds for the under (Integer).
            sportsbook: Name of the bookmaker the odds were sourced from (String).
        Only props where both an over and under outcome exist are included.
    """
    
    props = []
    overs = []
    unders = []
    unders_map = {}
    for bookmaker in response['bookmakers']:
        for market in bookmaker['markets']:
            for outcome in market['outcomes']:
                if outcome['name'] == 'Over':
                    overs.append(outcome)
                elif outcome['name'] == 'Under':
                    unders.append(outcome)
    for under in unders:
        key = (under['description'], under['point'])
        unders_map[key] = under['price']
    for over in overs:
        key = (over['description'], over['point'])
        if key in unders_map:
            props.append({
    'player': over['description'], 'line': over['point'], 'over_odds': over['price'], 'under_odds': unders_map[key], 'sportsbook': bookmaker['title']})
    return props
