"""SQL queries for the forwarder."""
import secrets

def init(dbconn):
    """Initialise DB (create table)."""
    cursor = dbconn.cursor()
    cursor.execute('CREATE TABLE url_entries '
                   '(identifier TEXT PRIMARY KEY, forward_to TEXT, update_token TEXT)')


def delete_url(dbconn, identifier: str):
    """Delete an entry."""
    cursor = dbconn.cursor()
    cursor.execute('DELETE FROM url_entries WHERE identifier = ?', (identifier,))
    dbconn.commit()


def update_url(dbconn, identifier: str, new_url: str):
    """Update an entry."""
    cursor = dbconn.cursor()
    cursor.execute('UPDATE url_entries SET forward_to = ? WHERE identifier = ?',
                   (new_url, identifier))
    dbconn.commit()


def get_entry(dbconn, identifier: str) -> str:
    """Retrieve an entry as dict."""
    cursor = dbconn.cursor()
    cursor.execute('SELECT * FROM url_entries WHERE identifier=?', (identifier,))
    raw = cursor.fetchone()
    if raw:
        data = dict(zip(('identifier', 'forward_to', 'token'), raw))
    else:
        data = None
    return data


def get_url(dbconn, identifier: str) -> str:
    """Get forward URL for an entry."""
    cursor = dbconn.cursor()
    cursor.execute('SELECT forward_to FROM url_entries WHERE identifier=?', (identifier,))
    data = cursor.fetchone()
    if data:
        data = data[0]
    return data


def add_url(dbconn, identifier: str, new_url: str) -> str:
    """Add an entry."""
    token = secrets.token_urlsafe(64)
    cursor = dbconn.cursor()
    cursor.execute('INSERT INTO url_entries VALUES (?, ?, ?)', (identifier, new_url, token))
    dbconn.commit()
    return token


def get_all(dbconn):
    """Get a list with all (identifier, forward_url) pairs."""
    cursor = dbconn.cursor()
    cursor.execute('SELECT identifier, forward_to FROM url_entries ORDER BY identifier')
    data = cursor.fetchall()
    return data
