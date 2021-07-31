import re

END_OF_SENTENCE_SYMBOLS = {'.', '!', '?', '؟'}

#HappyEmoticons
emoticons_happy = set([
    ':-)', ':)', ';)', ':o)', ':]', ': )', '; )', ':3', ':c)', ':>', '=]', '8)', '=)', ':}',
    ':^)', ':-D', ':D', '8-D', '8D', 'x-D', 'xD', 'X-D', 'XD', '=-D', '=D',
    '=-3', '=3', ':-))', ":'-)", ":')", ':*', ':-*', ':^*', '>:P', ':-P', ':P', 'X-P',
    'x-p', 'xp', 'XP', ':-p', ':p', '=p', ':-b', ':b', '>:)', '>;)', '>:-)',
    '<3'
])

# Sad Emoticons
emoticons_sad = set([
    ':L', ':-/', '>:/', ':S', '>:[', ':@', ':-(', ':[', ':-||', '=L', ':<',
    ':-[', ':-<', '=\\', '=/', '>:(', ':(', '>.<', ":'-(", ":'(", ':\\', ':-c',
    ':c', ':{', '>:\\', ';(', ':(', ': (', ':/'
])

EMOTICONS = emoticons_happy.union(emoticons_sad)

#Emoji patterns
EMOJI_PATTERN = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)

### Regex parsers
regex_query_remove_url = r'https?:\/\/[^\s]*[\r\n]*'
regex_patt_hashtag = r'\s(#[^\s]+)'
regex_patt_mention = r'\s(@[^\s]+)'
regex_patt_hashtag = r'\s(#[^\s]+)'
regex_patt_mention = r'\s(@[^\s]+)'
regex_patt_hashtag_ar = r'([^\s]+#)\s'
regex_patt_mention_ar = r'([^\s]+@)\s'


def cleanse_text(text, dict_hash, dict_ment, isArabic=False):
    text_cleaned = text
    if text_cleaned is None or len(text_cleaned) == 0:
        return None

    if len(text_cleaned.strip()) > 2:
        text_cleaned = re.sub(regex_query_remove_url, '', text_cleaned)
        text_cleaned = EMOJI_PATTERN.sub(r'', text_cleaned)
        for em in EMOTICONS:
            text_cleaned = text_cleaned.replace(em, "")

        # after removing emoticons, smileys and URLs, remove list of hashtags at the end of the post
        text_cleaned = remove_end_hashtags_mentions(text, isArabic)
        if text_cleaned is None or len(text_cleaned) == 0:
            return None

        # replace within-text hashtags & mentions with their processed version
        for k, v in dict_hash.items():
            if isArabic:
                text_cleaned = text_cleaned.replace(k + "#", v)
            text_cleaned = text_cleaned.replace("#" + k, v)
        for k, v in dict_ment.items():
            if isArabic:
                text_cleaned = text_cleaned.replace(k + "@", v)
            text_cleaned = text_cleaned.replace("@" + k, v)
    text_cleaned = text_cleaned.strip()

    if isArabic and len(text_cleaned) > 2 and text_cleaned[-1] in END_OF_SENTENCE_SYMBOLS:
        text_cleaned = text_cleaned[-1] + text_cleaned[:-1]
        while len(text_cleaned) > 2 and text_cleaned[-1] == '.': # for cases when people use multiple dots: "And so on ..."
            text_cleaned = text_cleaned[:-1]
        text_cleaned = text_cleaned.strip()

    if isArabic and len(text_cleaned) > 2 and len([1 for x in END_OF_SENTENCE_SYMBOLS if text_cleaned[0] == x]) == 0:
        text_cleaned = '.' + text_cleaned

    return text_cleaned


def remove_end_hashtags_mentions(text, isArabic=False):
    if text is None or len(text.strip()) == 0:
        return None
    text_cleansed = text.replace("\n", " ").replace("\t", " ").strip()
    if isArabic:
        while len(text_cleansed) > 0 and (text_cleansed.split(" ")[-1][-1] in {"#", "@"} or text_cleansed.split(" ")[-1][0] in {"#", "@"}):
            text_cleansed = " ".join(text_cleansed.split(" ")[:-1]).strip()
    else:
        while len(text_cleansed) > 0 and text_cleansed.split(" ")[-1][0] in {"#", "@"}:
            text_cleansed = " ".join(text_cleansed.split(" ")[:-1]).strip()
    return text_cleansed


def remove_urls(text):
    text_cleaned = text
    if len(text_cleaned.strip()) > 2:
        text_cleaned = re.sub(regex_query_remove_url, '', text_cleaned)
    return text_cleaned