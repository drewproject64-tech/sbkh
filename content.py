NAME = 'SB24GZ KH — រៀនភាសាអង់គ្លេស'
ABOUT = 'រៀនពាក្យអង់គ្លេស ឆ្លើយសំណួរខ្លីៗ និងតាមដានវឌ្ឍនភាពជាភាសាខ្មែរ។'
WELCOME = ('សូមស្វាគមន៍មកកាន់ SB24GZ KH!\nរៀនពាក្យអង់គ្លេស ៥ ពាក្យក្នុងមួយថ្ងៃ ជាមួយការបកប្រែជាភាសាខ្មែរ និងប្រយោគឧទាហរណ៍។ ឆ្លើយសំណួរខ្លីៗ និងតាមដានវឌ្ឍនភាពរបស់អ្នក។\nសូមជ្រើសរើសប៊ូតុងខាងក្រោម។')
BUTTONS = ['📚 ពាក្យប្រចាំថ្ងៃ', '📝 សំណួរខ្លីៗ', '📈 វឌ្ឍនភាពរបស់ខ្ញុំ']
# Seven rotating lessons; five words each. All learning content stays inside Telegram.
RAW = '''hello|សួស្តី|Hello, my friend!
thanks|អរគុណ|Thanks for your help.
please|សូម|Please sit down.
yes|បាទ / ចាស|Yes, I understand.
no|ទេ|No, thank you.
water|ទឹក|I drink water.
rice|បាយ|I eat rice.
bread|នំប៉័ង|This bread is fresh.
milk|ទឹកដោះគោ|I drink milk.
fruit|ផ្លែឈើ|I like fruit.
book|សៀវភៅ|I read a book.
pen|ប៊ិច|This is my pen.
school|សាលារៀន|I go to school.
teacher|គ្រូបង្រៀន|My teacher is kind.
student|សិស្ស|She is a student.
house|ផ្ទះ|This is my house.
door|ទ្វារ|Please open the door.
window|បង្អួច|The window is open.
chair|កៅអី|Sit on the chair.
table|តុ|The book is on the table.
sun|ព្រះអាទិត្យ|The sun is bright.
moon|ព្រះចន្ទ|I can see the moon.
rain|ភ្លៀង|The rain is heavy.
tree|ដើមឈើ|That tree is tall.
flower|ផ្កា|This flower is beautiful.
read|អាន|I read every day.
write|សរសេរ|Please write your name.
speak|និយាយ|I speak English.
listen|ស្តាប់|Listen to the teacher.
learn|រៀន|We learn together.
happy|សប្បាយចិត្ត|I am happy today.
big|ធំ|This house is big.
small|តូច|My bag is small.
new|ថ្មី|This is a new book.
good|ល្អ|Have a good day!'''
WORDS = [tuple(line.split('|')) for line in RAW.splitlines()]
