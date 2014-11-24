import os
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
    DATABASE=os.path.join(app.root_path, 'flaskapp.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


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
    return render_template('show_refs.html', referees=referees)


@app.route('/add_a_ref')
def add_a_ref():
    """Used to render the Add a Referee template"""
    return render_template('add_ref.html')


@app.route('/add', methods=['POST'])
def add_ref():
    """Adds a given referee to the database"""
    g.db.add(Referee(f_name=request.form['f_name'], l_name=request.form['l_name'],
                     number=request.form['number'], years_active=request.form['years']))
    g.db.commit()
    flash('New ref was successfully posted')
    return redirect(url_for('show_referees'))


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
