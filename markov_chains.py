import re
from collections import defaultdict, Counter
import itertools
import os
import sys
import random
import cPickle

PUNCTUATION = '.,:;?!'

spec_pattern = re.compile('([^\'\sA-Za-z{}]|_)+'.format(PUNCTUATION))
newline_pattern = re.compile('(\n)+')


def normalize_text(text):
    '''
    This function turns all letters to lowercase and
    removes all strange symbols
    except punctuation marks that are featuring in PUNCTUATION
    Moreover, however many newlines are replaced by a single "#" symbol
    '''
    text = re.sub('[{}]\W'.format(PUNCTUATION),
                  separate_punctuation, text.lower())
    # The next two lines are here to cope with some sort of strange
    # punctuation occuring in Pratchett's texts
    text = text.replace('\xe2\x80\x99', '\'')
    text = text.replace('\xe2\x80\xa6', ' ')
    text = spec_pattern.sub('', text)
    text = newline_pattern.sub(' # ', text)
    return text


def separate_quotes(text):
    '''
    Turns unary quote to binary quote
    provided it is not apostrophe, i.e.
    it is not surrounded by alphanumerics
    '''
    text = text.replace('.\'', '.').replace(',\'', ',')
    return (text[0] + ''.join(['"'
            if ((c == '\'') and
                ((not text[i].isalnum()) or (not text[i + 2].isalnum())))
                    else c for i, c in enumerate(text[1:-1])]) + text[-1])


def separate_punctuation(matchobj):
    '''
    Separates punctuation marks from preceding word
    '''
    return ' ' + matchobj.group()


class MarkovGenerator(object):

    def __init__(self):
        # Counter for words following a point
        self.first_words = []
        # Counter for triplets of words
        self.two_word_counter = defaultdict(Counter)

    def add_document(self,  file_path, report=False):
        '''
        Adds document to  collection and gathers statistics
        file_path - full path to the file containing text
        report - indicates whether we need to print filename
                 (left for debugging)
        '''
        document = open(file_path).read()
        if report:
            print file_path.split('\\')[-1]
        normalized_document = normalize_text(separate_quotes(document))
        words = normalized_document.split()
        for u, v, w in itertools.izip(words, itertools.islice(words, 1, None),
                                      itertools.islice(words, 2, None)):
            self.two_word_counter[u+'@'+v].update({w: 1})
            if u == '.' and v != '#':
                self.first_words.append(v)

    def add_folder(self, rootdir, report=False):
        '''
        Adds all files from a given folder to the collection
        '''
        for root, subdirs, files in os.walk(rootdir):
            for a_file in files:
                file_path = os.path.join(root, a_file)
                self.add_document(file_path, report=report)

    def clear_stats(self):
        '''
        Allows you to start erevything anew
        '''
        self.first_words = []
        self.two_word_counter = defaultdict(Counter)

    def dump(self):
        '''
        Saves the statistics to disc.
        At least provided your computer has enough memory...
        '''
        output = open(r'stats_startings.txt', 'wb')
        cPickle.dump(self.first_words, output)
        output.close()

        output = open(r'stats_triples.txt', 'wb')
        cPickle.dump(self.two_word_counter, output)
        output.close()

    def draw_first_word(self):
        '''
        generates the very first word of the text
        '''
        i = random.randrange(len(self.first_words))
        first_word = next(itertools.islice(self.first_words, i, None))
        return first_word

    def draw_second_word(self, first_word):
        '''
        generates the second word of the text
        '''
        possible_words =\
            list(self.two_word_counter['.'+'@'+first_word].elements())
        i = random.randrange(len(possible_words))
        return next(itertools.islice(possible_words, i, None))

    def draw_next_word(self, previous_word, this_word):
        '''
        generates the next word, based upon two preceding words
        '''
        possible_words =\
            list(self.two_word_counter[previous_word+'@'+this_word].elements())
        i = random.randrange(len(possible_words))
        return next(itertools.islice(possible_words, i, None))

    def generate(self, max_length, output_file):
        '''
        generates a text consisting of full sentences containing at least
        as many words as max_length. It may contain more words since generation
        may only stop after a sentence ended
        '''
        my_text = []
        first_word = self.draw_first_word()
        my_text.append(first_word.capitalize())

        this_word = self.draw_second_word(first_word)
        if this_word in PUNCTUATION:
            my_text[-1] = my_text[-1] + this_word
        else:
            my_text.append(this_word)
        previous_word = first_word
        text_length = 2

        if this_word in '.!?':
            is_starter = True
        else:
            is_starter = False

        for t in itertools.count():
            for s in itertools.count():
                next_word = self.draw_next_word(previous_word, this_word)
                previous_word = this_word
                this_word = next_word
                text_length += 1
                if next_word == '#':
                    is_starter = True
                    my_text.append('\n')
                elif next_word in PUNCTUATION:
                    my_text[-1] = my_text[-1] + this_word
                    if next_word in '.!?':
                        is_starter = True
                        break
                else:
                    if is_starter:
                        is_starter = False
                        my_text.append(this_word.capitalize())
                    else:
                        my_text.append(this_word)
            if text_length > max_length:
                break
        output = open(output_file, 'w')
        output.write(' '.join(my_text))
        output.close()


def main():
    rootdir = sys.argv[1]
    output_file = sys.argv[2]
    text_length = sys.argv[3]
    markov_generator = MarkovGenerator()
    markov_generator.add_folder(rootdir)

    my_generator.generate(text_length, output_file)


if __name__ == '__main__':
    main()
