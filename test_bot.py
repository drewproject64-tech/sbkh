import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from bot import Bot, MENU
from content import BUTTONS, WORDS, NAME, ABOUT, WELCOME

class FakeAPI:
    def __init__(self): self.calls = []
    def call(self, method, **params):
        self.calls.append((method, params))
        return {'message_id': len(self.calls)}

class BotTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.bot = Bot(self.api, ':memory:')
        self.bot.today = lambda: date(2026, 10, 22)
    def tearDown(self): self.bot.db.close()
    def message(self, text=None):
        self.bot.handle({'message': {'chat': {'id': 42, 'type': 'private'}, 'from': {'id': 42}, 'text': text}})
    def test_menu_and_fallback(self):
        for text in ['/start', '/help', 'hello', None]:
            self.message(text)
            self.assertEqual(self.api.calls[-1][1]['reply_markup'], MENU)
        self.assertEqual(len(MENU['keyboard']), 3)
    def test_daily_lesson_deduplication_and_rotation(self):
        self.message('/words'); first = self.api.calls[-1][1]['text']
        self.message(BUTTONS[0])
        self.assertEqual(self.bot.db.execute('SELECT COUNT(*) FROM lessons').fetchone()[0], 1)
        self.bot.today = lambda: date(2026, 10, 23)
        self.message('/words')
        self.assertNotEqual(first, self.api.calls[-1][1]['text'])
        self.message('/progress')
        self.assertIn('2 ថ្ងៃ', self.api.calls[-1][1]['text'])
    def callback(self, qid, selected, uid=42):
        self.bot.handle({'callback_query': {'id': 'test', 'from': {'id': uid},
            'message': {'chat': {'id': uid, 'type': 'private'}}, 'data': f'q:{qid}:{selected}'}})
    def test_quiz_owner_replay_and_score(self):
        self.message('/quiz')
        qid, answer = self.bot.db.execute('SELECT id,answer FROM quizzes').fetchone()
        self.callback(qid, answer, 99)
        self.assertIsNone(self.bot.db.execute('SELECT selected FROM quizzes').fetchone()[0])
        self.callback(qid, answer); self.callback(qid, answer)
        self.message('/progress')
        self.assertIn('100%', self.api.calls[-1][1]['text'])
        self.assertIn('1/1', self.api.calls[-1][1]['text'])
    def test_wrong_answer_stale_quiz_and_delete(self):
        self.message('/quiz')
        old = self.bot.db.execute('SELECT id FROM quizzes').fetchone()[0]
        self.message('/quiz')
        qid, answer = self.bot.db.execute('SELECT id,answer FROM quizzes').fetchone()
        self.assertNotEqual(old, qid)
        self.callback(old, answer)
        self.assertIsNone(self.bot.db.execute('SELECT selected FROM quizzes').fetchone()[0])
        self.callback(qid, (answer+1)%3)
        self.message('/progress'); self.assertIn('0/1', self.api.calls[-1][1]['text'])
        self.message('/words'); self.message('/delete_data')
        for table in ('lessons', 'quizzes'):
            self.assertEqual(self.bot.db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory)/'db.sqlite')
            first = Bot(self.api, path); first.lesson(42); first.db.close()
            second = Bot(self.api, path)
            self.assertEqual(second.db.execute('SELECT COUNT(*) FROM lessons').fetchone()[0], 1)
            second.db.close()
    def test_content(self):
        self.assertEqual(len(WORDS), 35)
        self.assertEqual(len({w[1] for w in WORDS}), 35)
        self.assertLessEqual(len(NAME), 64)
        self.assertLessEqual(len(ABOUT), 120)
        self.assertLessEqual(len(WELCOME), 512)

if __name__ == '__main__': unittest.main()
