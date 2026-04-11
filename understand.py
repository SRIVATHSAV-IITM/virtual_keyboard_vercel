try:
    import nltk
    nltk.download('words', quiet=True)
    from nltk.corpus import words
    DICTIONARY_WORDS = list(set(words.words()))
    print(len(DICTIONARY_WORDS))
except Exception as e:
    DICTIONARY_WORDS = []