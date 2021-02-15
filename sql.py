import secrets

def init(dbconn):
    cursor = dbconn.cursor()
    cursor.execute('CREATE TABLE url_entries '                 
                   '(identifier TEXT PRIMARY KEY, forward_to TEXT, update_token TEXT)')


def update_url(dbconn, identifier: str, new_url: str):
    cursor = dbconn.cursor()
    cursor.execute('UPDATE url_entries SET forward_to = ? WHERE identifier = ?',
                   (new_url, identifier))
    dbconn.commit()


def get_entry(dbconn, identifier: str) -> str:
    cursor = dbconn.cursor()
    cursor.execute('SELECT * FROM url_entries WHERE identifier=?', (identifier,))
    data = dict(zip(('identifier', 'forward_to', 'token'), cursor.fetchone()))
    return data


def get_url(dbconn, identifier: str) -> str:
    cursor = dbconn.cursor()
    cursor.execute('SELECT forward_to FROM url_entries WHERE identifier=?', (identifier,))
    data = cursor.fetchone()[0]
    return data


def add_url(dbconn, identifier: str, new_url: str) -> str:
    token = secrets.token_urlsafe(128)
    cursor = dbconn.cursor()
    cursor.execute('INSERT INTO url_entries VALUES (?, ?, ?)', (identifier, new_url, token))
    dbconn.commit()
    return token


def get_all(dbconn):
    cursor = dbconn.cursor()
    cursor.execute('SELECT identifier, forward_to FROM url_entries ORDER BY identifier')
    data = cursor.fetchall()
    return data
