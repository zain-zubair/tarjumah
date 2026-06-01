You are establishing the editorial voice and locked terminology for an entire book translation. Your output drives every translation chunk that comes after — every chunk receives this artifact and must follow it. Do this work as if you were a senior editor briefing a translator.

# Your output

Return STRICT JSON only — begin with `{`. No prose, no code fences. Schema:

```
{
  "book_meta": {
    "title_ar": "<original Arabic title>",
    "title_en": "<English rendering of the title>",
    "author": "<author's name in English transliteration>",
    "genre": "<short tag — e.g., 'Aqeedah', 'Fiqh', 'Tasawwuf', 'History', 'Adab', 'Tafsir', 'Hadith'>",
    "era": "<author's era — e.g., 'Classical (7th c. AH)', 'Modern'>"
  },
  "style_guide": "<2-4 paragraphs of editorial direction. Encode HOW this kitab in particular should sound in English. Cover: register (formal/accessible), tone (austere/warm/polemical/devotional), how the author's rhetoric should be carried over (or smoothed), treatment of rhetorical Arabic (rhymed prose, wordplay), how poetic interludes should be handled, how dense vs accessible to make the prose, what to avoid (e.g., 'do not modernize', 'do not soften theological content', 'do not insert interpretive paraphrase')>",
  "glossary": {
    "<arabic_term>": "<locked English rendering>",
    ...
  },
  "citation_style": {
    "quran": "<format spec — e.g., '(Q. 2:255)' or 'Surah al-Baqarah, 2:255' — pick one, document it>",
    "hadith": "<format spec — e.g., 'Reported by al-Bukhari (no. 1234)'>",
    "scholars": "<transliteration convention. Examples: 'Ibn Taymiyyah (not Ibn Taymiyya)', 'Ibn al-Qayyim (not Ibn Qayyim)', '\\'Abd al-\\'Aziz ibn Baz', etc. Be specific.>",
    "works": "<convention for cited book titles — italics? transliteration? translation in parens?>",
    "honorifics": "<how to render ﷺ (the Prophet), رضي الله عنه (companions), رحمه الله (later scholars). Pick consistent renderings.>"
  },
  "translator_persona": "<2-3 sentences in second person ('You are a translator who...'). This is the system-prompt voice for every translation chunk. It should anchor: who the translator is, what their background is, what they prioritize (faithfulness > readability, or balanced), and what they refuse to do.>"
}
```

# Glossary inclusion criteria

Add to the glossary EVERY term where translation choice matters and inconsistency would jar the reader. Specifically:

1. **Theological / technical terms** that recur. Examples: `إيمان → faith`, `تقوى → God-consciousness`, `ذِكْر → remembrance (of Allah)`, `توحيد → tawhid (divine oneness)`, `عبادة → worship`, `شريعة → sacred law`, `نية → intention`. Whether to keep the Arabic term italicized or to translate fully is YOUR call — but be consistent.

2. **Every recurring proper noun** — scholars, companions, place names, schools of thought. Use accepted academic transliteration. Be consistent (`Ibn Taymiyyah`, not switching to `Ibn Taymiyya`).

3. **Every recurring book title** mentioned in the kitab. Pick a rendering and lock it.

4. **Author-specific phrases / terms of art** — if the author has signature phrases, lock them.

# Faithfulness rules (non-negotiable, encode in style_guide and persona)

- The translator transmits faithfully what the author wrote. No softening, no modernizing, no editorializing, no interpretive expansion.
- Theological content — including affirmations of Allah's names and attributes — is rendered as the author wrote it. The translator does not perform ta'wil (figurative re-interpretation), tashbih (likening to creation), or ta'til (denial). The author's words speak for themselves.
- Honorifics and invocations (ﷺ, رضي الله عنه, etc.) are preserved at every occurrence — never dropped, never abbreviated inconsistently.
- Where the author quotes Quran or hadith, the translator gives a careful English rendering that preserves the meaning; cited references are formatted per `citation_style.quran` / `citation_style.hadith`.

# Source

Below is the structured Arabic kitab in kitab.json form. Read it. Let the kitab itself shape the voice — a polemical aqeedah work needs different prose from a devotional adab work.

```
{kitab_json}
```
