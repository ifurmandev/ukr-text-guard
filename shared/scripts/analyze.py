#!/usr/bin/env python3
"""
Статистичний аналізатор українського тексту на ознаки ШІ-письма.

Використання:
    python3 analyze.py файл.txt|.md|.html|.docx [--json]
    python3 analyze.py - < текст.txt

Індекс 0–100 — евристична підказка, а не доказ авторства.
Лише стандартна бібліотека; для .docx бажано встановити python-docx,
інакше текст дістається напряму з XML.
"""
import html
import json
import re
import statistics
import sys
import zipfile
from collections import Counter
from html.parser import HTMLParser

# ---------------------------------------------------------------- читання


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
             "section", "article", "tr", "blockquote"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    low = path.lower()
    if low.endswith(".docx"):
        try:
            import docx  # type: ignore
            return "\n\n".join(p.text for p in docx.Document(path).paragraphs)
        except ImportError:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8")
            xml = re.sub(r"</w:p>", "\n\n", xml)
            return html.unescape(re.sub(r"<[^>]+>", "", xml))
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    if low.endswith((".html", ".htm")) or raw.lstrip().startswith("<"):
        p = _TextExtractor()
        p.feed(raw)
        return html.unescape("".join(p.parts))
    return raw


# ---------------------------------------------------------------- словники

APOS = "'’ʼ`"
WORD_RE = re.compile(r"[A-Za-zА-ЩЬЮЯЄІЇҐа-щьюяєіїґ0-9'’ʼ-]+")

CLICHES = [  # (регулярка, вага, підказка)
    (r"варто (за|від)значити|варто підкреслити|варто наголосити", 3, "викреслити, одразу суть"),
    (r"важливо (за|від)значити|важливо підкреслити|важливо пам.ятати|важливо розуміти", 3, "викреслити"),
    (r"слід (за|від)значити|слід підкреслити|необхідно (за|від)значити|необхідно наголосити", 3, "викреслити"),
    (r"не можна не (згадати|відзначити|зазначити)", 3, "викреслити"),
    (r"[ув] сучасному світі|[ув] сучасних реаліях|[ув] наш час|в епоху (цифров|інформац|технолог)", 3, "конкретний час/місце"),
    (r"відігра[єю]т?ь? (ключову|важливу|вирішальну|значну|провідну|центральну) роль", 3, "від чого залежить…"),
    (r"відкрива[єю]т?ь? (нові|широкі) (можливості|горизонти|перспективи)", 3, "назвати, що саме дає"),
    (r"широкий спектр|широкого спектр", 2, "перелічити конкретне"),
    (r"комплексн\w+ підх[іо]д|індивідуальн\w+ підх[іо]д", 2, "описати дії"),
    (r"інноваційн\w+ (рішен|підх|технол)", 2, "що нового і для кого"),
    (r"найвищ\w+ стандарт|бездоганн\w+ якіст", 2, "факт замість оцінки"),
    (r"невід.ємн\w+ частин", 2, "без чого не буває…"),
    (r"ключ до успіху|справжній прорив|незамінн\w+ помічник|надійн\w+ партнер", 2, "конкретика"),
    (r"зануримося|давайте розберемося|давайте розглянемо|давайте поговоримо", 3, "почати зі змісту"),
    (r"[ув] цій статті ми|[ув] цьому матеріалі ми|у цьому тексті ми", 3, "почати з гачка"),
    (r"(^|[.!?]\s+)таким чином", 2, "тож / зрештою / без маркера"),
    (r"підсумовуючи|у підсумку можна|отже, можна (сказати|зробити висновок)|на завершення варто", 3, "висновок без маркера"),
    (r"сподіваюся, це (допоможе|було корисно)|чудове питання|звертайтеся, якщо у вас", 3, "залишок чату — викреслити"),
    (r"це не просто [^.!?]{1,60}(—|–|-) це", 3, "сказати прямо"),
    (r"як ніколи раніше|стрімко розвива|стрімкий розвиток|цифров\w+ трансформаці", 2, "конкретика"),
    (r"на сьогоднішній день|з огляду на вищезазначене|з метою покращення", 1, "сьогодні / тому / щоб поліпшити"),
    (r"має безліч переваг|має низку переваг|ряд переваг", 2, "назвати переваги"),
    (r"(за|на)значимо, що|наголосимо, що|як відомо,|загальновідомо|не секрет, що|очевидно, що", 2, "викреслити вступ"),
    (r"слід звернути увагу|варто врахувати|важливо враховувати|варто пам.ятати", 2, "викреслити"),
    (r"як (за|від)значалося вище|як (уже|вже) (за|від)значалося|як було сказано", 2, "повтор структури"),
    (r"з одного боку|з іншого боку|у той час як|тим не менш|в цілому|у цілому|загалом кажучи|по суті", 1, "спростити зв'язку"),
    (r"по-перше[\s\S]{0,400}по-друге[\s\S]{0,400}по-третє", 2, "шаблонна нумерація аргументів"),
    (r"ключов(і|их) переваг|основн(і|их) переваг|переваги та недоліки|плюси та мінуси", 2, "структура-шаблон"),
    (r"часті запитання|часті питання|поширені запитання", 1, "шаблонний FAQ-блок (перевірити зміст)"),
    (r"дозволя[єю]т?ь? (значно|суттєво|істотно) (підвищити|покращити|поліпшити|скоротити|зменшити)", 2, "цифра замість «значно»"),
    (r"забезпечу[єю]т?ь? (високу|максимальну|надійну|повну)", 2, "факт замість обіцянки"),
    (r"першим і найважливішим кроком|першим кроком є|наступним кроком є|завершальним етапом є", 2, "шаблон переліку етапів"),
    (r"системний процес|галузев\w+ стандарт|різнопрофільн\w+ фахівц|вимагає чіткої", 1, "загальник"),
    (r"незалежно від (типу|виду|розміру|масштабу)", 1, "загальник"),
    (r"високотехнологічн\w+|високоефективн\w+|високоякісн\w+|високоміцн\w+", 1, "епітет без цифри — дати показник"),
    (r"нового покоління|ідеально підходить|незамінн\w+ (у|в|для)|преміальн\w+|найсуворіш\w+ вимог", 2, "рекламний штамп — замінити фактом"),
    (r"лідер (з|у|на) (виробництв|ринк)|номер один|№ ?1 (в|на)", 2, "неперевірне твердження"),
]

CHAT_RESIDUE = [
    r"як (мовна модель|штучний інтелект|ШІ-помічник|ai-помічник)", r"станом на (мою|мій) (базу|дату|знання)",
    r"я не маю доступу до", r"\[(вставте|вставити|назва компанії|ваше ім.я|ім.я|дата|місто|ваш[ае]? )[^\]]{0,40}\]",
    r"lorem ipsum", r"\{\{[^}]+\}\}", r"ось (оновлений|переписаний|виправлений) (текст|варіант)",
    r"звичайно! ось", r"звісно! ось", r"нижче наведено", r"ось кілька (варіантів|ідей)",
]

CALQUES = [
    (r"\bявля(ється|ються|ється|ючись|вся|лася|лись)\b|\bявляє собою\b", "є, становить"),
    (r"\bпри(йма|йня|йняв|йнял)\w* участ", "брати участь"),
    (r"\bна протязі\b", "протягом, упродовж"),
    (r"\bв якості\b|\bу якості\b(?! (продукц|товар|послуг))", "як"),
    (r"\bслідуюч\w+", "наступний"),
    (r"\bспівпада\w*|\bспівпав\w*", "збігатися"),
    (r"\bна даний (момент|час)\b", "наразі"),
    (r"\bдан(ий|ого|ому|им|ій|ої|ою|а|е)\b(?! (закон|статт))", "цей"),
    (r"\bміроприємств\w*", "захід"),
    (r"\bпо (питанню|питаннях|темі)\b", "з питання, на тему"),
    (r"\bсам(ий|а|е|і) (кращ|гірш|більш|менш|перш)", "най-"),
    (r"\bприходиться\b", "доводиться"),
    (r"\bу випадку,? якщо\b|\bв випадку,? якщо\b", "якщо, у разі"),
    (r"\bвідноси(ться|ться|ться|ться|ться)\b до", "стосується, належить до"),
    (r"\bприйня\w* міри\b|\bприйма\w* міри\b", "вжити заходів"),
    (r"\bзгідно (?!з\b|із\b)\w+", "згідно з / відповідно до"),
    (r"\bбільше (ста|сотні|тисячі|мільйона)\b", "понад"),
    (r"\bгра[єю]т?ь? (важливу |ключову |значну )?роль\b", "відіграє роль / важить"),
    (r"\bадресува\w+ (проблем|питан)", "розв'язати, взятися за"),
    (r"\bв кінці дня\b", "зрештою"),
    (r"\bбути в змозі\b|\bв змозі\b", "могти, змогти"),
    (r"\bрахую, що\b|\bрахує, що\b|\bрахуємо, що\b", "вважати"),
    (r"\bперш за все\b", "насамперед, передусім"),
    (r"\bу порівнянні з\b|\bв порівнянні з\b", "порівняно з"),
    (r"\bз точки зору\b", "з погляду"),
    (r"\bбільш(е)? ніж\b(?= \d)", "понад"),
    (r"\bдля того,? щоб\b", "щоб (якщо без наголосу)"),
    (r"\bне дивлячись на\b", "незважаючи на, попри"),
    (r"\bв (значній|великій) мірі\b|\bв певній мірі\b", "значною мірою, певною мірою"),
    (r"\bзаймати (місце|позицію)\b", "посідати місце"),
    (r"\bстановити (інтерес|небезпеку)\b", "бути цікавим / бути небезпечним"),
    (r"\bносити (характер|назву)\b", "мати характер / називатися"),
]

PARTICIPLE_OK = {
    "блискучий", "колючий", "родючий", "співучий", "квітучий", "плакучий", "живучий",
    "гарячий", "сидячий", "лежачий", "стоячий", "ходячий", "тямущий", "невмирущий",
    "їдучий", "смердючий", "тягучий", "балакучий", "рухучий", "пекучий", "жгучий",
    "дрімучий", "могутній", "летючий", "линючий", "в'юнкий", "повзучий", "кипучий",
    "падучий", "лякучий", "в’язкий", "працюючий",  # «працюючий» — калька, але часто в тех. текстах; не штрафуємо
}
NOUN_ACH = re.compile(r"^(користувач|викладач|читач|глядач|слухач|перекладач|оглядач|споживач|доповідач|отримувач|одержувач|наглядач|розповідач|відвідувач|завідувач|укладач|дослідувач|багач|силач|орач|ткач|сіяч|копач|стукач)")
PARTICIPLE_RE = re.compile(r"\b\w{2,}(уч|юч|ач|яч)(ий|а|е|і|ого|ому|им|их|ими|ої|ій|у|ою)\b")

DIEPR_RE = re.compile(r"\b\w{2,}(учи|ючи|ачи|ячи|вши|ши)(сь)?\b")
DIEPR_EXCL = re.compile(r"(пиши|лиши|души|ліши|виши|миши|кіши)(сь)?$")

SUBORD = re.compile(
    r"(,|^)\s*(що|який|яка|яке|які|якого|якої|якому|яким|якій|яких|коли|бо|щоб|аби|якщо|якби|"
    r"хоча|хоч|оскільки|тому що|через те що|де|куди|звідки|поки|доки|ніби|наче|мов|мовби|"
    r"відколи|як тільки|дарма що|незважаючи на те|так що|чим)\b")
COORD = re.compile(r",\s*(і|й|та|а|але|проте|зате|однак|або|чи|то|втім)\s")
DETACHED = re.compile(r"\b(незважаючи на|попри|всупереч|завдяки|внаслідок|з огляду на|у разі|на відміну від)\b")

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2705]")


# ---------------------------------------------------------------- розбір

ZW_RE = re.compile("[\u200b-\u200f\u2060\u2061\u2062\u2063\ufeff\u00ad\u034f]")
HOMO = str.maketrans({"a": "а", "e": "е", "o": "о", "i": "і", "c": "с", "p": "р", "x": "х", "y": "у",
                      "A": "А", "E": "Е", "O": "О", "I": "І", "C": "С", "P": "Р", "X": "Х", "H": "Н",
                      "K": "К", "M": "М", "T": "Т", "B": "В", "k": "к"})
CYR = re.compile("[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]")
LAT = re.compile("[A-Za-z]")
OBF = {"zero_width": 0, "mixed_words": []}


def norm(t):
    """Прибирає невидимі символи, зводить апострофи, лікує латинські двійники.
    Усе знайдене фіксує в OBF — приховування тексту від аналізу саме по собі є червоним прапорцем."""
    zw = len(ZW_RE.findall(t))
    OBF["zero_width"] += zw
    t = ZW_RE.sub("", t)
    for a in APOS:
        t = t.replace(a, "'")

    def fix(m):
        w = m.group(0)
        if CYR.search(w) and LAT.search(w):
            OBF["mixed_words"].append(w)
            return w.translate(HOMO)
        return w
    return re.sub(r"[A-Za-zА-ЩЬЮЯЄІЇҐа-щьюяєіїґ0-9']+", fix, t)


def split_paragraphs(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) <= 1:
        paras = [p.strip() for p in text.split("\n") if p.strip()]
    return paras


ABBR = re.compile(r"\b(т\.\s?д|т\.\s?п|т\.\s?ч|р|рр|ст|м|вул|див|напр|грн|тис|млн|млрд|с|п|пп|ім|проф|д-р)\.", re.I)


def split_sentences(para):
    safe = ABBR.sub(lambda m: m.group(0).replace(".", "§"), para)
    parts = re.split(r"(?<=[.!?…])\s+(?=[«\"(A-ZА-ЩЬЮЯЄІЇҐ0-9—–-])", safe)
    return [p.replace("§", ".").strip() for p in parts if WORD_RE.search(p)]


def words(t):
    return [w.lower().strip("-'") for w in WORD_RE.findall(norm(t)) if w.strip("-'")]


def mattr(tokens, window=100):
    if len(tokens) < window:
        return len(set(tokens)) / max(1, len(tokens))
    vals = [len(set(tokens[i:i + window])) / window for i in range(0, len(tokens) - window + 1)]
    return sum(vals) / len(vals)


def cv(values):
    if len(values) < 2:
        return None
    m = statistics.mean(values)
    return statistics.pstdev(values) / m if m else None


def snippet(sentence, n=110):
    s = " ".join(sentence.split())
    return s if len(s) <= n else s[:n] + "…"


# ---------------------------------------------------------------- аналіз

def analyze(text):
    text = norm(text)
    paras = split_paragraphs(text)
    sents = [s for p in paras for s in split_sentences(p)]
    toks = words(text)
    n = len(toks)
    per1k = lambda x: round(x * 1000 / n, 1) if n else 0.0

    slen = [len(words(s)) for s in sents]
    plen = [len(words(p)) for p in paras]

    # кліше
    cliche_hits, cliche_weight = [], 0
    low_sents = [(s, s.lower()) for s in sents]
    for pat, w, tip in CLICHES:
        rx = re.compile(pat, re.I | re.M)
        for s, ls in low_sents:
            m = rx.search(ls)
            if m:
                cliche_hits.append({"фраза": m.group(0).strip(" .!?"), "вага": w,
                                    "порада": tip, "речення": snippet(s)})
                cliche_weight += w

    # кліше, що охоплюють кілька речень
    for pat, w, tip in CLICHES:
        if "\\s\\S" in pat:
            m_ = re.search(pat, text.lower(), re.I)
            if m_ and not any(h["порада"] == tip for h in cliche_hits):
                cliche_hits.append({"фраза": snippet(m_.group(0), 60), "вага": w, "порада": tip, "речення": "(кілька речень)"})
                cliche_weight += w

    # кальки
    calque_hits = []
    for pat, fix in CALQUES:
        rx = re.compile(pat, re.I)
        for s, ls in low_sents:
            for m in rx.finditer(ls):
                calque_hits.append({"калька": m.group(0), "норма": fix, "речення": snippet(s)})
    for s, ls in low_sents:
        for m in PARTICIPLE_RE.finditer(ls):
            w = m.group(0)
            base = re.sub(r"(ий|а|е|і|ого|ому|им|их|ими|ої|ій|у|ою)$", "ий", w)
            if base not in PARTICIPLE_OK and len(w) > 6 and not NOUN_ACH.match(w):
                calque_hits.append({"калька": w, "норма": "перевірити: активний дієприкметник → «який/що …»",
                                    "речення": snippet(s)})

    # граматичне багатство
    diepr_words = [t for t in toks if DIEPR_RE.fullmatch(t) and not DIEPR_EXCL.search(t)]
    complex_n = sum(1 for s in sents if SUBORD.search(s.lower()) or COORD.search(s.lower()))
    subord_n = sum(1 for s in sents if SUBORD.search(s.lower()))
    detached_n = sum(1 for s in sents if DETACHED.search(s.lower()))

    # сліди чату / шаблонів
    chat_hits = [m.group(0) for pat in CHAT_RESIDUE for m in re.finditer(pat, text.lower())]

    # «інженерна людяність»: ударні кінцівки, механічне чергування, звороти на початку
    closers = 0
    for p in paras:
        ss = split_sentences(p)
        if len(ss) >= 3:
            last = len(words(ss[-1])); avg = statistics.mean(len(words(x)) for x in ss[:-1])
            if last <= 7 and avg and last < 0.5 * avg:
                closers += 1
    closer_share = round(closers / len(paras), 2) if paras else 0
    lag1 = None
    if len(slen) >= 10 and statistics.pstdev(slen):
        mu = statistics.mean(slen)
        num = sum((slen[i] - mu) * (slen[i + 1] - mu) for i in range(len(slen) - 1))
        den = sum((x - mu) ** 2 for x in slen)
        lag1 = round(num / den, 3) if den else None
    diepr_start = sum(1 for s_ in sents if words(s_) and DIEPR_RE.fullmatch(words(s_)[0])
                      and not DIEPR_EXCL.search(words(s_)[0]))

    # конкретика: числа, власні назви всередині речення, лапки «», перша особа
    numbers = len(re.findall(r"\b\d+([.,]\d+)?\b", text))
    proper = sum(1 for s_ in sents for w in WORD_RE.findall(s_)[1:]
                 if w[:1].isupper() and len(w) > 2 and not w.isupper() and CYR.search(w))
    quotes_uk = text.count("«")
    first_person = sum(1 for t in toks if t in {"я", "ми", "мене", "мені", "нас", "нам", "мій", "моя", "наш", "наша", "наші"})
    concreteness = numbers + proper + quotes_uk

    # типографіка
    straight_quotes = len(re.findall(r'"[^"\n]{2,}"', text))
    hyphen_dash = len(re.findall(r"\s-\s", text))

    # гарячі точки (для змішаних текстів)
    hotspots = []
    for i, p in enumerate(paras, 1):
        pl = p.lower(); w_ = 0; found = []
        for pat, wt, _ in CLICHES:
            if re.search(pat, pl, re.I | re.M):
                w_ += wt; found.append(re.search(pat, pl, re.I | re.M).group(0).strip())
        for pat, _ in CALQUES:
            m_ = re.search(pat, pl, re.I)
            if m_:
                w_ += 2; found.append(m_.group(0))
        if w_:
            hotspots.append({"абзац": i, "вага": w_, "знайдено": found[:6], "початок": snippet(p, 70)})
    hotspots.sort(key=lambda h: -h["вага"])

    # одноманітні пасивні початки: «Формується…», «Визначаються…», «Забезпечується…»
    lines = [l.strip() for l in text.split("\n") if WORD_RE.search(l)]
    prx = re.compile(r"\W*\w+(ується|уються|юється|юються|ається|аються|яється|яються|иться|аться|яться)\b")
    cand = [(u, sum(1 for x in u if prx.match(x.lower()))) for u in (sents, lines) if u]
    units, passive_start = max(cand, key=lambda c: c[1] / len(c[0]))
    passive_share = round(passive_start / len(units), 2) if units else 0

    # симетрія списків: блоки з однаковою кількістю пунктів
    list_blocks, cur = [], 0
    for l in text.split("\n"):
        if l.strip() and not re.match(r"^\s*\d+[.)]\s", l) and len(words(l)) <= 25 and not l.rstrip().endswith(":"):
            cur += 1
        else:
            if cur >= 2:
                list_blocks.append(cur)
            cur = 0
    if cur >= 2:
        list_blocks.append(cur)
    list_symmetry = None
    if len(list_blocks) >= 3:
        c = Counter(list_blocks)
        list_symmetry = round(c.most_common(1)[0][1] / len(list_blocks), 2)

    # двомовні глоси «термін (English Term)» і пункти «Мітка: Опис» — почерк моделей-пояснювачів
    glosses = len(re.findall(r"\([A-Z][A-Za-z0-9 &./-]{2,40}\)", text))
    label_lines = sum(1 for l in lines if re.match(r"^[^:]{3,70}:\s+[А-ЯA-ZЄІЇҐ]", l))
    label_share = round(label_lines / len(lines), 2) if lines else 0

    # SEO-переспам: найчастіша біграма з повнозначних слів
    STOP = {"та", "і", "й", "для", "з", "із", "у", "в", "на", "до", "від", "що", "як", "по", "за", "чи", "або", "а", "не", "це", "їх", "ми", "наш", "наша", "наші", "під", "при", "про", "the", "of"}
    bigr = Counter((a_, b_) for a_, b_ in zip(toks, toks[1:]) if a_ not in STOP and b_ not in STOP and len(a_) > 3 and len(b_) > 3)
    top_bigram, top_bigram_n = (bigr.most_common(1)[0] if bigr else (("", ""), 0))
    top_bigram_per1k = per1k(top_bigram_n)

    # структура
    starts = Counter(words(s)[0] for s in sents if words(s))
    top_start, top_start_n = (starts.most_common(1)[0] if starts else ("", 0))
    dashes = len(re.findall(r"\s[—–]\s", text))
    md = len(re.findall(r"\*\*|^#{1,6}\s|^\s*[-*•]\s|^\s*\d+[.)]\s", text, re.M))
    emoji = len(EMOJI_RE.findall(text))
    rq_para = sum(1 for p in paras if split_sentences(p) and split_sentences(p)[0].rstrip().endswith("?"))

    m = {
        "слів": n,
        "речень": len(sents),
        "абзаців": len(paras),
        "середня_довжина_речення": round(statistics.mean(slen), 1) if slen else 0,
        "CV_довжини_речень": round(cv(slen), 3) if cv(slen) is not None else None,
        "частка_коротких_речень_до7": round(sum(1 for x in slen if x <= 7) / len(slen), 2) if slen else 0,
        "частка_довгих_речень_30плюс": round(sum(1 for x in slen if x >= 30) / len(slen), 2) if slen else 0,
        "CV_довжини_абзаців": round(cv(plen), 3) if len(plen) >= 3 and cv(plen) is not None else None,
        "MATTR": round(mattr(toks), 3) if toks else 0,
        "найчастіший_початок_речення": top_start,
        "частка_цього_початку": round(top_start_n / len(sents), 2) if sents else 0,
        "тире_на_1000_слів": per1k(dashes),
        "маркдаун_сліди": md,
        "емодзі": emoji,
        "абзаців_з_риторичного_питання": rq_para,
        "дієприслівників": len(diepr_words),
        "дієприслівників_на_1000_слів": per1k(len(diepr_words)),
        "частка_складних_речень": round(complex_n / len(sents), 2) if sents else 0,
        "частка_складнопідрядних": round(subord_n / len(sents), 2) if sents else 0,
        "речень_з_відокремленими_обставинами_прийм": detached_n,
        "кліше_знайдено": len(cliche_hits),
        "кальки_знайдено": len(calque_hits),
        "сліди_чату_шаблонів": chat_hits,
        "частка_одиниць_з_пасивним_початком": passive_share,
        "двомовних_глосів_на_1000_слів": per1k(glosses),
        "найчастіша_біграма": " ".join(top_bigram),
        "найчастіша_біграма_на_1000_слів": top_bigram_per1k,
        "частка_рядків_виду_Мітка_Опис": label_share,
        "симетрія_списків": list_symmetry,
        "ударні_кінцівки_абзаців_частка": closer_share,
        "автокореляція_довжин_речень_lag1": lag1,
        "речень_що_починаються_дієприслівником": diepr_start,
        "конкретика_на_1000_слів": per1k(concreteness),
        "перша_особа_на_1000_слів": per1k(first_person),
        "прямі_лапки_замість_кутових": straight_quotes,
        "дефіс_замість_тире": hyphen_dash,
        "невидимих_символів": OBF["zero_width"],
        "слів_зі_змішаною_абеткою": len(OBF["mixed_words"]),
        "приклади_змішаної_абетки": OBF["mixed_words"][:8],
    }
    m["дієприслівники_приклади"] = sorted(set(diepr_words))[:15]

    # ------------------------------------------------ індекс
    score, why = 0, []

    def add(pts, reason):
        nonlocal score
        if pts:
            score += pts
            why.append(f"+{pts}: {reason}")

    c = m["CV_довжини_речень"]
    if c is not None and len(sents) >= 8:
        add(20 if c < 0.25 else 14 if c < 0.35 else 7 if c < 0.45 else 0,
            f"рівний ритм речень (CV={c})")
    if n >= 150:
        add(min(30, round(cliche_weight * 1000 / n / 1.5)), f"ШІ-кліше: {len(cliche_hits)} (вага {cliche_weight})")
    else:
        add(min(30, cliche_weight * 2), f"ШІ-кліше: {len(cliche_hits)}")
    add(min(10, len(calque_hits) * 2), f"кальки: {len(calque_hits)}")
    if n >= 200 and m["дієприслівників_на_1000_слів"] < 3:
        add(8, "майже нема дієприслівників")
    if len(sents) >= 8 and m["частка_складнопідрядних"] < 0.2:
        add(6, "мало складнопідрядних речень")
    if len(sents) >= 8 and m["частка_цього_початку"] > 0.15 and top_start_n >= 3:
        add(6, f"повтор початку «{top_start}»")
    if m["CV_довжини_абзаців"] is not None and len(paras) >= 4 and m["CV_довжини_абзаців"] < 0.25:
        add(6, "однакові абзаци")
    if n >= 300 and m["тире_на_1000_слів"] > 8:
        add(5, "надмір тире")
    if md:
        add(5, "маркдаун-сліди")
    if emoji > 2:
        add(3, "емодзі")
    if rq_para >= 2:
        add(3, "абзаци починаються риторичними питаннями")
    if n >= 300 and m["MATTR"] < 0.62:
        add(4, f"невисоке лексичне різноманіття (MATTR={m['MATTR']})")
    if OBF["zero_width"] or OBF["mixed_words"]:
        add(25, f"ОБФУСКАЦІЯ: невидимих символів {OBF['zero_width']}, слів зі змішаною абеткою {len(OBF['mixed_words'])} — текст навмисно ховали від детектора")
    if chat_hits:
        add(min(40, 20 * len(chat_hits)), f"сліди чату/шаблону: {chat_hits[:3]} (один слід = вердикт, індекс не нижче 70)")
    engineered = 0
    if len(paras) >= 4 and closer_share >= 0.6:
        engineered += 1
        add(8 if closer_share >= 0.8 else 5, f"кожен абзац закінчується коротким «ударом» ({closer_share}) — інженерна людяність")
    if lag1 is not None and lag1 < -0.45:
        engineered += 1
        add(5, f"механічне чергування коротких і довгих речень (lag1={lag1})")
    if len(sents) >= 8 and diepr_start / len(sents) > 0.25:
        engineered += 1
        add(8 if diepr_start / len(sents) > 0.4 else 5, "надто багато речень починаються дієприслівниковим зворотом")
    if engineered >= 2:
        add(10, "кілька ознак «інженерної людяності» разом — текст, ймовірно, промптували під людський стиль")
    if n >= 300 and m["конкретика_на_1000_слів"] < 6:
        add(6, f"майже нема конкретики: {m['конкретика_на_1000_слів']} чисел/назв/цитат на 1000 слів")
    if len(units) >= 10 and passive_share >= 0.3:
        add(10 if passive_share >= 0.55 else 6, f"одноманітні пасивні початки «Формується/Визначаються…» ({passive_share})")
    if list_symmetry is not None and list_symmetry >= 0.6 and (md >= 3 or len(list_blocks) >= 5):
        add(6, f"симетричні списки: {list_symmetry} блоків однакової довжини — шаблонна структура")
    if n >= 200 and top_bigram_per1k >= 15 and top_bigram_n >= 5:
        add(5, f"SEO-переспам: «{' '.join(top_bigram)}» {top_bigram_per1k} разів на 1000 слів")
    if n >= 200 and m["двомовних_глосів_на_1000_слів"] >= 8:
        add(6, f"двомовні глоси «термін (English)»: {m['двомовних_глосів_на_1000_слів']} на 1000 слів")
    if len(lines) >= 10 and label_share >= 0.4:
        add(6, f"пункти виду «Мітка: Опис» ({label_share}) — типовий формат відповіді моделі")
    if straight_quotes >= 2 or hyphen_dash >= 3:
        add(2, "типографіка: прямі лапки або дефіс замість тире")

    if chat_hits:
        score = max(score, 70)
    score = min(100, score)
    level = ("низький" if score <= 25 else "помірний" if score <= 50
             else "високий" if score <= 75 else "дуже високий")
    reliability = ("низька (текст закороткий)" if n < 150 else
                   "середня" if n < 400 else "прийнятна")

    return {"індекс": score, "рівень": level, "надійність_статистики": reliability,
            "складові_індексу": why, "метрики": m,
            "кліше": cliche_hits, "кальки": calque_hits, "гарячі_точки": hotspots[:5]}


# ---------------------------------------------------------------- вивід

def to_markdown(r):
    m = r["метрики"]
    out = [f"# Індекс ознак ШІ: {r['індекс']}/100 ({r['рівень']})",
           f"Надійність статистики: {r['надійність_статистики']} · слів: {m['слів']}, речень: {m['речень']}, абзаців: {m['абзаців']}",
           "", "## Складові індексу"]
    out += [f"- {w}" for w in r["складові_індексу"]] or ["- (жодної статистичної ознаки)"]
    out += ["", "## Метрики", "| Метрика | Значення | Орієнтир для людського тексту |", "|---|---|---|"]
    guide = {
        "CV_довжини_речень": "0,45–0,8", "частка_коротких_речень_до7": "≥ 0,1",
        "CV_довжини_абзаців": "> 0,3", "MATTR": "> 0,68 (залежить від жанру)",
        "частка_цього_початку": "< 0,15", "тире_на_1000_слів": "< 8",
        "дієприслівників_на_1000_слів": "4–15", "частка_складних_речень": "0,35–0,6",
        "частка_складнопідрядних": "≥ 0,25", "конкретика_на_1000_слів": "≥ 10 (крім абстрактних жанрів)",
        "ударні_кінцівки_абзаців_частка": "< 0,5", "автокореляція_довжин_речень_lag1": "від −0,4 до 0,4",
        "невидимих_символів": "0", "слів_зі_змішаною_абеткою": "0",
        "частка_одиниць_з_пасивним_початком": "< 0,3", "симетрія_списків": "< 0,6",
        "двомовних_глосів_на_1000_слів": "< 5", "частка_рядків_виду_Мітка_Опис": "< 0,3",
        "найчастіша_біграма_на_1000_слів": "< 12",
    }
    for k, v in m.items():
        if k in ("дієприслівники_приклади", "приклади_змішаної_абетки"):
            continue
        out.append(f"| {k} | {v} | {guide.get(k, '')} |")
    if m["дієприслівники_приклади"]:
        out.append(f"\nЗнайдені дієприслівники: {', '.join(m['дієприслівники_приклади'])}")
    if m["приклади_змішаної_абетки"]:
        out.append(f"\nСлова зі змішаною абеткою: {', '.join(m['приклади_змішаної_абетки'])}")
    if r["кліше"]:
        out += ["", "## Кліше", "| Фраза | Порада | Речення |", "|---|---|---|"]
        out += [f"| {h['фраза']} | {h['порада']} | {h['речення']} |" for h in r["кліше"]]
    if r["кальки"]:
        out += ["", "## Кальки", "| Калька | Норма | Речення |", "|---|---|---|"]
        out += [f"| {h['калька']} | {h['норма']} | {h['речення']} |" for h in r["кальки"]]
    if r["гарячі_точки"]:
        out += ["", "## Гарячі точки (абзаци з найбільшою густотою ознак — для змішаних текстів)"]
        out += [f"- абзац {h['абзац']} (вага {h['вага']}): {', '.join(h['знайдено'])} — «{h['початок']}»" for h in r["гарячі_точки"]]
    out += ["", "## Чого скрипт НЕ бачить",
            "- добре промптований ШІ-текст без кліше і з вигаданою конкретикою — його ловить лише якісний аналіз і перевірка фактів;",
            "- переклад людського тексту через ШІ; ШІ-текст, переписаний людиною;",
            "- правдивість чисел, імен і посилань — їх треба перевіряти окремо."]
    out += ["", "_Індекс — евристика. Остаточний висновок робіть разом з якісним аналізом._"]
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    OBF["zero_width"] = 0; OBF["mixed_words"].clear()
    r = analyze(read_input(args[0]))
    try:
        print(json.dumps(r, ensure_ascii=False, indent=2) if "--json" in sys.argv else to_markdown(r))
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
