import logging
import os
import sqlite3
import sys

import flask

import sql

app = flask.Flask(__name__)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    logging.error('ADMIN_TOKEN must be set')
    sys.exit(1)

dbconn = sqlite3.connect('urls.db')
cursor = dbconn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_entries'")
if not cursor.fetchone():
    sql.init(dbconn)
dbconn.close()

@app.before_request
def prepare():
    """Open the database connection and get the current user."""
    flask.g.dbconn = sqlite3.connect('urls.db')


@app.after_request
def finalize(response):
    flask.g.dbconn.close()
    return response


@app.route('/')
def list_entries():
    return flask.jsonify(sql.get_all(flask.g.dbconn))


@app.route('/update/', methods=['GET', 'POST'])
def update_entry():
    if flask.request.method == 'GET':
        return flask.render_template('update.html')
    elif flask.request.method == 'POST':
        args = dict(flask.request.form)
        if 'token' in args and 'identifier' in args and 'new_url' in args:
            entry = sql.get_entry(flask.g.dbconn, args['identifier'])
            if entry:
                logging.error(f'Entry: {entry}')
                logging.error(f'Args: {args}')
                if entry['token'] == args['token'] or args['token'] == ADMIN_TOKEN:
                    sql.update_url(flask.g.dbconn, args['identifier'], args['new_url'])
                    return flask.Response('200: Entry updated successfully', status=200)
                else:
                    return flask.Response('400: Bad input', status=400)
            else:
                if args['token'] == ADMIN_TOKEN:
                    try:
                        new_token = sql.add_url(flask.g.dbconn, args['identifier'], args['new_url'])
                    except sqlite3.IntegrityError:
                        return flask.response('Identifier already exists', status=400)
                    return flask.jsonify({'identifier': args['identifier'],
                                          'forward_to': args['new_url'],
                                          'token': new_token})
                else:
                    return flask.Response('400: Bad input', status=400)
    return flask.Response('400: Token is required', status=400)


@app.route('/goto/<identifier>/')
def forward(identifier: str):
    url = sql.get_url(flask.g.dbconn, identifier)
    if not url:
        return flask.Response(status=404)
    return flask.redirect(url)
