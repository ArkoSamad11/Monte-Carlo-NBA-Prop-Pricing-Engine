<<<<<<< HEAD
from dotenv import load_dotenv
import requests
import os


def american_to_implied(odds):
    assert type(odds) == int
    if odds == 0:
        raise ValueError('Odds cannot be equivalent to 0')
    if odds < 0:
        return (abs(odds)) / (abs(odds)+100)
    elif odds > 0:
        return (100) / (odds + 100)
    

def remove_vigorish(over_implied, under_implied):
    fair_over = (over_implied) / (over_implied + under_implied)
    fair_under = (under_implied) / (over_implied + under_implied)
    return fair_over, fair_under


load_dotenv()
def get_events_ids():
    events_list = []
    API_KEY = os.getenv('ODDS_API_KEY')
    response = requests.get('https://api.the-odds-api.com/v4/sports/basketball_nba/events', params={'apiKey': API_KEY})
    for event in response.json():
        events_list.append({'id': event['id'], 'display': f"{event['away_team']} vs {event['home_team']}"})
    return events_list


def get_market(stat_category):
    stat_category = stat_category.lower().replace(' ', '')
    markets = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists',
        'steals': 'player_steals', 'blocks': 'player_blocks', 'threes': 'player_threes', 'turnovers': 'player_turnovers'}
    if stat_category not in markets:
        raise ValueError('Invalid stat category. Options are points, rebounds, assists, steals, blocks, threes, turnovers.')
    return markets[stat_category]


def get_odds(event_id, stat_category):
    assert type(event_id) == str
    API_KEY = os.getenv('ODDS_API_KEY')
    market = get_market(stat_category)
    response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds',
        params={ 'apiKey': API_KEY, 'regions': 'us', 'markets': market,'oddsFormat': 'american'})
    return response.json()


def parse_props(response):
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
=======
from dotenv import load_dotenv
import requests
import os


def american_to_implied(odds):
    assert type(odds) == int
    if odds == 0:
        raise ValueError('Odds cannot be equivalent to 0')
    if odds < 0:
        return (abs(odds)) / (abs(odds)+100)
    elif odds > 0:
        return (100) / (odds + 100)
    

def remove_vigorish(over_implied, under_implied):
    fair_over = (over_implied) / (over_implied + under_implied)
    fair_under = (under_implied) / (over_implied + under_implied)
    return fair_over, fair_under


load_dotenv()
def get_events_ids():
    events_list = []
    API_KEY = os.getenv('ODDS_API_KEY')
    response = requests.get('https://api.the-odds-api.com/v4/sports/basketball_nba/events', params={'apiKey': API_KEY})
    for event in response.json():
        events_list.append({'id': event['id'], 'display': f"{event['away_team']} vs {event['home_team']}"})
    return events_list


def get_market(stat_category):
    stat_category = stat_category.lower().replace(' ', '')
    markets = {'points': 'player_points', 'rebounds': 'player_rebounds', 'assists': 'player_assists',
        'steals': 'player_steals', 'blocks': 'player_blocks', 'threes': 'player_threes', 'turnovers': 'player_turnovers'}
    if stat_category not in markets:
        raise ValueError('Invalid stat category. Options are points, rebounds, assists, steals, blocks, threes, turnovers.')
    return markets[stat_category]


def get_odds(event_id, stat_category):
    assert type(event_id) == str
    API_KEY = os.getenv('ODDS_API_KEY')
    market = get_market(stat_category)
    response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds',
        params={ 'apiKey': API_KEY, 'regions': 'us', 'markets': market,'oddsFormat': 'american'})
    return response.json()


def parse_props(response):
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
>>>>>>> 4ebe7d745d0e4970ddf29786bc1a0d1bc8d07616
