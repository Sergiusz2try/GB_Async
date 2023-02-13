# Задание 1
import subprocess

words = ["Разработка", "Сокет", "Декоратор"]

for word in words:
    print(f"Type: {type(word)}, word: {word}")

words_unicode = [
    "\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430",
    "\u0441\u043e\u043a\u0435\u0442",
    "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"
]

for word in words_unicode:
    print(f"Type: {type(word)}, word: {word}")

# Задание 2

words_2 = [b'class', b'function', b'method']

for word in words_2:
    print(f"Type: {type(word)}, word: {word}, length: {len(word)}")

# Задание 3

# words_3 = [b'attribute', b'класс', b'функция', b'type']
# Слова класс и функция нельзя записать в айтовом типе, так как русские символы не входят в ASCII

# Задание 4

words_4 = ["разработка", "администрирование", "protocol", "standard"]

for word in words_4:
    word_enc = word.encode("utf-8")
    print(word_enc)
    print(word_enc.decode("utf-8"))

# Задание 5

# hosts = ["yandex.ru", "youtube.com"]
#
# for host in hosts:
#     ping = subprocess.Popen(
#         ["ping", "-c", "4", host],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE
#     )
#     out, err = ping.communicate()
#     print(out.decode("utf-8"))

# Задание 6

with open("test_file.txt", "r") as file:
    print(file.encoding)

with open("test_file.txt", "r", encoding="utf-8") as file:
    print(file.read())
