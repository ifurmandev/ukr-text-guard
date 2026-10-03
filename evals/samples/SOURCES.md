# Sources register — human samples

This file records where every human sample of the eval comes from and why it may sit in a public repository. The eval ignores it (it is not a `.txt` file). It is the only place that explains why a text counts as human.

## Rules

1. **Register first, samples second.** The entry of a candidate, with its fragment borders and blind word count, is committed here before the analyzer is run on the text and before the sample file is committed. A later addition repeats the pattern.
2. **A score is never a reason to change the set.** A sample is replaced, dropped or re-cut only for provenance, basis for publication, a length below 150 or above 600 words under the selection rule, or a defect of the file. Never for its index. A false alarm stays in the set and in the README table.
3. **Selection rule.** The fragment runs from the start of the work or section to the first paragraph end after 150 words. Length is measured with the analyzer's own `words()` function (`plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py`), never by calling `analyze()` or the eval on a candidate. A fragment under 150 or over 600 words is refused, not trimmed by hand.
4. **Permitted changes to the text.** Only the fragment cut, removed invisible characters, and personal details replaced by neutral words of the same kind. Each change is logged in the entry. Anything else is restored to the source text.
5. **Only texts written before 2023 count as human.** A date of writing that is unknown or 2023 or later is refused as human.
6. **No text without a nameable basis for publication.** Allowed bases: public domain, an official document outside copyright, the plugin author's own text (no third-party personal data or confidential content left).
7. **Defaults for open questions.** Evidence of the date of writing for an own text: any dated original the plugin author can point to, recorded as a reference. Edition: the original public-domain text, never a modern edition with editorial rights; for a law, the version in force before 2023.
8. **File rules.** UTF-8 without BOM, LF line ends, no invisible characters. Name: `human-<author>-<work>.txt`. The entry heading carries the same stem.

Genres (one per entry): business letters and mail · articles and blogs · technical and legal documents · fiction and informal style.

## Entry template

```markdown
## human-<author>-<work>

- **Author:** <one named person, or the one body that adopted an official document>
- **Genre:** <one of the four genres>
- **Source:** <URL or edition, with the section or work title>
- **Basis for publication:** <public domain | official document outside copyright | own text>
- **Date of writing:** <year> — evidence: <reference>
- **Fragment borders:** from <first words> to <last words>
- **Blind word count:** <n> (by `words()`, before any run of the analyzer)
- **Change log:** <none | each change: what, where, why>
```

## Refusal template

```markdown
- **<candidate>** — reason: <AC-05 basis for publication | AC-06 length / provenance / file defect | AC-07 date> — <date of the decision>
```

## Pre-ship review checklist

- [ ] Every human sample has an entry with all fields filled.
- [ ] At least 3 authors, at least 1 of them another person (neither the plugin author nor an official body).
- [ ] Every blind word count is between 150 and 600.
- [ ] In `git log` the register commit precedes the commit that adds the sample files.
- [ ] Human sample files total at most 150 KB.
- [ ] Every refused candidate is listed below with its reason.

## Samples

### human-franko-miy-zlochyn

- **Author:** Ivan Franko (another person)
- **Genre:** fiction and informal style
- **Source:** uk.wikisource.org, «Твори в 20 томах», vol. II, «Мій злочин» (New York: Книгоспілка, 1956), https://uk.wikisource.org/wiki/Твори_(Франко,_1956–1962)/2/Мій_злочин
- **Basis for publication:** public domain (the author died in 1916; the text is the author's original story, the fragment holds no editorial apparatus)
- **Date of writing:** not later than 1916, the author's death — evidence: the work is printed in the 1956 edition above; the exact year is not claimed
- **Fragment borders:** from «Ні, не видержу! Не можу довше видержати!» to «…чим більше силкуюся забути про нього, затерти його.» (the first two paragraphs of the story, after the title line)
- **Blind word count:** 248 (by `words()`, before any run of the analyzer)
- **Change log:** none. The file keeps the one no-break space (U+00A0) of the source; it is not an invisible character in the eval's sense, so it was not altered.

### human-kotsiubynskyi-dorohoiu-tsinoiu

- **Author:** Mykhailo Kotsiubynskyi (another person)
- **Genre:** fiction and informal style
- **Source:** uk.wikisource.org, «Твори в 2-х томах», vol. I, «Дорогою ціною» (New York: Книгоспілка, 1955), https://uk.wikisource.org/wiki/Твори_(Коцюбинський,_1955)/1/Дорогою_ціною
- **Basis for publication:** public domain (the author died in 1913; the text is the author's original story, the fragment holds no editorial apparatus)
- **Date of writing:** not later than 1913, the author's death — evidence: the work is printed in the 1955 edition above; the exact year is not claimed
- **Fragment borders:** from «Діялось це в тридцятих роках минулого століття.» to «…рвалась гаряча уява й тягла за собою сотки й тисячі…» (the first two paragraphs after the title and the subtitle «Оповідання»)
- **Blind word count:** 173 (by `words()`, before any run of the analyzer)
- **Change log:** none. The file equals the registered fragment.

### human-verkhovna-rada-konstytutsiia

- **Author:** Verkhovna Rada of Ukraine (an official body)
- **Genre:** technical and legal documents
- **Source:** uk.wikisource.org, «Конституція України (1996)», the text as adopted on 28 June 1996, https://uk.wikisource.org/wiki/Конституція_України_(1996)
- **Basis for publication:** official document outside copyright (Law of Ukraine «On Copyright and Related Rights», Art. 10: official documents of state bodies are not objects of copyright)
- **Date of writing:** 28 June 1996 — evidence: adoption date in the same source; the original version, not a later amended one
- **Fragment borders:** from «Верховна Рада України від імені Українського народу» to «…визнаються в Україні найвищою соціальною цінністю.» (the preamble and Articles 1–3, first paragraph of Article 3; one source line is one paragraph)
- **Blind word count:** 152 (by `words()`, before any run of the analyzer)
- **Change log:** none. The file keeps the two no-break spaces (U+00A0) of the source; they are not invisible characters in the eval's sense, so they were not altered.

## Refusals

No candidate has been refused in the first batch. A refusal is recorded here in the refusal template format.
