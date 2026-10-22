"""Python 3.12+ Telegram learning bot; standard library only."""
import json
import logging
import os
from pathlib import Path
import random
import signal
import sqlite3
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from content import NAME, ABOUT, WELCOME, BUTTONS, WORDS

LOG = logging.getLogger('sbkh')
STOP = threading.Event()
MENU = {'keyboard': [[{'text': b}] for b in BUTTONS], 'resize_keyboard': True}

class APIError(Exception):
    def __init__(self, code, retry=3):
        self.code, self.retry = code, retry
        super().__init__(f'Telegram API error {code}')

class Telegram:
    def __init__(self, token):
        self.base = f'https://api.telegram.org/bot{token}/'

    def call(self, method, **params):
        request = Request(self.base + method, data=json.dumps(params).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=40) as response:
                data = json.load(response)
        except HTTPError as error:
            try:
                data = json.load(error)
            except (ValueError, OSError):
                raise APIError(error.code) from None
        except (URLError, TimeoutError, OSError):
            raise APIError(503) from None  # Never expose token-bearing URLs in logs.
        if not data.get('ok'):
            raise APIError(data.get('error_code', 500), data.get('parameters', {}).get('retry_after', 3))
        return data['result']

class Bot:
    def __init__(self, api, path):
        self.api = api
        if path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS lessons (uid INTEGER, day TEXT, PRIMARY KEY(uid, day));
        CREATE TABLE IF NOT EXISTS quizzes (id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, word INTEGER,
          options TEXT, answer INTEGER, selected INTEGER);
        CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value INTEGER);
        ''')

    def today(self):
        return datetime.now(ZoneInfo('Asia/Phnom_Penh')).date()

    def send(self, uid, text, markup=MENU):
        return self.api.call('sendMessage', chat_id=uid, text=text, reply_markup=markup)

    def lesson(self, uid):
        day = self.today()
        start = (day.toordinal() % 7) * 5
        text = '📚 ពាក្យប្រចាំថ្ងៃ — ' + str(day) + '\n\n'
        text += '\n\n'.join(f'{i+1}. {en} — {kh}\nឧទាហរណ៍: {ex}'
                             for i, (en, kh, ex) in enumerate(WORDS[start:start+5]))
        text += '\n\nសូមអានពាក្យទាំងនេះ រួចសាកល្បងសំណួរខ្លីៗ។'
        self.send(uid, text)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO lessons VALUES (?, ?)', (uid, str(day)))

    def quiz(self, uid):
        word = random.randrange(len(WORDS))
        options = random.sample([i for i in range(len(WORDS)) if i != word], 2) + [word]
        random.shuffle(options)
        with self.db:
            self.db.execute('DELETE FROM quizzes WHERE uid=? AND selected IS NULL', (uid,))
            cur = self.db.execute('INSERT INTO quizzes(uid,word,options,answer) VALUES (?,?,?,?)',
                                  (uid, word, json.dumps(options), options.index(word)))
        markup = {'inline_keyboard': [[{'text': WORDS[w][1], 'callback_data': f'q:{cur.lastrowid}:{i}'}]
                                      for i, w in enumerate(options)]}
        self.send(uid, f'📝 តើពាក្យ «{WORDS[word][0]}» មានន័យថាអ្វី?', markup)

    def answer(self, callback):
        uid = callback['from']['id']
        message = callback.get('message', {})
        if message.get('chat', {}).get('type') != 'private':
            self.api.call('answerCallbackQuery', callback_query_id=callback['id'])
            return
        try:
            prefix, qid, selected = callback.get('data', '').split(':')
            qid, selected = int(qid), int(selected)
            if prefix != 'q' or selected not in range(3):
                raise ValueError
        except ValueError:
            self.api.call('answerCallbackQuery', callback_query_id=callback['id'])
            return
        row = self.db.execute('SELECT word,answer,selected FROM quizzes WHERE id=? AND uid=?', (qid, uid)).fetchone()
        if not row or row[2] is not None:
            self.api.call('answerCallbackQuery', callback_query_id=callback['id'],
                          text='សូមចាប់ផ្តើមសំណួរថ្មី។')
            return
        word, correct, _ = row
        with self.db:
            self.db.execute('UPDATE quizzes SET selected=? WHERE id=? AND selected IS NULL', (selected, qid))
        self.api.call('answerCallbackQuery', callback_query_id=callback['id'],
                      text='ត្រឹមត្រូវ!' if selected == correct else 'មិនទាន់ត្រឹមត្រូវទេ។')
        en, kh, example = WORDS[word]
        feedback = ('✅ ត្រឹមត្រូវ!' if selected == correct else '❌ មិនទាន់ត្រឹមត្រូវទេ។')
        self.send(uid, f'{feedback}\n{en} មានន័យថា «{kh}»។\nឧទាហរណ៍: {example}\n\nចុចសំណួរខ្លីៗ ដើម្បីបន្ត។')

    def progress(self, uid):
        days = {r[0] for r in self.db.execute('SELECT day FROM lessons WHERE uid=?', (uid,))}
        date, streak = self.today(), 0
        if str(date) not in days:
            date -= timedelta(days=1)
        while str(date) in days:
            streak += 1
            date -= timedelta(days=1)
        total, correct = self.db.execute('SELECT COUNT(*), COALESCE(SUM(selected=answer),0) FROM quizzes WHERE uid=? AND selected IS NOT NULL', (uid,)).fetchone()
        self.send(uid, f'📈 វឌ្ឍនភាពរបស់ខ្ញុំ\n\nថ្ងៃដែលបានអានមេរៀន: {len(days)}\nរៀនជាប់គ្នា: {streak} ថ្ងៃ\nសំណួរដែលបានឆ្លើយ: {total}\nចម្លើយត្រឹមត្រូវ: {correct}/{total}\nពិន្ទុ: {round(100*correct/total) if total else 0}%')

    def handle(self, update):
        if 'callback_query' in update:
            return self.answer(update['callback_query'])
        message = update.get('message', {})
        chat = message.get('chat', {})
        if not chat or message.get('from', {}).get('is_bot'):
            return
        uid = chat['id']
        if chat.get('type') != 'private':
            return self.send(uid, 'សូមបើកការជជែកឯកជនជាមួយ bot ដើម្បីរៀន។', {'remove_keyboard': True})
        text = message.get('text', '')
        command = text.split()[0].split('@')[0] if text else ''
        if command in ('/start', '/help', '/menu'):
            self.send(uid, WELCOME)
        elif text == BUTTONS[0] or command == '/words':
            self.lesson(uid)
        elif text == BUTTONS[1] or command == '/quiz':
            self.quiz(uid)
        elif text == BUTTONS[2] or command == '/progress':
            self.progress(uid)
        elif command == '/privacy':
            self.send(uid, 'យើងរក្សាទុកលេខសម្គាល់ Telegram ថ្ងៃរៀន និងលទ្ធផលសំណួរ ដើម្បីបង្ហាញវឌ្ឍនភាព។ យើងមិនរក្សាទុកឈ្មោះ លេខទូរស័ព្ទ ឬសាររបស់អ្នកទេ។ ប្រើ /delete_data ដើម្បីលុបទិន្នន័យ។')
        elif command == '/delete_data':
            with self.db:
                for table in ('lessons', 'quizzes'):
                    self.db.execute(f'DELETE FROM {table} WHERE uid=?', (uid,))
            self.send(uid, 'ទិន្នន័យវឌ្ឍនភាពរបស់អ្នកត្រូវបានលុបហើយ។')
        else:
            self.send(uid, 'សូមជ្រើសរើសប៊ូតុងមួយខាងក្រោម ឬប្រើ /help។')

    def run(self):
        row = self.db.execute("SELECT value FROM state WHERE key='offset'").fetchone()
        offset = row[0] if row else 0
        while not STOP.is_set():
            try:
                updates = self.api.call('getUpdates', offset=offset, timeout=25,
                                        allowed_updates=['message', 'callback_query'])
                for update in updates:
                    if STOP.is_set():
                        break
                    try:
                        self.handle(update)
                    except APIError as error:
                        if error.code not in (400, 403):
                            raise
                        LOG.warning('Cannot reply to update %s: code %s', update['update_id'], error.code)
                    offset = update['update_id'] + 1
                    with self.db:
                        self.db.execute("INSERT OR REPLACE INTO state VALUES ('offset',?)", (offset,))
            except APIError as error:
                if error.code in (401, 409):
                    raise SystemExit('Invalid token or another polling instance/webhook is active.') from None
                LOG.warning('Temporary Telegram failure: %s', error.code)
                STOP.wait(min(max(error.retry, 3), 60))


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    token = os.environ.get('BOT_TOKEN', '').strip()
    if not token:
        raise SystemExit('Set BOT_TOKEN in your hosting environment before starting.')
    api = Telegram(token)
    bot = Bot(api, os.environ.get('DATABASE_PATH', 'data/sbkh.sqlite3'))
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: STOP.set())
    try:
        api.call('getMe')
        if api.call('getWebhookInfo').get('url'):
            raise SystemExit('An existing webhook is active. Remove it before enabling polling.')
        api.call('setMyName', name=NAME)
        api.call('setMyDescription', description=WELCOME)
        api.call('setMyShortDescription', short_description=ABOUT)
        api.call('setMyCommands', commands=[{'command': c, 'description': d} for c, d in [
            ('start', 'បើកម៉ឺនុយ'), ('words', 'ពាក្យប្រចាំថ្ងៃ'), ('quiz', 'សំណួរខ្លីៗ'),
            ('progress', 'វឌ្ឍនភាពរបស់ខ្ញុំ'), ('help', 'ជំនួយ'),
            ('privacy', 'ឯកជនភាព'), ('delete_data', 'លុបទិន្នន័យរបស់ខ្ញុំ')]])
        LOG.info('SB24GZ KH is running')
        bot.run()
    except APIError as error:
        raise SystemExit(f'Telegram setup failed (code {error.code}). Check token and connectivity.') from None
    finally:
        bot.db.close()

if __name__ == '__main__':
    main()
