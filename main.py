import datetime
import urllib.error
import urllib.request
import os

from bs4 import BeautifulSoup
import jinja2

def last_modified_date(filepath):
    modification_timestamp = os.path.getmtime(filepath)
    modification_date = datetime.date.fromtimestamp(modification_timestamp)
    return modification_date


def needs_refreshing(filepath):
    """Basically we assume that if the file in question is for a season
    before the current one, then the data has not been updated and we do
    not need to refresh it. If it is from the current season, then we
    check whether we have downloaded the file previously today and if
    not we re-download it. Note, that this assumes the file does exist.
    """
    today = datetime.date.today()
    return last_modified_date(filepath) != today


def download_if_stale(filepath, fileurl):
    """Given a file to download we check if there exists a file in
    the filesystem that was downloaded today, if so we do not download
    it again, otherwise we download it afresh.
    """
    if not os.path.exists(filepath) or needs_refreshing(filepath):
        try:
            urllib.request.urlretrieve(fileurl, filepath)
        except urllib.error.HTTPError:
            print('The {0} is not reachable'.format(fileurl))

html_template = """
<!DOCTYPE>
<html>
<head>
<title>Guess the Grid Statistics</title>
</head>
<body>
{}
</body>
</html>
"""

def make_tag(name, contents):
    return "<{}>{}</{}>".format(name, contents, name)

def create_table(headers, rows):
    header_cells = "".join([make_tag('th', h) for h in headers])
    head_row = make_tag('tr', header_cells)
    def make_row(row):
        return make_tag('tr', "".join([make_tag('td', r) for r in row]))
    body_rows = "".join([make_row(r) for r in rows])
    return make_tag('table', head_row + body_rows)

def main():
    data_file = 'leaderboard.html'
    leaderboard_url = 'http://guessthegrid.com/2016'

    download_if_stale(data_file, leaderboard_url)

    with open(data_file, 'r') as leaderboard_file:
        soup = BeautifulSoup(leaderboard_file, 'html.parser')
    
    player_names = ['tomato_plan', 'Seneska', 'jdanielp']
    # For now we just assume that for each race there are two scores for each
    # player. If we get to the point where someone has missed one, that should
    # not be a problem, inside each race well there should be two ordered lists
    # the qualifying score will be in the first one and the race score will be
    # in the second one, so we will know for sure where each score is coming
    # from and won't be wrong if, say, someone misses qualifying but scores for
    # the race.
    def points_for_race(race_title):
        race_well = race_title.parent.parent
        race_links = race_well.find_all('a')
        def points_for_player(player_name):
            def points_from_link(link):
                return int(link.parent.find('span').text)
            qualifying, race = [points_from_link(l) for l in race_links
                                if l.text == player_name]
            return qualifying, race, qualifying + race
        return {n: points_for_player(n) for n in player_names}

    race_titles = soup.find_all('h3', class_='pull-left')
    race_dictionaries = [(r['id'], points_for_race(r)) for r in race_titles]

    def get_totals(n):
        dictionaries = [d for _, d in race_dictionaries]
        return (sum(p[n][0] for p in dictionaries),
                sum(p[n][1] for p in dictionaries),
                sum(p[n][2] for p in dictionaries))

    totals_dictionary = ('totals', { n: get_totals(n) for n in player_names })
    
    race_dictionaries.append(totals_dictionary)

    tables = []
    
    def make_column_table(name, column):
        headers = ['Race', 'Allan', 'Dan', 'Charlotte']
        def make_row(name, race_dictionary):
            return [name, race_dictionary['tomato_plan'][column],
                          race_dictionary['jdanielp'][column],
                          race_dictionary['Seneska'][column]]
        rows = [make_row(n,d) for n,d in race_dictionaries]
        table = create_table(headers, rows)
        return make_tag('h2', name) + table

    for n,c in [('Qualification', 0), ('Race', 1), ('Weekend', 2)]:
        tables.append(make_column_table(n,c))

    html = html_template.format("\n".join(tables))
    with open('result.html', 'w') as output_file:
        output_file.write(html)
    

if __name__ == '__main__':
    main()