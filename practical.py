"""
PRACTICAL 1
Oana-Maria CAMBURU
After a naive implementation of the parsing where we assume all the tokens are of the form "word/POS" we saw that our code failled for 3 types of exceptions:
1. Typo: "Chiat\/NNP"
2. Multiple escaped backslashes: "a\/k\/a/IN" or "7\/8/CD"
3. Mutiple POS associated separated by "|"
4. Initiales linked with &: S*/NNP&P/NN, AT*/NNP&T/NN
We treated the last case manually since it only appears 2 times. 
We also check each time that our pos are in the Brill tags, which guarantees that our splits were correct. The only difference I had was the double quotes were replaced by two single quotes. I replaced that manually in or tagging to match the Brill tags.
We give here the final code handeling these exceptions.
"""

import glob
import sys
import numpy
import operator

brill_tags = [
	    u"CC",  # Coordinating conjunction
	    u"CD",  # Cardinal number
	    u"DT",  # Determiner
	    u"EX",  # Existential there
	    u"FW",  # Foreign word
	    u"IN",  # Preposition/subord. conjunction
	    u"JJ",  # Adjective
	    u"JJR",  # Adjective, comparative
	    u"JJS",  # Adjective, superlative
	    u"LS",  # List item marker
	    u"MD",  # Modal
	    u"NN",  # Noun, singular or mass
	    u"NNS",  # Noun, plural
	    u"NNP",  # Proper noun, singular
	    u"NNPS",  # Proper noun, plural
	    u"PDT",  # Predeterminer
	    u"POS",  # Possessive ending
	    u"PRP",  # Personal pronoun
	    u"PRP$",  # Possessive pronoun
	    u"RB",  # Adverb
	    u"RBR",  # Adverb, comparative
	    u"RBS",  # Adverb, superlative
	    u"RP",  # Particle
	    u"SYM",  # Symbol (mathematical or scientific)
	    u"TO",  # to
	    u"UH",  # Interjection
	    u"VB",  # Verb, base form
	    u"VBD",  # Verb, past tense
	    u"VBG",  # Verb, gerund/present participle
	    u"VBN",  # Verb, past participle
	    u"VBP",  # Verb, non-3rd ps. sing. present
	    u"VBZ",  # Verb, 3rd ps. sing. present
	    u"WDT",  # wh-determiner
	    u"WP",  # wh-pronoun
	    u"WP$",  # Possessive wh-pronoun
	    u"WRB",  # wh-adverb
	    u"#",  # Pound sign
	    u"$",  # Dollar sign
	    u".",  # Sentence-final punctuation
	    u",",  # Comma
	    u":",  # Colon, semi-colon
	    u"(",  # Left bracket character
	    u")",  # Right bracket character
	    u"\"",  # Straight double quote
	    u"`",  # Left open single quote
	    u"\"",  # Left open double quote
	    u"'",  # Right close single quote
	    u"\"",  # Right close double quote 
	]
K = len(brill_tags)

folds = 10 # for cross-validation. Don't change this!

all_sentences = [''] * folds # treat each of the 10 files as a sentence. keeps track of the sentences in each file without pos-es
previous_POSes = ['.'] # first time when we read a file begins with a new sentence, so it's as if we had a '.' before

all_POSes = [0] * folds
for i in range(folds):
    all_POSes[i] = []

parsed = [0] * folds # keeps track of the files parsed so that we don't overwrite the sentences and posses


def parse_file(file_number):
    global previous_POSes   
    
    counts_probabilities = {}
    counts_transitions = {}
    counts_POS = {}
    
    # add 1-smoothing initialization
    counts_POS["START"] = K
    for tag1 in brill_tags:
        counts_POS[tag1] = K
        counts_transitions[("START", tag1)] = 1
        for tag2 in brill_tags:
            counts_transitions[(tag1, tag2)] = 1
    
    file_name = 'data/x0' + str(file_number) + '.POS'
    print file_name
    f = open(file_name, 'r')
    
    for line in f:  # read each line from the input file
        if '.' in previous_POSes: # every sentence is ended by the POS '.'
            previous_POSes = ["START"]	# mark new sentence	 # REMARK: we could remove the "START" symbol and only use the "." but for purposes of clearness we keep the START symbol
        if line != "\n":  # that is not empty
            tokens = line.split()  # split by words with their annotation
            for token in tokens:
                if "/" in token:  # some tokens might not be word/POS, for example "[" or '===='
                    if "\/" in token: 
                        if token != "Chiat\/NNP": # we ignore this word because it is a typo and we don't know what that actually meant
                            # proceed with the other type of exeptions that are of the form for example "a\/k\/a/POS"
                            split = token.split("\/")
                            s = "\/"
                            word = s.join(split[0:len(split) - 1]) + s + split[len(split) - 1].split("/")[0]  # we now combine back "a\/k\/a"
                            POS = split[len(split) - 1].split("/")[1].split("|")  # take the POS as the second part after "\" in '8/CD', that is 'CD' and split by "|" to be consistent
                    elif token == "S*/NNP&P/NN":
                        word = "S&P"
                        POS = ["NNP", "NN"]
                    elif token == "AT*/NNP&T/NN":
                        word = "AT&T"
                        POS = ["NNP", "NN"]
                    else:  # normal form word/POS
                        split = token.split("/")   # simply split between word and POS by "/"
                        word = split[0].lower()    # current word, we lower case all words so that we don't treat the same word as two different in case it appears at the begining of sentence
                        POS = split[1].split("|")  # list of the possible POS-es(separated by "|")
                    # Now that we treated the possible exceptions and have a clear view of the word and its possible multiple POSes we insert these into the counts_probabilities dictionary
                    current_POSes = [];                    
                    if counts_probabilities.has_key(word):  # if word already encountered
                        val = counts_probabilities[word]  # POS with which the word was encountered
                        for pos in POS:  # for all the POS listed in the current annotation
                            if pos == "``" or pos == "''" or pos == "''\n" or pos == "``\n": # replace '' and `` with double quotes so that it matches brill tagset; eliminate end of line
                                pos="\""
                            if pos[len(pos)-1] == "\n":
                                pos=pos[0:len(pos)-1]
                            if pos not in brill_tags:
                                print "ERROR  " + pos + " in " + token
                                sys.exit() # the program will stop executing if we detect a POS that is not in the brill_tags
                            elif val.has_key(pos):  # if the word has already been viewed with this POS
                                val[pos] += 1
                            else:
                                val[pos] = 1
                            current_POSes.append(pos)
                    else:  # new word
                        for pos in POS:
                            if pos == "``" or pos == "''" or pos == "''\n" or pos == "``\n": # replace these exeptional tags with the one in the brill tagset
                                pos="\""
                            if pos[len(pos)-1] == "\n":
                                pos=pos[0:len(pos)-1]
                            if pos not in brill_tags:
                                print "ERROR  " + pos + " in " + token
                                sys.exit() # the program will stop executing if we detect a POS that is not in the brill_tags
                            counts_probabilities[word] = {pos: 1}
                            current_POSes.append(pos)
                    all_POSes.append(current_POSes)
                    # Compute counts for transitions    
                    for previous_POS in previous_POSes:
                        for current_POS in current_POSes:
                            counts_transitions[(previous_POS, current_POS)] += 1
                            counts_POS[previous_POS] += 1
                    previous_POSes = current_POSes[:]
                    # Add word to all_sentences[file_number] with its associated posses if we haven't done that yet (we will pass through each file 10 times do to cross validation but we only need to parse the file once)
                    if not parsed[file_number]:
                        all_sentences[file_number] += ' ' + word
                        all_POSes[file_number].append(current_POSes)
    
    parsed[file_number] = 1 # mark that we already parsed this file
    return counts_probabilities, counts_transitions, counts_POS


def computeWordProbabilitiesAndTransitions(exclude_file_number):

    category_probabilities = {}
    transitions_probabilities = {}

    for file_number in range(10):
        if file_number != exclude_file_number:
            counts_probabilities, counts_transitions, counts_POS = parse_file(file_number)
            
    print "All files parsed correctly and the POS tags are in Brill tags! :) "
    for word, pos in counts_probabilities.items():
        sum = 0;
        proba = {};
        for pos_key, count in pos.items():
	        sum += count
        for pos_key, count in pos.items():
	        proba[pos_key] = count/float(sum)
        category_probabilities[word] = proba

    for key, val in counts_transitions.items():
        transitions_probabilities[key] = val/float(counts_POS[key[0]])

    return category_probabilities, transitions_probabilities

def Viterbi_Log(sentence, category_probabilities, transitions_probabilities):
    words = sentence.lower().split() # lower case because that's what we did when we indexed the words
    print words[0:5]
    N = len(words)
    score = [[-float("inf") for x in range(N)] for x in range(K)]
    back = [[0 for x in range(N)] for x in range(K)]

    # Initialise
    first_word = words[0]
    for i in range(K):
        tag = brill_tags[i]
        if category_probabilities.has_key(first_word): 
            if category_probabilities[first_word].has_key(tag):
                score[i][0] = numpy.log(category_probabilities[first_word][tag] * transitions_probabilities[("START", tag)])
        else: # unkown word
            score[i][0] = numpy.log(1/float(K) * transitions_probabilities[("START", tag)])
    
    # Induction
    for j in range(1, N):
        word = words[j]
        for i in range(K):
            tag_i = brill_tags[i]
            max_so_far = -float("inf")
            arg_max = -1
            for k in range(K):
                tag_k = brill_tags[k]
                val = score[k][j-1] + numpy.log(transitions_probabilities[(tag_k, tag_i)])
                if category_probabilities.has_key(word):
                    if category_probabilities[word].has_key(tag_i):
                        val += numpy.log(category_probabilities[word][tag_i])
                    else: # word have never had this pos
                        val = -float("inf") # log(0)
                else: # unknown word
                    val += numpy.log(1/float(K))
                if max_so_far < val:
                    max_so_far = val
                    arg_max = k
            score[i][j] = max_so_far
            back[i][j] = arg_max

    # Back tracing the best tagging
    t = [0] * N
    max_so_far = -float('inf')
    for i in range(K):
        if max_so_far < score[i][N-1]:
            max_so_far = score[i][N-1]
            t[N-1] = i
    for i in range(N-2, -1, -1):
        t[i] = back[t[i+1]][i+1]
    tags = ['a'] * N
    for i in range(N):
        tags[i] = brill_tags[t[i]]
    return tags

def Viterbi(sentence, category_probabilities, transitions_probabilities):
    words = sentence.lower().split() # lower case because that's what we did when we indexed the words
    N = len(words)
    score = [[0 for x in range(N)] for x in range(K)]
    back = [[0 for x in range(N)] for x in range(K)]
    
    # Initialise
    first_word = words[0]
    for i in range(K):
        tag = brill_tags[i]
        if category_probabilities.has_key(first_word): 
            if category_probabilities[first_word].has_key(tag):
                score[i][0] = category_probabilities[first_word][tag] * transitions_probabilities[("START", tag)]
        else: # unkown word
            score[i][0] = 1/float(K) * transitions_probabilities[("START", tag)]
    
    # Induction
    for j in range(1, N):
        word = words[j]
        for i in range(K):
            tag_i = brill_tags[i]
            max_so_far = -float("inf")
            arg_max = -1
            for k in range(K):
                tag_k = brill_tags[k]
                val = score[k][j-1] * transitions_probabilities[(tag_k, tag_i)]
                if category_probabilities.has_key(word):
                    if category_probabilities[word].has_key(tag_i):
                        val *= category_probabilities[word][tag_i]
                    else: # word have never had this pos
                        val = 0
                else: # unknown word
                    val *= 1/float(K)
                if max_so_far < val:
                    max_so_far = val
                    arg_max = k
            score[i][j] = max_so_far
            back[i][j] = arg_max

    # Back tracing the best tagging
    t = [0] * N
    max_so_far = -1
    for i in range(K):
        if max_so_far < score[i][N-1]:
            max_so_far = score[i][N-1]
            t[N-1] = i
    for i in range(N-2, -1, -1):
        t[i] = back[t[i+1]][i+1]
    tags = ['a'] * N
    for i in range(N):
        tags[i] = brill_tags[t[i]]
    return tags


# Uncomment for a more complex sentence
sentence = 'Once she did so , the big-souled German maestro with the shaky nerves who so often cancels offered a limpid , flowing performance that in its unswagged and unswaggering approach was totally at odds with the staging .'

#sentence = 'she can go .'
#print sentence

#sentence = "she is cool cool cool go there ."

category_probabilities, transitions_probabilities = computeWordProbabilitiesAndTransitions('')
predicted_tags = Viterbi(sentence, category_probabilities, transitions_probabilities)
predicted_tags_log = Viterbi_Log(sentence, category_probabilities, transitions_probabilities)

print sentence
print predicted_tags
print predicted_tags_log

accuracy = [0] * folds
counts = [0] * folds

def cross_validation():
    for file_number in range(folds): 
        category_probabilities, transitions_probabilities = computeWordProbabilitiesAndTransitions(file_number)
        predicted_tags = Viterbi_Log(all_sentences[file_number], category_probabilities, transitions_probabilities)
        #print predicted_tags
        # check predicted tags against the true values
        for predicted_tag, true_tags in zip(predicted_tags, all_POSes[file_number]):
            if predicted_tag in true_tags:
                counts[file_number] += 1
        accuracy[file_number] =  counts[file_number]/float(len(predicted_tags))
        print '------'
        g = open('sentence' + str(file_number), 'w')
        g.write(all_sentences[file_number])
        g.close()
        g = open('prediction' + str(file_number), 'w')
        g.write(str(predicted_tags))
        g.close()
        g = open('trueValues' + str(file_number), 'w')
        g.write(str(all_POSes[file_number]))
        g.close()
        words = all_sentences[file_number].split()
        print 'true tags'
        print all_POSes[file_number][0:10]
        print 'pred tags'
        print predicted_tags[0:10]
        print file_number
        print len(words)
        print len(predicted_tags)
        print len(all_POSes[file_number])
        print counts[file_number]
        print accuracy[file_number]
        print '------'

cross_validation()
print counts
print '----'
print accuracy
print mean(accuracy)







