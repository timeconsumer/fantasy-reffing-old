import json, datetime
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, g, redirect, url_for, \
    render_template, flash
from table_mapping import Base, engine, Referee, Game, StatLine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
# create the flask app
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key'
))


@app.before_request
def before_request():
    print "starting request"
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    g.db = session


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.db.close()


@app.route('/')
def show_referees():
    """Gets a list of currently registered referees"""
    referees = g.db.query(Referee).all()
    update_game_counts(referees)
    return render_template('show_refs.html', referees=referees)


def update_game_counts(referees):
    for ref in referees:
        ref.games_reffed = g.db.query(StatLine).filter(StatLine.active_ref_id == ref.id).count()
    g.db.commit()


@app.route('/show_games')
def show_games():
    """Gets a list of currently played games"""
    referees = g.db.query(Referee).all()
    games = g.db.query(Game).all()
    for game in games:
        game.statlines = g.db.query(StatLine).filter(StatLine.game_id == game.id).all()
    return render_template('show_games.html', games=games, referees=referees)


@app.route('/add_a_ref')
def add_a_ref():
    """Used to render the Add a Referee template"""
    return render_template('add_ref.html')


@app.route('/add_ref', methods=['POST'])
def add_ref():
    """Adds a given referee to the database"""
    g.db.add(Referee(f_name=request.form['f_name'], l_name=request.form['l_name'],
                     number=request.form['number'], years_active=request.form['years']))
    g.db.commit()
    flash('New ref was successfully posted')
    return redirect(url_for('show_referees'))


@app.route('/add_a_game')
def add_a_game():
    """Used to render the Add a Game template"""
    referees = g.db.query(Referee).all()
    return render_template('add_game.html', referees=referees)


@app.route('/add_game', methods=['POST'])
def add_game():
    """Used to add a new game record to the database"""
    g.db.add(Game(date=datetime.datetime.strptime(
        request.form['date'], '%Y-%m-%d').date(), home_team=request.form['home_team'],
        away_team=request.form['away_team'], home_score=request.form['home_score'],
        away_score=request.form['away_score']))
    ref = g.db.query(Referee).filter_by(id=request.form["refId"]).one()
    ref.games_reffed = 1
    g.db.commit()
    flash('New game was successfully posted')
    return redirect(url_for('show_games'))


@app.route('/edit_game', methods=['POST'])
def edit_game():
    """Edit an existing game's details"""
    game = g.db.query(Game).filter_by(id=request.form['gameid']).one()
    game.home_team = request.form['home_team']
    game.away_team = request.form['away_team']
    game.date = datetime.datetime.strptime(
        request.form['date'], '%Y-%m-%d').date()
    game.home_score = request.form['home_score']
    game.away_score = request.form['away_score']
    g.db.commit()
    flash('Game edited!')
    return redirect(url_for('show_games'))


@app.route('/delete_game', methods=['POST'])
def delete_game():
    """Delete an existing game from the database via its ID"""
    statlines = g.db.query(StatLine).filter_by(game_id=request.form['gameid']).all()
    for stat in statlines:
        g.db.delete(stat)
    game = g.db.query(Game).filter_by(id=request.form['gameid']).one()
    g.db.delete(game)
    g.db.commit()
    flash('Game deleted!')
    return redirect(url_for('show_games'))


@app.route('/add_statline', methods=['POST'])
def add_statline():
    """Add a statline for a ref to a game"""
    g.db.add(StatLine(game_id=request.form["gameid"],
                      active_ref_id=request.form["refId"],
                      total_penalties=request.form["penalties"]))
    g.db.commit()
    flash('Stats added!')
    return redirect(url_for('show_games'))


@app.route('/game_info', methods=['GET', 'POST'])
def game_info():
    """Return the details of a game in JSON"""
    gameid = request.args["gameid"]
    game = g.db.query(Game).filter_by(id=gameid).one()
    return json.dumps(dict(id=game.id, date=str(game.date), home_team=game.home_team,
                           away_team=game.away_team, home_score=game.home_score,
                           away_score=game.away_score))


@app.route('/ref_info')
def get_ref():
    """Gets specific info for a ref based on their ID"""
    id = request.args.get('id')
    try:
        ref = g.db.query(Referee).filter_by(id=id).one()
    except NoResultFound:
        print "No result found for {0}".format(id)
        ref = None
    return render_template('ref_info.html', ref=ref)


@app.route('/search', methods=['POST'])
def search_db():
    """Used to search for a referee in the database"""
    print "asdfasdfsda"
    term = request.form["term"]
    q1 = g.db.query(Referee).filter(Referee.f_name.like('%{0}%'.format(term)))
    q2 = g.db.query(Referee).filter(Referee.l_name.like('%{0}%'.format(term)))

    results = q1.union(q2).all()
    return render_template('search_results.html', results=results)


# Run the app
app.run()
