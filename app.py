"""
Simple URL forwarder with entries stored in a sqlite db.

ADMIN_TOKEN must be set.
"""
import json
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

dbconn = sqlite3.connect('data/urls.db')
cursor = dbconn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_entries'")
if not cursor.fetchone():
    sql.init(dbconn)
dbconn.close()


@app.before_request
def prepare():
    """Connect to the database."""
    flask.g.dbconn = sqlite3.connect('data/urls.db')


@app.after_request
def finalize(response):
    """Close database connection."""
    flask.g.dbconn.close()
    return response


@app.route('/')
def list_entries():
    """List available entries."""
    return flask.render_template('entries.html', entries=sql.get_all(flask.g.dbconn))


@app.route('/update/', methods=['GET', 'POST'])
def update_entry():
    """
    Add, edit, or delete entry.

    A valid token must be provided.

    Only ADMIN_TOKEN may add and delete entries.
    """
    if flask.request.method == 'GET':
        return flask.render_template('update.html')
    if access_key := flask.request.headers.get('X-Access-Key'):
        try:
            if len(flask.request.json):
                args = flask.request.json
            else:
                args = dict(flask.request.form)
        except json.decoder.JSONDecodeError:
            logging.error('here')
            flask.abort(status=400)
        except TypeError:
            logging.error(f'here2 {flask.request.form} {flask.request.json}')
            flask.abort(status=400)
    else:
        args = dict(flask.request.form)
        access_key = args['token']
    if  access_key and 'identifier' in args and 'new_url' in args:
        entry = sql.get_entry(flask.g.dbconn, args['identifier'])
        if entry:
            if access_key == entry['token'] or access_key == ADMIN_TOKEN:
                if args['new_url']:
                    sql.update_url(flask.g.dbconn, args['identifier'], args['new_url'])
                    return flask.Response('200: Entry updated successfully', status=200)
                if access_key == ADMIN_TOKEN:
                    sql.delete_url(flask.g.dbconn, args['identifier'])
                    return flask.Response('200: Entry deleted successfully', status=200)
            return flask.Response('400: Bad input', status=400)
        if access_key == ADMIN_TOKEN:
            if not args['new_url']:
                return flask.Response('400: Bad input', status=400)
            try:
                new_token = sql.add_url(flask.g.dbconn, args['identifier'], args['new_url'])
            except sqlite3.IntegrityError:
                return flask.Response('400: Identifier already exists', status=400)
            return flask.render_template('added.html',
                                         identifier=args['identifier'],
                                         stable_url=flask.url_for('forward',
                                                                  _external=True,
                                                                  identifier=args['identifier']),
                                         forward_url=args['new_url'],
                                         token=new_token)
        return flask.Response('400: Bad input', status=400)
    return flask.Response('400: Token is required', status=400)


@app.route('/goto/<identifier>/')
def forward(identifier: str):
    """
    Forward to the given url.

    Forwards with code 307.
    """
    url = sql.get_url(flask.g.dbconn, identifier)
    if not url:
        return flask.Response(status=404)
    return flask.redirect(url, code=307)
