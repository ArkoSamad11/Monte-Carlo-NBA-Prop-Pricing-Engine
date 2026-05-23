import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

import streamlit as st

@st.cache_data(ttl=3600)
def get_roster(home_team, away_team):
    response = requests.get(
        'http://localhost:8001/roster',
        params={'home_team': home_team, 'away_team': away_team}
    )
    return response.json()

st.markdown("""
<style>
    .stApp { background-color: #0f0f1a; }
    div[data-testid="stMetric"] {
        background: #1a1a2e;
        border: 1px solid #e07b6b;
        border-radius: 8px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label {
        font-size: 11px !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: clip;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
    }
    .stButton button {
        background-color: #e07b6b;
        color: white;
        border: none;
        border-radius: 6px;
        width: 100%;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title('NBA Player Prop Volatility Engine')

year = datetime.now().year
month = datetime.now().month
if month >= 10:
    season = str(year) + '-' + str(year + 1)[2:]
else:
    season = str(year - 1) + '-' + str(year)[2:]

events_response = requests.get('http://localhost:8001/events')
events = events_response.json()

event_display = []
event_ids = []
for e in events:
    event_display.append(e['display'])
    event_ids.append(e['id'])

col_left, col_right = st.columns([1, 2])

with col_left:
    selected_index = st.selectbox('Pick a game', range(len(event_display)), format_func=lambda x: event_display[x])
    selected_game = event_display[selected_index]
    teams_in_game = selected_game.split(' vs ')
    away_team = teams_in_game[0]
    home_team = teams_in_game[1]

    roster_response = requests.get(
        'http://localhost:8001/roster',
        params={'home_team': home_team, 'away_team': away_team}
    )
    roster = roster_response.json()

    manual_player = st.selectbox('Select player', roster)

    home_roster_response = requests.get(
        'http://localhost:8001/roster',
        params={'home_team': home_team, 'away_team': home_team}
    )
    home_roster = home_roster_response.json()

    if manual_player in home_roster:
        player_team = home_team
        opponent_team = away_team
    else:
        player_team = away_team
        opponent_team = home_team

    player_id_response = requests.get(
        'http://localhost:8001/playerid',
        params={'player_name': manual_player}
    )
    player_id = player_id_response.json()['id']
    image_url = 'https://cdn.nba.com/headshots/nba/latest/1040x760/' + str(player_id) + '.png'
    st.image(image_url, width=180)

    bookmaker = st.selectbox('Bookmaker', ['DraftKings', 'FanDuel', 'Kalshi', 'Other'])

    manual_stat = st.selectbox('Stat category', ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Threes', 'Turnovers'])
    manual_line = st.number_input('Prop line', min_value=0.0, step=0.5)
    manual_over_odds = st.number_input('Over odds (e.g. -110)', step=1, value=-110)
    manual_under_odds = st.number_input('Under odds (e.g. -120)', step=1, value=-120)

    st.write('Using a prediction market? Enter probability instead:')
    use_prob = st.checkbox('Enter as probability')
    if use_prob:
        over_prob = st.number_input('Hit probability (e.g. 72 for 72%)', min_value=0.0, max_value=100.0, step=1.0)
        if over_prob == 0 or over_prob == 100:
            st.error('Probability cannot be 0% or 100%')
        elif over_prob > 0:
            prob = over_prob / 100
            if prob > 0.5:
                manual_over_odds = int(-(prob / (1 - prob)) * 100)
            else:
                manual_over_odds = int(((1 - prob) / prob) * 100)
            under_prob = 100 - over_prob
            prob_under = under_prob / 100
            if prob_under > 0.5:
                manual_under_odds = int(-(prob_under / (1 - prob_under)) * 100)
            else:
                manual_under_odds = int(((1 - prob_under) / prob_under) * 100)
            st.write('Converted over odds: ' + str(manual_over_odds))
            st.write('Converted under odds: ' + str(manual_under_odds))

    find = st.button('Find Mispricing')

with col_right:
    if find:
        manual_prop = {
            'player': manual_player,
            'line': manual_line,
            'over_odds': int(manual_over_odds),
            'under_odds': int(manual_under_odds)
        }
        response = requests.post(
            'http://localhost:8001/log_signal',
            params={
                'player_name': manual_player,
                'season': season,
                'stat_category': manual_stat.lower(),
                'bookmaker': bookmaker,
                'player_team': player_team,
                'opponent_team': opponent_team
            },
            json=manual_prop
        )
        result = response.json()

        stat_response = requests.get(
            'http://localhost:8001/statlist',
            params={
                'player_name': manual_player,
                'season': season,
                'stat_category': manual_stat.lower()
            }
        )
        stat_data = stat_response.json()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(range(1, len(stat_data) + 1)),
            y=stat_data,
            name=manual_stat,
            marker_color='#e07b6b'
        ))
        fig.add_hline(
            y=manual_line,
            line_dash='dash',
            line_color='white'
        )
        fig.update_layout(
            title='Last 10 Games ' + manual_stat,
            xaxis_title='Game',
            yaxis_title=manual_stat,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig)

        if len(result) == 0:
            st.info(
                'No significant edge detected. Based on ' + manual_player +
                "'s last 10 games, the Monte Carlo simulation and weighted empirical model " +
                'both indicate the market is pricing this prop correctly.'
            )
        else:
            for signal in result:
                st.subheader(
                    signal['player'] + ' ' +
                    manual_stat.capitalize() + ' O/U ' +
                    str(signal['line'])
                )

                side_label = signal['side'].capitalize()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric('Avg (L10)', str(signal['rolling_avg']))
                c2.metric(
                    'MC ' + side_label,
                    str(round(signal['mc_prob'] * 100, 1)) + '%'
                )
                c3.metric(
                    'Emp ' + side_label,
                    str(round(signal['empirical_prob'] * 100, 1)) + '%'
                )
                c4.metric(
                    'Mkt ' + side_label,
                    str(round(signal['market_prob'] * 100, 1)) + '%'
                )

                st.metric(
                    'Edge Gap (MC vs Market)',
                    str(round(abs(signal['mc_gap']) * 100, 1)) + ' pp'
                )

                if signal['confidence'] == 'high':
                    st.success(
                        'HIGH CONFIDENCE: Monte Carlo and Weighted Empirical Models agree on an edge and direction.'
                    )
                else:
                    st.warning(
                        'MODERATE CONFIDENCE: Monte Carlo and Weighted Empirical Models disagree on a shared edge or direction'
                    )

                fig2 = go.Figure()
                fig2.add_trace(go.Histogram(
                    x=signal['simulations'],
                    nbinsx=50,
                    name='Simulated Outcomes',
                    marker_color='#e07b6b',
                    opacity=0.75
                ))
                fig2.add_vline(
                    x=manual_line,
                    line_dash='dash',
                    line_color='white',
                    annotation_text='Prop Line ' + str(manual_line),
                    annotation_position='top right'
                )
                fig2.update_layout(
                    title='Monte Carlo Distribution ' + manual_stat + ' (10,000 simulations)',
                    xaxis_title=manual_stat,
                    yaxis_title='Frequency',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig2)

                if signal['direction'] == 'underpriced':
                    if signal['side'] == 'over':
                        odds_for_kelly = manual_over_odds
                    else:
                        odds_for_kelly = manual_under_odds
                    p = signal['mc_prob']
                else:
                    if signal['side'] == 'over':
                        odds_for_kelly = manual_under_odds
                    else:
                        odds_for_kelly = manual_over_odds
                    p = 1 - signal['mc_prob']

                q = 1 - p

                if odds_for_kelly < 0:
                    decimal_odds = 1 + (100 / abs(odds_for_kelly))
                else:
                    decimal_odds = 1 + (odds_for_kelly / 100)

                b = decimal_odds - 1
                kelly = (p * b - q) / b
                half_kelly = kelly * 0.5

                if decimal_odds >= 2.0:
                    odds_display = '+' + str(round((decimal_odds - 1) * 100))
                else:
                    odds_display = str(round(-100 / (decimal_odds - 1)))

                if half_kelly <= 0:
                    st.warning(
                        'Edge detected on the ' + signal['side'] + ' (' +
                        'Kelly Criterion returns negative EV at current odds. Pass.'
                    )
                else:
                    if signal['direction'] == 'underpriced':
                        st.success(
                            'Bet the ' + signal['side'].upper() + '. ' +
                            'Monte Carlo probability exceeds that of Market.'
                        )
                    else:
                        if signal['side'] == 'over':
                            st.success(
                                'Bet the UNDER. ' +
                                'Market overpricing the over.'
                            )
                        else:
                            st.success(
                                'Bet the OVER. ' +
                                'Market overpricing the under.'
                            )
                    st.info(
                        'Kelly: ' + str(round(p * 100, 1)) + '% win prob at ' +
                        odds_display + ' odds. ' +
                        'Half Kelly: ' + str(round(half_kelly * 100, 1)) + '% of bankroll. ' +
                        'Quarter Kelly: ' + str(round(half_kelly * 50, 1)) + '%.'
                    )