
import psycopg2
import os

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) NOT NULL,
            text TEXT NOT NULL
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (note_id, tag_id)
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def get_or_create_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    if user:
        user_db_id = user[0]
    else:
        cur.execute("INSERT INTO users (user_id) VALUES (%s) RETURNING id", (user_id,))
        user_db_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    conn.close()
    return user_db_id

def get_notes(user_db_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM notes WHERE user_id = %s", (user_db_id,))
    notes = cur.fetchall()
    
    notes_with_tags = []
    for note in notes:
        note_id, note_text = note
        cur.execute('''
            SELECT t.name FROM tags t
            JOIN note_tags nt ON t.id = nt.tag_id
            WHERE nt.note_id = %s
        ''', (note_id,))
        tags = [row[0] for row in cur.fetchall()]
        notes_with_tags.append({"id": note_id, "text": note_text, "tags": tags})
        
    cur.close()
    conn.close()
    return notes_with_tags

def add_note(user_db_id: int, note_text: str, tags: list[str]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s) RETURNING id", (user_db_id, note_text))
    note_id = cur.fetchone()[0]
    
    for tag_name in tags:
        cur.execute("INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (tag_name,))
        cur.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
        tag_id = cur.fetchone()[0]
        cur.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (%s, %s)", (note_id, tag_id))
    
    conn.commit()
    cur.close()
    conn.close()

def delete_note(note_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    conn.commit()
    cur.close()
    conn.close()

def edit_note(note_id: int, new_text: str, tags: list[str]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET text = %s WHERE id = %s", (new_text, note_id))
    
    cur.execute("DELETE FROM note_tags WHERE note_id = %s", (note_id,))
    
    for tag_.pyname in tags:
        cur.execute("INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (tag_name,))
        cur.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
        tag_id = cur.fetchone()[0]
        cur.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (%s, %s)", (note_id, tag_id))
        
    conn.commit()
    cur.close()
    conn.close()

def find_notes_by_tag(user_db_id: int, tag_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT n.id, n.text FROM notes n
        JOIN note_tags nt ON n.id = nt.note_id
        JOIN tags t ON nt.tag_id = t.id
        WHERE n.user_id = %s AND t.name = %s
    ''', (user_db_id, tag_name))
    notes = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": note[0], "text": note[1]} for note in notes]
