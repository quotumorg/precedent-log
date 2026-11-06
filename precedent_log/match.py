"""Word overlap only: no inference, network, or fuzzy semantic claims."""

import re


STOPWORDS = frozenset("a an and are as at be been but by can do does for from has have how i in is it its of on or our should that the their this to use was we what when where which with would you your".split())


def normalize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return frozenset(word[:-1] if len(word) > 3 and word.endswith("s") else word
                     for word in words if word not in STOPWORDS)


def key_token(text):
    """A key is one whole word, never a multiword phrase or substring."""
    if not isinstance(text, str) or not re.fullmatch(r"[a-z0-9]+", text.strip(), re.I):
        return None
    words = normalize(text)
    return next(iter(words)) if len(words) == 1 else None


def overlap_score(words, phrase):
    tokens = normalize(phrase)
    overlap = len(tokens & words)
    return overlap / len(tokens) if tokens else 0.0, overlap >= 2 and overlap * 5 >= len(tokens) * 3


def match(reason, rulings):
    words = normalize(reason)
    found = []
    for row in rulings:
        if row.get("retired"):
            continue
        score, question_match = overlap_score(words, row["question"])
        keys = row.get("keys", [])
        matches = all(key_token(key) in words for key in keys) if keys else question_match
        # Human aliases are alternate questions. They use the same 60%/two-word
        # rule, independently of keys that describe the original question.
        for alias in row.get("also", []):
            alias_score, alias_match = overlap_score(words, alias)
            if alias_match:
                matches = True
                score = max(score, alias_score)
        if matches:
            found.append((score, int(row["id"][2:]), row))
    found.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in found[:3]]
