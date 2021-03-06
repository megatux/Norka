# storage.py
#
# MIT License
#
# Copyright (c) 2020 Andrey Maksimov <meamka@ya.ru>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import sqlite3

from gi.repository import GLib

from norka.define import APP_TITLE
from norka.models.document import Document
from norka.services.logger import Logger


class Storage(object):
    def __init__(self):
        self.base_path = os.path.join(GLib.get_user_data_dir(), APP_TITLE)
        self.file_path = os.path.join(self.base_path, 'storage.db')
        self.conn = None

    def init(self):
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)
            Logger.info('Storage folder created at %s', self.base_path)

        Logger.info(f'Storage located at %s', self.file_path)

        self.conn = sqlite3.connect(self.file_path)

        self.conn.execute("""
                CREATE TABLE IF NOT EXISTS `documents` (
                    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                    `title` TEXT NOT NULL,
                    `content` TEXT,
                    `archived` INTEGER NOT NULL DEFAULT 0 
                )
            """)

    def count(self, with_archived: bool = False) -> int:
        query = 'SELECT COUNT (1) AS count FROM documents'
        if not with_archived:
            query += " WHERE archived=0"
        cursor = self.conn.cursor().execute(query)
        row = cursor.fetchone()
        return row[0]

    def add(self, document: Document) -> int:
        cursor = self.conn.cursor().execute("INSERT INTO documents(title, content, archived) VALUES (?, ?, ?)",
                                            (document.title, document.content, document.archived,), )
        self.conn.commit()
        return cursor.lastrowid

    def all(self, with_archived: bool = False) -> list:
        query = "SELECT * FROM documents"
        if not with_archived:
            query += " WHERE archived=0"

        cursor = self.conn.cursor().execute(query)
        rows = cursor.fetchall()

        docs = []
        for row in rows:
            docs.append(Document.new_with_row(row))

        return docs

    def get(self, doc_id: int) -> Document:
        query = "SELECT * FROM documents WHERE id=?"
        cursor = self.conn.cursor().execute(query, (doc_id,))
        row = cursor.fetchone()

        return Document.new_with_row(row)

    def save(self, document: Document) -> bool:
        query = "UPDATE documents SET title=?, content=?, archived=? WHERE id=?"

        try:
            self.conn.execute(query, (document.title, document.content, document.archived,))
            self.conn.commit()
        except Exception as e:
            Logger.error(e)
            return False

        return True

    def update(self, doc_id: int, data: dict) -> bool:
        fields = {field: value for field, value in data.items()}

        query = f"UPDATE documents SET {','.join(f'{key}=?' for key in fields.keys())} WHERE id=?"

        try:
            self.conn.execute(query, tuple(fields.values()) + (doc_id,))
            self.conn.commit()
        except Exception as e:
            Logger.error(e)
            return False

        return True

    def delete(self, doc_id: int) -> bool:
        query = f"DELETE FROM documents WHERE id=?"

        try:
            self.conn.execute(query, (doc_id,))
            self.conn.commit()
        except Exception as e:
            Logger.error(e)
            return False

        return True

    def find(self, search_text: str) -> list:
        query = f"SELECT * FROM documents WHERE lower(title) LIKE ? ORDER BY archived ASC"

        cursor = self.conn.cursor().execute(query, (f'%{search_text.lower()}%',))
        rows = cursor.fetchall()

        docs = []
        for row in rows:
            docs.append(Document.new_with_row(row))

        return docs


storage = Storage()
