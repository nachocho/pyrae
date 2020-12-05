import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from bs4.element import Tag
from copy import deepcopy
from pyrae.util import nested_dictionary_set
from typing import List, Optional, Sequence, Union

DLE_MAIN_URL = 'https://dle.rae.es'


class FromHTML(ABC):
    """ Represents an entity that can parse HTML text.
    """
    def __init__(self, html: str):
        """ Initializes a new instance of the FromHTML class.

        :param html: HTML text.
        """
        self._soup: Optional[BeautifulSoup] = None
        self.html = html

    @property
    def html(self) -> str:
        """ Gets the HTML text used for parsing.
        """
        return self._html

    @html.setter
    def html(self, value: str):
        """ Property setter for html.

        :param value: The HTML text used for parsing.
        """
        self._html = value
        self._parse_html()

    @classmethod
    def from_html(cls, html: str):
        """ Creates an instance from HTML code if parsed successfully.
        """
        try:
            return cls(html=html)
        except Exception:
            return None

    @abstractmethod
    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        return {
            'html': self._html
        } if extended else {}

    @abstractmethod
    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        if not self._html:
            raise Exception('No HTML has been set.')
        self._soup = BeautifulSoup(self._html, 'html.parser')
        if not self._soup:
            raise Exception('Invalid HTML.')


class Abbr(FromHTML):
    """ Represents an abbreviation.
    """
    def __init__(self, html: str):
        """ Initializes a new instance of the Abbr class.

        :param html: HTML code that represents an abbreviation.
        """
        self._abbr: str = ''
        self._class: str = ''
        self._text: str = ''
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Abbr(abbr="{self._abbr}", class="{self._class}", text="{self._text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'{self._abbr} ({self._text})'

    @property
    def abbr(self) -> str:
        """ Gets the abbreviated text.
        """
        return self._abbr

    @property
    def class_(self) -> str:
        """ Gets the class of the abbreviation (if any).
        """
        return self._class

    @property
    def text(self) -> str:
        """ Gets the expanded text for the abbreviation.
        """
        return self._text

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['abbr'] = self._abbr
        if extended:
            res_dict['class'] = self._class
        res_dict['text'] = self._text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        if not self._soup.abbr:
            raise Exception('Invalid HTML.')
        self._abbr = self._soup.abbr.text
        if self._soup.abbr.has_attr('class'):
            self._class = self._soup.abbr['class'][0]
        if not self._soup.abbr.has_attr('title'):
            raise Exception('The title attribute is expected to contain the expanded text.')
        self._text = self._soup.abbr['title']


class Word(FromHTML):
    """ A single word with a corresponding ID in the RAE dictionary.
    """
    def __init__(self, html: str,
                 parent_href: str = ''):
        """ Initialize a new instance of the Word class.

        :param html: HTML code that represents a single word.
        :param parent_href: An optional HREF to complement the link if needed.
        """
        self._text: str = ''
        self._href: str = ''
        self._parent_href: str = parent_href
        self._is_active_link: bool = False
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Word(text="{self._text}", active_link={self._is_active_link}, ' \
               f'html="{self._html}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._text

    @property
    def href(self) -> str:
        """ Gets a HREF piece of the link corresponding to this word.
        """
        return self._href

    @property
    def is_active_link(self) -> bool:
        """ Gets a value indicating whether the word is part of an active link, meaning RAE rendered this
        word with an <a> element so the reader sees the word as a regular hyperlink. When not an active
        link, RAE renders the word with a <mark> element so the word is render normally but still can be
        clicked to search for its meaning.
        """
        return self._is_active_link

    @property
    def link(self) -> str:
        """ Gets the link to get results for this word.
        """
        return f'{DLE_MAIN_URL}{self._href}' if self._href else ''

    @property
    def text(self) -> str:
        """ Gets the text of the word.
        """
        return self._text

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['text'] = self._text
        if self._is_active_link:
            res_dict['link'] = self.link
        if extended:
            res_dict['is_active_link'] = self._is_active_link
            if not self._is_active_link:
                res_dict['link'] = self.link
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        if self._soup.mark:
            self._href = f"/?id={self._soup.mark['data-id']}"
            self._text = self._soup.mark.text
            return
        if self._soup.a:
            self._text = self._soup.a.text.strip()
            self._href = self._soup.a['href']
            if self._href and not self._href.startswith('/'):
                self._href = f'/{self._parent_href}{self._href}'
            self._is_active_link = True
            return
        if self._soup.span and self._soup.span['class'][0].lower() == 'u':
            self._text = self._soup.span.text
            return
        raise Exception('The HTML code cannot be parsed to a Word.')


class Sentence(FromHTML):
    """ A sentence made up of strings and instances of the Word class.
    """
    def __init__(self, html: str,
                 ignore_tags: Sequence[str] = ()):
        """ Initializes a new instance of the Sentence class.

        :param html: HTML code that can be parsed into a sentence.
        :param ignore_tags: A sequence of tags to be ignored while parsing the sentence.
        """
        self._components: List[Union[Abbr, Word, str]] = []
        self._ignore_tags: Sequence[str] = ignore_tags
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        # noinspection SpellCheckingInspection
        counts = {
            'abbrs': 0,
            'strings': 0,
            'words': 0
        }
        for component in self._components:
            if isinstance(component, Abbr):
                # noinspection SpellCheckingInspection
                counts['abbrs'] += 1
            elif isinstance(component, Word):
                counts['words'] += 1
            else:
                counts['strings'] += 1
        # noinspection SpellCheckingInspection
        return f'Sentence(text="{self.text}", abbrs={counts["abbrs"]}, words={counts["words"]}, ' \
               f'strings={counts["string"]})'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self.text

    @property
    def components(self) -> Sequence[Union[Abbr, Word, str]]:
        """ Gets the components of a sentence, can be strings or instances of the Word class.
        """
        return self._components

    @property
    def text(self) -> str:
        """ Gets the text of the sentence.
        """
        return ''.join([str(component) for component in self._components]).strip()

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['text'] = self.text
        if extended:
            res_dict['components'] = [component.to_dict(extended=extended)
                                      if not isinstance(component, str) else component
                                      for component in self._components]
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        for tag in self._soup.contents[0].children:
            if tag.name in self._ignore_tags:
                continue
            abbr = Abbr.from_html(html=str(tag))
            if abbr:
                self._components.append(abbr)
                continue
            word = Word.from_html(html=str(tag))
            if word:
                self._components.append(word)
                continue
            self._components.append(tag.get_text() if isinstance(tag, Tag) else str(tag))


class Definition(FromHTML):
    """ Represents a simple definition for a simple or complex form.
    """
    __INDEX_REGEX_STRING = r'^(?P<index>\d+).\D*$'
    # noinspection SpellCheckingInspection
    __VERB_REGEX_STRING = r'^.*verbo.*$'
    __index_re = re.compile(pattern=__INDEX_REGEX_STRING, flags=re.IGNORECASE)
    __verb_re = re.compile(pattern=__VERB_REGEX_STRING, flags=re.IGNORECASE)

    def __init__(self, html: str):
        """ Initializes a new instance of the Definition class.

        :param html: HTML code that contains a definition.
        """
        self._id: str = ''
        self._index: int = 0
        self._category: Optional[Abbr] = None
        self._first_of_category: bool = False
        self._abbreviations: List[Abbr] = []
        self._sentence: Optional[Sentence] = None
        self._examples: List[Sentence] = []
        self._raw_text: str = ''
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Definition(id="{self._id}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def abbreviations(self) -> Sequence[Abbr]:
        """ Gets a dictionary where its keys represent the abbreviations and its values, the full words.
        """
        return self._abbreviations

    @property
    def category(self) -> Abbr:
        """ Gets the abbreviation that represents the grammatical category of this definition.
        """
        return self._category

    @property
    def examples(self) -> Sequence[Sentence]:
        """ Gets a collection of sentences representing examples for this definition.
        """
        return self._examples

    @property
    def first_of_category(self) -> bool:
        """ Gets a value indicating whether the category is the first one in a block of grammatical categories.
        """
        return self._first_of_category

    @property
    def id(self) -> str:
        """ Gets the ID of the definition.
        """
        return self._id

    @property
    def index(self) -> int:
        """ Gets the ordinal index of this definition.
        """
        return self._index

    @property
    def is_adverb(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to an adverb.
        """
        return self._category.abbr == 'adv.'

    @property
    def is_adjective(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to an adjective.
        """
        return self._category.abbr == 'adj.'

    @property
    def is_noun(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a noun.
        """
        # noinspection SpellCheckingInspection
        return self._category.abbr in ('s.', 'sust.')

    @property
    def is_pronoun(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a pronoun.
        """
        return self._category.abbr == 'pron.'

    @property
    def is_verb(self) -> bool:
        """ Gets a value indicating whether the category of the definition corresponds to a verb.
        """
        # noinspection SpellCheckingInspection
        return (self.__verb_re.match(self._category.text) is not None
                or re.search(pattern='|'.join(('part.', 'ger.', 'pret.', 'fut.', 'pres.', 'infinit.')),
                             string=self._category.abbr) is not None)

    @property
    def raw_text(self) -> str:
        """ Gets the raw text of the whole HTML used for the definition.
        """
        return self._raw_text

    @property
    def sentence(self) -> Optional[Sentence]:
        """ Gets the main sentence of this definition.
        """
        return self._sentence

    @property
    def text(self) -> str:
        """ Gets the text of the main sentence of the definition.
        """
        return self._sentence.text if self._sentence else ''

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        if extended:
            res_dict['id'] = self._id
        res_dict.update({
            'index': self._index,
            'category': self._category.to_dict(extended=extended),
            'is': {
                'adjective': self.is_adjective,
                'adverb': self.is_adverb,
                'noun': self.is_noun,
                'pronoun': self.is_pronoun,
                'verb': self.is_verb
            }
        })
        if extended:
            res_dict['first_of_category'] = self._first_of_category
        res_dict.update({
            'abbreviations': [abbr.to_dict(extended=extended) for abbr in self._abbreviations],
            'sentence': self._sentence.to_dict(extended=extended),
            'examples': [ex.to_dict(extended=extended) for ex in self._examples]
        })
        if extended:
            res_dict['raw_text'] = self._raw_text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        if not self._soup.p or not self._soup.p.has_attr('class'):
            raise Exception('Invalid HTML tag passed for a definition.')
        if self._soup.p['class'][0].lower()[0] not in ['j', 'm']:
            raise Exception('Paragraph class does not correspond to a definition.')
        self._raw_text = self._soup.get_text()
        if self._soup.p.has_attr('id'):
            self._id = self._soup.p['id']
        for tag in self._soup.p.children:
            if not isinstance(tag, Tag):
                continue
            tag_class = tag['class'][0].lower() if tag.has_attr('class') else ''
            if tag.name == 'span':
                # noinspection SpellCheckingInspection
                if tag_class == 'n_acep':
                    # The index
                    match = self.__index_re.match(string=tag.text)
                    if match:
                        self._index = int(match['index'])
                elif tag_class == 'h':
                    # An example
                    self._examples.append(Sentence(html=str(tag)))
            elif tag.name == 'abbr':
                if not self._category:
                    # The first abbr is the category
                    self._category = Abbr(html=str(tag))
                    self._first_of_category = tag_class == 'd'
                else:
                    # Another abbr to complement the main sentence of the definition
                    self._abbreviations.append(Abbr(html=str(tag)))
        self._sentence = Sentence(html=str(self._soup.p), ignore_tags=('abbr', 'span'))


class EntryLema(FromHTML):
    """ Represents a lema for a simple entry.
    """
    PROCESSING_TAGS = {
        'lema': {
            'tag': 'p',
            'class': 'k'
        }
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the EntryLema class.

        :param html: HTML code that contains a lema entry.
        """
        self._id: str = ''
        self._is_foreign: bool = False
        self._lema: str = ''
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Lema(id="{self._id}", lema="{self._lema}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._lema

    @property
    def id(self) -> str:
        """ Gets the ID (if any) associated to this lema.
        """
        return self._id

    @property
    def is_foreign(self) -> bool:
        """ Gets a value indicating whether the lema word is of foreign origin or of a non-adapted latin origin.
        """
        return self._is_foreign

    @property
    def lema(self) -> str:
        """ Gets the lema word.
        """
        return self._lema

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['lema'] = self._lema
        if extended:
            res_dict.update({
                'id': self._id,
                'is_foreign': self._is_foreign
            })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        tag = self._soup.find(name=self.PROCESSING_TAGS['lema']['tag'])
        if not tag or not tag.has_attr('class') or tag['class'][0].lower()[0] != self.PROCESSING_TAGS['lema']['class']:
            raise Exception('Invalid HTML.')
        if tag.has_attr('id'):
            self._id = tag['id']
        self._lema = tag.get_text()
        self._is_foreign = tag.find(name='i') is not None


class Entry(FromHTML):
    """ Represents an entry, which is a full group of definitions for a word or word combination.
    """
    _LEMA_CLASS = EntryLema
    PROCESSING_TAGS = {
        'supplementary_info': {
            'tag': 'p',
            'class': 'n'
        },
        'definition': {
            'tag': 'p',
            'class': 'm'
        }
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Entry class.

        :param html: HTML code that contains a simple entry.
        """
        self._lema: Optional[EntryLema] = None
        self._supplementary_info: List[Sentence] = []
        self._definitions: List[Definition] = []
        self._raw_text: str = ''
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Entry(lema="{self.lema.lema}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def definitions(self) -> List[Definition]:
        """ Gets a collection of definitions (simple forms) for the lema word.
        """
        return self._definitions

    @property
    def lema(self) -> EntryLema:
        """ Gets the lema for this entry.
        """
        return self._lema

    @property
    def raw_text(self) -> str:
        """ Gets the raw text of the whole HTML used for the Article.
        """
        return self._raw_text

    @property
    def supplementary_info(self) -> List[Sentence]:
        """ Gets a collection (if any) of supplementary information about the lema word.
        """
        return self._supplementary_info

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict.update({
            'lema': self.lema.to_dict(extended=extended),
            'supplementary_info': [s.to_dict(extended=extended) for s in self._supplementary_info],
            'definitions': [definition.to_dict(extended=extended) for definition in self._definitions]
        })
        if extended:
            res_dict['raw_text'] = self._raw_text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        self._process_entry(entry_tag=self._soup.contents[0])

    def _process_entry(self, entry_tag: Tag):
        """ Processes the whole entry.

        :param entry_tag: A tag instance.
        """
        if not entry_tag:
            return
        for tag in entry_tag.children:
            if not isinstance(tag, Tag):
                continue
            if not self._lema:
                self._lema = self._LEMA_CLASS.from_html(html=str(tag))
                if self._lema:
                    continue
            class_letter = tag['class'][0].lower()[0] if tag.has_attr('class') else ''
            if (tag.name == self.PROCESSING_TAGS['supplementary_info']['tag']
                    and class_letter == self.PROCESSING_TAGS['supplementary_info']['class']):
                self._supplementary_info.append(Sentence(html=str(tag)))
            elif (tag.name == self.PROCESSING_TAGS['definition']['tag']
                    and class_letter == self.PROCESSING_TAGS['definition']['class']):
                self._definitions.append(Definition(html=str(tag)))
        if not self._lema:
            raise Exception('Could not process lema from the given HTML.')
        self._raw_text = self._soup.get_text()


class ArticleLema(EntryLema):
    """ Represents a lema for an article.
    """
    LEMA_REGEX_STRING = r'^(?P<lema>[^\W\d_]+)(?P<index>\d+)?(?:,\s+(?P<female_suffix>\w+))?(?:\s+\((' \
                        r'?P<related>\w+)\))?$'
    lema_re = re.compile(pattern=LEMA_REGEX_STRING, flags=re.IGNORECASE)
    PROCESSING_TAGS = deepcopy(EntryLema.PROCESSING_TAGS)
    PROCESSING_TAGS['lema']['tag'] = 'header'
    PROCESSING_TAGS['lema']['class'] = 'f'

    def __init__(self, html: str):
        """ Initializes a new instance of the ArticleLema class.

        :param html: HTML code that contains an a lema for an article.
        """
        self._index: int = 0
        self._female_suffix: str = ''
        super().__init__(html=html)

    @property
    def female_suffix(self) -> str:
        """ Gets the female form suffix of this lema (if any).
        """
        return self._female_suffix

    @property
    def index(self) -> int:
        """ Gets the ordinal index of the article's lema.
        """
        return self._index

    @property
    def is_acronym(self) -> bool:
        """ Gets a value indicating whether the lema word is an acronym.
        """
        return self._lema.isupper()

    @property
    def is_prefix(self) -> bool:
        """ Gets a value indicating whether the lema word is a prefix.
        """
        return self._lema.startswith('-')

    @property
    def is_suffix(self) -> bool:
        """ Gets a value indicating whether the lema word is a suffix.
        """
        return self._lema.endswith('-')

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict.update({
            'index': self._index,
            'female_suffix': self._female_suffix
        })
        if extended:
            res_dict.update({
                'is_acronym': self.is_acronym,
                'is_prefix': self.is_prefix,
                'is_suffix': self.is_suffix,
            })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        match = self.lema_re.match(string=self._lema)
        if match:
            self._lema = match['lema']
            if match['index']:
                self._index = int(match['index'])
            if match['female_suffix']:
                self._female_suffix = match['female_suffix'].strip()


class Conjugation(FromHTML):
    """ Represents the conjugation table for a verb.
    """
    # noinspection SpellCheckingInspection
    CONJUGATION_BASE_DICT = {
        'Formas no personales': {
            'Infinitivo': '',
            'Gerundio': '',
            'Participio': ''
        },
        'Indicativo': {
            'Presente': {},
            'Copretérito': {},
            'Pretérito': {},
            'Futuro': {},
            'Pospretérito': {}
        },
        'Subjuntivo': {
            'Presente': {},
            'Futuro': {},
            'Copretérito': {}
        },
        'Imperativo': {}
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Conjugation class.

        :param html: HTML code that contains the table of a conjugation.
        """
        self._id: str = ''
        self._verb: str = ''
        self._conjugations: dict = {}
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Conjugation(id="{self._id}", verb="{self._verb}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return str(self._conjugations)

    @property
    def conjugations(self) -> dict:
        """ Gets the conjugations of a verb.
        """
        return self._conjugations

    @property
    def id(self) -> str:
        """ Gets the ID that matches the conjugation with an article.
        """
        return self._id

    @property
    def verb(self) -> str:
        """ Gets the verb (in infinitive form) of the conjugations.
        """
        return self._verb

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        if extended:
            res_dict['id'] = self._id
        res_dict.update({
            'verb': self._verb,
            'conjugations': self._conjugations
        })
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        # noinspection SpellCheckingInspection
        if not self._soup.div or not self._soup.div.has_attr('id') or self._soup.div['id'] != 'conjugacion':
            raise Exception('Invalid HTML for a conjugations table.')
        id_tag = self._soup.div.find(name='article')
        if id_tag and id_tag.has_attr('id'):
            # noinspection SpellCheckingInspection
            self._id = f"conjugacion{id_tag['id']}"
        header_tag = self._soup.div.find(name='header')
        if header_tag:
            verb_tag = header_tag.find(name='b')
            if verb_tag:
                self._verb = verb_tag.text
        table_tag = self._soup.div.find(name='table', class_='cnj')
        if table_tag:
            self._conjugations = deepcopy(self.CONJUGATION_BASE_DICT)
            sub_type_keys_dict = {}
            verb_separators = (' u ' if self._verb.startswith('o') else ' o ', ' / ')
            type_key = ''
            for row_tag in table_tag.children:
                for cell_index, cell_tag in enumerate(row_tag.contents):
                    if cell_index < 3:
                        continue
                    if cell_tag.name == 'th':
                        header_text = cell_tag.get_text()
                        if header_text in self._conjugations.keys():
                            type_key = header_text
                            sub_type_keys_dict = {}
                            continue
                        # noinspection SpellCheckingInspection
                        sub_type_key = next((key for key in self._conjugations[type_key].keys()
                                             if re.search(pattern=f'/ {key}' if key != 'Presente' else key,
                                                          string=header_text,
                                                          flags=re.IGNORECASE)), '')
                        sub_type_keys_dict[cell_index] = sub_type_key
                        continue
                    if cell_tag.name == 'td':
                        persona_tag: Optional[Tag] = row_tag.contents[2] if cell_index >= 3 else None
                        persona = str(persona_tag.string) if persona_tag and persona_tag.string is not None else ''
                        keys = [type_key]
                        if sub_type_keys_dict:
                            keys.append(sub_type_keys_dict[cell_index])
                        verbs = cell_tag.get_text()
                        for verb_separator in verb_separators:
                            if verb_separator in verbs:
                                verbs = verbs.split(verb_separator)
                                if len(verbs) == 1:
                                    verbs = verbs[0]
                                break
                        data_value = {persona: verbs} if persona else verbs
                        nested_dictionary_set(dictionary=self._conjugations, keys=keys, value=data_value)


class Article(Entry):
    """ Represents an article, which contains simple entries and complex forms.
    """
    _LEMA_CLASS = ArticleLema
    PROCESSING_TAGS = deepcopy(Entry.PROCESSING_TAGS)
    PROCESSING_TAGS['definition']['class'] = 'j'
    PROCESSING_TAGS['other'] = {
        'tag': 'p',
        'class': 'l'
    }

    def __init__(self, html: str):
        """ Initializes a new instance of the Article class.

        :param html: HTML code that contains a definition.
        """
        self._id: str = ''
        self._lema: Optional[ArticleLema] = None
        self._complex_forms: List[Entry] = []
        self._other_entries: List[Word] = []
        self.conjugations: Optional[Conjugation] = None
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'Article(id="{self._id}", lema="{self.lema.lema}", raw_text="{self._raw_text}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._raw_text

    @property
    def complex_forms(self) -> Sequence[Entry]:
        """ Gets a sequence of entries representing complex forms of the lema word.
        """
        return self._complex_forms

    @property
    def id(self) -> str:
        """ Gets the ID of the article.
        """
        return self._id

    @property
    def is_verb(self) -> bool:
        """ Gets a value indicating whether the article has conjugations or an entry that is a verb.
        """
        return self.conjugations is not None or any(definition for definition in self.definitions
                                                    if definition.is_verb)

    @property
    def lema(self) -> ArticleLema:
        """ Gets the lema for this article.
        """
        return self._lema

    @property
    def other_entries(self) -> Sequence[Word]:
        """ Gets a sequence of words representing related entries with corresponding links to fetch their results.
        """
        return self._other_entries

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super(Entry, self).to_dict(extended=extended)
        res_dict.update({
            'id': self._id,
            'lema': self.lema.to_dict(extended=extended),
            'supplementary_info': [s.to_dict(extended=extended) for s in self._supplementary_info],
            'is': {
              'verb': self.is_verb
            },
            'definitions': [definition.to_dict(extended=extended) for definition in self._definitions],
            'complex_forms': [complex_form.to_dict(extended=extended) for complex_form in self._complex_forms],
            'other_entries': [entry.to_dict(extended=extended) for entry in self._other_entries]
        })
        if self.conjugations:
            res_dict['conjugations'] = self.conjugations.to_dict(extended=extended)
        if extended:
            res_dict['raw_text'] = self._raw_text
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super(Entry, self)._parse_html()
        if not self._soup.article or not self._soup.article.header:
            raise Exception('Invalid HTML.')
        if self._soup.article.has_attr('id'):
            self._id = self._soup.article['id']
        lema_entry_tag = Tag(name='lema_entry')
        complex_form_tag: Optional[Tag] = None
        complex_forms_tags: List[Tag] = []
        for tag in self._soup.article.children:
            if tag.name == ArticleLema.PROCESSING_TAGS['lema']['tag']:
                lema_entry_tag.append(tag)
            elif tag.name == 'p':
                class_letter = tag['class'][0].lower()[0]
                if class_letter == self.PROCESSING_TAGS['definition']['class']:
                    lema_entry_tag.append(tag)
                elif class_letter == EntryLema.PROCESSING_TAGS['lema']['class']:
                    complex_form_tag = Tag(name='complex_form_entry')
                    complex_forms_tags.append(complex_form_tag)
                    complex_form_tag.append(tag)
                elif class_letter == self.PROCESSING_TAGS['supplementary_info']['class']:
                    if complex_form_tag is not None:
                        complex_form_tag.append(tag)
                    else:
                        lema_entry_tag.append(tag)
                elif (class_letter == super().PROCESSING_TAGS['supplementary_info']['class']
                      or class_letter == super().PROCESSING_TAGS['definition']['class']):
                    complex_form_tag.append(tag)
                elif class_letter == self.PROCESSING_TAGS['other']['class']:
                    self._other_entries.append(Word(html=str(tag), parent_href=self._id))
        self._process_entry(entry_tag=lema_entry_tag)
        for complex_form_tag in complex_forms_tags:
            self._complex_forms.append(Entry(html=str(complex_form_tag)))
        self._raw_text = self._soup.get_text()


class SearchResult(FromHTML):
    """ Represents the result of a search.
    """
    __INDEX_REGEX_STRING = r'^(?P<lema>\D*)(?P<index>\d+)$'
    __index_re = re.compile(pattern=__INDEX_REGEX_STRING, flags=re.IGNORECASE)

    def __init__(self, html: str):
        """ Initializes a new instance of the SearchResult class.

        :param html: HTML code that contains a definition.
        """
        self._articles: List[Article] = []
        self._title: str = ''
        self._canonical: str = ''
        self._meta_description: str = ''
        self._related_entries: dict = {}
        super().__init__(html=html)

    def __repr__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return f'SearchResult(title="{self._title}", canonical="{self._canonical}", ' \
               f'meta_description="{self._meta_description}")'

    def __str__(self):
        """ Gets the string representation of the object instance.

        :return: The string representation of the object instance.
        """
        return self._meta_description

    @property
    def articles(self) -> Sequence[Article]:
        """ Gets a sequence with all articles contained in the search result.
        """
        return self._articles

    @property
    def canonical(self) -> str:
        """ Gets the canonical link that returns this search result.
        """
        return self._canonical

    @property
    def meta_description(self) -> str:
        """ Gets the full one-line description of the search result.
        """
        return self._meta_description

    @property
    def related_entries(self) -> dict:
        """ Gets related entries (if any) in case no articles are returned from the search.
        """
        return self._related_entries

    @property
    def title(self) -> str:
        """ Gets the title of the search result.
        """
        return self._title

    def to_dict(self, extended: bool = False) -> dict:
        """ Gets a dictionary representation of this instance.

        :param extended: Flag indicating whether extended or basic information is output in the dictionary.
        """
        res_dict = super().to_dict(extended=extended)
        res_dict['title'] = self._title
        if extended:
            res_dict.update({
                'canonical': self._canonical,
                'meta_description': self._meta_description
            })
        if self._articles:
            res_dict['articles'] = [article.to_dict(extended=extended) for article in self._articles]
        elif self._related_entries:
            res_dict['related_entries'] = {k: [w.to_dict(extended=extended) for w in v]
                                           for k, v in self._related_entries.items()}
        return res_dict

    def _parse_html(self):
        """ Parses the contents of the HTML.
        """
        super()._parse_html()
        canonical_tag = self._soup.find(name='link', attrs={'ref': 'canonical'})
        if canonical_tag:
            self._canonical = canonical_tag['href']
        if self._soup.title:
            self._title = str(self._soup.title.text)
        meta_description_tag = self._soup.find(name='meta', attrs={'name': 'description'})
        if meta_description_tag:
            self._meta_description = meta_description_tag['content']
        # noinspection SpellCheckingInspection
        results_div_tag = self._soup.find(name='div', attrs={'id': 'resultados'})
        if results_div_tag:
            for article_tag in results_div_tag.find_all(name='article', recursive=False):
                article = Article(html=str(article_tag))
                self._articles.append(article)
                # noinspection SpellCheckingInspection
                conjugations_tag = article_tag.find_next_sibling(name='div', attrs={'id': 'conjugacion'})
                if conjugations_tag:
                    conjugations = Conjugation(html=str(conjugations_tag))
                    a_tag = article_tag.find(name='a', class_=re.compile('^e'))
                    if a_tag and a_tag.has_attr('href') and a_tag['href'] == f'#{conjugations.id}':
                        article.conjugations = conjugations
            for related_res in results_div_tag.find_all(name='div', class_='n1', recursive=False):
                if not related_res.a:
                    continue
                match = ArticleLema.lema_re.match(related_res.get_text())
                if not match:
                    continue
                if match['related'] in self._related_entries:
                    self._related_entries[match['related']].append(Word(html=str(related_res.a)))
                else:
                    self._related_entries[match['related']] = [Word(html=str(related_res.a))]
