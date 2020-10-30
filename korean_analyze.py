#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import numpy as np
import json
import gensim
import pyLDAvis.gensim as gensimvis
import pyLDAvis
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from konlpy.tag import Okt
from review_tokenize import df_tokenize
from gensim.models import LdaModel
from os.path import join
from os import remove
from gensim.models import Word2Vec
from collections import Counter
from render import render


# In[4]:


df = pd.read_pickle("example_posts.pkl")
df.head()


# In[5]:


# version nori
def tokenizeNpostprocess(df):
    df = df_tokenize(df)
    return df


df.head()


# In[6]:


def tokenize_okt(df):
    okt = Okt()
    df['content_token'] = df['content'].map(lambda x: [t[0] for t in okt.pos(
        x, stem=True) if t[1] in ['Noun', 'Verb', 'Adjective']])
    df['title_token'] = df['title'].map(lambda x: [t[0] for t in okt.pos(
        x, stem=True) if t[1] in ['Noun', 'Verb', 'Adjective']])
    return df


# In[7]:


def identity_tokenizer(text):
    """
    sklearn의 Tfidfvectorizer를 이용함에 있어서 우리의 nori 토크나이저가 토큰화 한 결과를 사용하기 위한 method이다.

    :param text: 토큰화 하고자 하는 문장
    :return: 토큰이 담긴 리스트가 반환된다.
    """
    list1 = text.split('00')
    return list1


# In[8]:


def TfidfWord(df):
    # TF-IDF를 기반으로 카이스트 검색시 가장 의미가 높은 단어로 예상되는 단어 100가지를 추출함.

    vectorizer = TfidfVectorizer(tokenizer=identity_tokenizer,
                                 max_features=100,
                                 max_df=0.5,
                                 ngram_range=(1, 1))

    # content를 기반으로 TF-IDF를 돌리는 함수
    words_list_content = []
    token_concat = df['content_token'].map(lambda x: "00".join(x))
    tfidf_matrix = vectorizer.fit_transform(token_concat)
    tfidf_wordslist = vectorizer.get_feature_names()
    vocab = dict()
    for idx, word in enumerate(tfidf_wordslist):
        vocab[word] = tfidf_matrix.getcol(idx).sum()
    words_list_content = sorted(
        vocab.items(), key=lambda x: x[1], reverse=True)

    # title을 기반으로 TF-IDF를 돌리는 함수
    words_list_title = []
    token_concat = df['title_token'].map(lambda x: "00".join(x))
    tfidf_matrix = vectorizer.fit_transform(token_concat)
    tfidf_wordslist = vectorizer.get_feature_names()
    vocab = dict()
    for idx, word in enumerate(tfidf_wordslist):
        vocab[word] = tfidf_matrix.getcol(idx).sum()
    words_list_title = sorted(vocab.items(), key=lambda x: x[1], reverse=True)

    return words_list_content, words_list_title


# In[9]:


def CountWord(df):
    # 단어가 나온 빈도수를 기반으로 카이스트 검색시 가장 의미가 높은 단어로 예상되는 단어 100가지를 추출함.

    vectorizer = CountVectorizer(tokenizer=identity_tokenizer,
                                 max_features=100,
                                 max_df=0.5,
                                 ngram_range=(1, 1))

    # content를 기반으로 TF-IDF를 돌리는 함수
    words_list_content = []
    token_concat = df['content_token'].map(lambda x: "00".join(x))
    tfidf_matrix = vectorizer.fit_transform(token_concat)
    tfidf_wordslist = vectorizer.get_feature_names()
    vocab = dict()
    for idx, word in enumerate(tfidf_wordslist):
        vocab[word] = tfidf_matrix.getcol(idx).sum()
    words_list_content = sorted(
        vocab.items(), key=lambda x: x[1], reverse=True)

    # title을 기반으로 를 돌리는 함수
    words_list_title = []
    token_concat = df['title_token'].map(lambda x: "00".join(x))
    tfidf_matrix = vectorizer.fit_transform(token_concat)
    tfidf_wordslist = vectorizer.get_feature_names()
    vocab = dict()
    for idx, word in enumerate(tfidf_wordslist):
        vocab[word] = tfidf_matrix.getcol(idx).sum()
    words_list_title = sorted(vocab.items(), key=lambda x: x[1], reverse=True)

    return words_list_content, words_list_title


# In[10]:


class Documents:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, encoding='utf-8') as f:
            for doc in f:
                yield doc.strip().split()


class Corpus:
    def __init__(self, path, dictionary):
        self.path = path
        self.dictionary = dictionary
        self.length = 0

    def __iter__(self):
        with open(self.path, encoding='utf-8') as f:
            for doc in f:
                yield self.dictionary.doc2bow(doc.split())

    def __len__(self):
        if self.length == 0:
            with open(self.path, encoding='utf-8') as f:
                for i, doc in enumerate(f):
                    continue
            self.length = i + 1
        return self.length


def topic_modeling(corpus_path, html_path):
    documents = Documents(corpus_path)
    dictionary = gensim.corpora.Dictionary(documents)
    min_count = 5
    word_counter = Counter((word for words in documents for word in words))
    removal_word_idxs = {
        dictionary.token2id[word] for word, count in word_counter.items()
        if count < min_count
    }

    dictionary.filter_tokens(removal_word_idxs)
    dictionary.compactify()
    corpus = Corpus(corpus_path, dictionary)
    from gensim.models import LdaModel
    lda_model = LdaModel(corpus, id2word=dictionary, num_topics=50)
    prepared_data = gensimvis.prepare(lda_model, corpus, dictionary)
    pyLDAvis.save_html(prepared_data, html_path)


# In[11]:


def find_cooccur(tokens, target, window, num):
    cooccur_dict = dict()
    for token in tokens:
        indices = [i for i, x in enumerate(
            token) if x.lower() == target.lower()]
        if len(indices) != 0:
            for indice in indices:
                for i in np.arange(indice-window, indice+window):
                    if i >= 0 and i <= len(token)-1:
                        if token[i] in cooccur_dict.keys():
                            cooccur_dict[token[i]] += 1
                        else:
                            cooccur_dict[token[i]] = 1
    try:
        del cooccur_dict[target]
    except KeyError:
        del cooccur_dict[target.upper()]
    return sorted(cooccur_dict.items(), key=lambda item: item[1], reverse=True)[:num]


# In[12]:


def stopwords_remove(dict):
    stopwords = ['kaist', '교수']
    for stopword in stopwords:
        try:
            del dict[stopword]
        except KeyError:
            continue
    return dict


# In[13]:


def word_tuple2dict(tups):
    target_dict = dict((x, int(y)) for x, y in tups)
    for key in list(target_dict.keys()):
        if len(key) == 1:
            del target_dict[key]
    return target_dict


# In[14]:


def dftotext(df, path):
    textlist = df['content_token'].tolist()
    with open(path, 'w', encoding='utf-8-sig') as f:
        for text in textlist:
            f.write(' '.join(text)+'\n')


# In[15]:


def analyze_korean(df, root_path, topic_num=10, keyword_num=50, topn=10):

    #df =tokenizeNpostprocess(df)
    df = tokenize_okt(df)
    print('tokenize end')
    detoken_path = join(root_path, 'detokenize_text.txt')
    dftotext(df, detoken_path)
    print('detokenize end')
    topic_modeling(detoken_path, join(root_path, 'topic_model.html'))
    print('topic model made')
    remove(detoken_path)

    # keyword extract part
    TF_content_word, TF_title_word = TfidfWord(df)
    Count_content_word, Count_title_word = CountWord(df)
    # TF_content_word_dict=word_tuple2dict(TF_content_word[:keyword_num])
    # TF_content_word_dict = stopwords_remove(TF_content_word_dict)
    # TF_title_word_dict=word_tuple2dict(TF_title_word[:keyword_num])
    # TF_title_word_dict = stopwords_remove(TF_title_word_dict)
    Count_content_word_dict = word_tuple2dict(Count_content_word[:keyword_num])
    Count_content_word_dict = stopwords_remove(Count_content_word_dict)
    Count_title_word_dict = word_tuple2dict(Count_title_word[:keyword_num])
    Count_title_word_dict = stopwords_remove(Count_title_word_dict)

    dict_list = [Count_content_word_dict, Count_title_word_dict]
    titles_token = df['title_token'].tolist()
    contents_token = df['content_token'].tolist()
    tokens = titles_token + contents_token

    # window내에서 함께 나타난 다른 토큰들의 내림차순 및 유사어로 추측되는 것을 내림차순 정렬 그리고 저장
    model = Word2Vec(sentences=tokens, size=300, window=5,
                     min_count=3, workers=4, sg=0)
    print('word2vec end')

    for j, method_dict in enumerate(dict_list):
        keyword_list = []
        for keyword in method_dict.keys():
            subkeyword_dict = dict()
            subkeyword_dict['keyword'] = keyword
            subkeyword_dict['score'] = method_dict[keyword]

            tups = find_cooccur(tokens, keyword, 4, topn)
            cooccur_list = []
            for i, tup in enumerate(tups):
                cooccur_list.append(
                    {'index': i+1, 'subkeyword': tup[0], 'cooccur_num': tup[1]})
            subkeyword_dict['cooccur'] = cooccur_list
            try:
                tups = model.wv.similar_by_word(keyword, topn=topn)
            except:
                tups = model.wv.similar_by_word(keyword.upper(), topn=topn)
            similar_list = []
            for i, tup in enumerate(tups):
                similar_list.append(
                    {'index': i+1, 'subkeyword': tup[0], 'cooccur_num': tup[1]})
            subkeyword_dict['similar'] = similar_list

            keyword_list.append(subkeyword_dict)

        if j == 0:
            with open(join(root_path, 'content_wordcloud'+'.html'), 'w', encoding='UTF-8-sig') as file:
                file.write(
                    render(json.dumps(keyword_list, ensure_ascii=False)))
            with open(join(root_path, 'content_wordcloud'+'.json'), 'w', encoding='UTF-8-sig') as file:
                file.write((json.dumps(keyword_list, ensure_ascii=False)))
        else:
            with open(join(root_path, 'title_worldcloud'+'.html'), 'w', encoding='UTF-8-sig') as file:
                file.write(
                    render(json.dumps(keyword_list, ensure_ascii=False)))
            with open(join(root_path, 'title_wordcloud'+'.json'), 'w', encoding='UTF-8-sig') as file:
                file.write((json.dumps(keyword_list, ensure_ascii=False)))
        print('made visualize file')


analyze_korean(df, './visualize')