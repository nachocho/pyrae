pyrae
=====

Perform searches against the RAE dictionary.
--------------------------------------------
**pyrae** is a simple library providing functionality to
search for words or terms in the RAE (Real Academia
Española) online dictionary.

The RAE does not provide a public API, so this library
makes HTML requests to the dle.rae.es domain and parses
the responses to assemble the search results.

Installation
------------
The easiest is to use pip, so that :

```
$ pip install pyrae
```

Usage
-----
To search for a word or term in Spanish:

```
>>> from pyrae import dle
>>> res = dle.search_by_word(word='hola')
>>> res.to_dict()
{'title': 'hola | Definición | Diccionario de la lengua española | RAE - ASALE', 'articles': [{'id': 'KYtLWBc', 'lema': {'lema': 'hola', 'index': 0, 'female_suffix': ''}, 'supplementary_info': [{'text': 'Voz expr. (Voz expresiva); cf. (confer) ingl. (inglés o inglesa) hello, al. (alemán o alemana) hallo.'}], 'definitions': [{'index': 1, 'category': {'abbr': 'interj.', 'text': 'interjección'}, 'abbreviations': [{'abbr': 'U.', 'text': 'Usado, usada, usados o usadas'}], 'sentence': {'text': 'como salutación familiar.'}, 'examples': []}, {'index': 2, 'category': {'abbr': 'interj.', 'text': 'interjección'}, 'abbreviations': [{'abbr': 'p. us.', 'text': 'poco usado o usada, poco usados o usadas'}, {'abbr': 'U.', 'text': 'Usado, usada, usados o usadas'}, {'abbr': 'U. t. repetida.', 'text': 'Usada también repetida'}], 'sentence': {'text': 'para denotar extrañeza, placentera o desagradable.'}, 'examples': []}, {'index': 3, 'category': {'abbr': 'interj.', 'text': 'interjección'}, 'abbreviations': [{'abbr': 'desus.', 'text': 'desusado, desusada, desusados o desusadas'}, {'abbr': 'Era u.', 'text': 'Era usado o usada'}], 'sentence': {'text': 'para llamar a los inferiores.'}, 'examples': []}], 'complex_forms': [], 'other_entries': []}]}
```

Other use cases offered by the RAE will be covered in future versions.