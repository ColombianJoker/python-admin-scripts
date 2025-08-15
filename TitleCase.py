#!/usr/bin/python
# -*- coding: UTF-8 -*-

#   Version 1.0.0
#   This is an adaptation of John Gruber's original Title Case Script
#   While not completely Pythonic, it gets the job done :) 
#   To test the edge cases, run this with 'test' as the first argument
#   
#   Jordan Sherer
#   http://widefido.com/
#   20 May 2008

#   This filter changes all words to Title Caps, and attempts to be clever
#   about *un*capitalizing small words like a/an/the in the input.
#
#   The list of "small words" which are not capped comes from
#   the New York Times Manual of Style, plus 'vs' and 'v'. 
#
#   John Gruber
#   http://daringfireball.net/
#   10 May 2008
#
#   License: http://www.opensource.org/licenses/mit-license.php
#

import re, sys
small_words = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", \
               "in", "of", "on", "or", "the", "to", "v\.?", "via", "vs\.?"] 

boundary_hash = "*#*"   # This is a random string to split against 
exception_chars = ".'&" # These are chars that should NOT split words

small_re = re.compile("|".join([r"%s\b" % word for word in small_words]), re.I)
inline_dots_re = re.compile(r"\w+\.\w")
inline_caps_re = re.compile(r"[\w|&]([A-Z]+)")
bounds_re = re.compile(r'\b')
vs_exception_re = re.compile(r"(Vs|vS)\.")
quotes_re = re.compile(r"(?<=\s)?(['\"])(?:(?:([^\1]+))|(?:([^\1]+)))(\1)(?=\s)?")

def title_case(title):
    if not title:
        return ""
    word_list = bounds_re.sub(boundary_hash, title)
    word_list = word_list.strip(boundary_hash)
    for c in exception_chars:
        word_list = word_list.replace("".join([boundary_hash, c, boundary_hash]), c)
    words = word_list.split(boundary_hash)
    if words:
        first_word_index = last_word_index = -1
        for i, word in enumerate(words):
            # The first word in the list could be a punctuation, so lets 
            # check to see if it is an 'alpha' word
            if word.isalpha():
                if first_word_index == -1:
                    first_word_index = i
                last_word_index = i
                
            # If there are inline dots or capitals, skip word and continue...
            if inline_dots_re.search(word) or inline_caps_re.search(word):
                continue
                
            if small_re.match(word):
                #Word matches the a smallword, make lowercase
                words[i] = word.lower()
            else:
                #Word is normal, capitalize
                words[i] = word.capitalize()
        
        #If first word is a small word, capitalize
        if small_re.match(words[first_word_index]):
            words[first_word_index] = words[first_word_index].capitalize()
        
        #If last word is a small word, capitalize
        if small_re.match(words[last_word_index]):
            words[last_word_index] = words[last_word_index].capitalize()
    title = "".join(words)
    
    # Look for the exceptions (Vs. or vS. only...the rest are take care of)
    title = vs_exception_re.sub(r"vs.", title)
    
    # Look for subquotes, and replace them with their titled counterparts
    quotes = quotes_re.search(title)
    if quotes:
        mark = quotes.group(1)
        titled_quote = title_case(quotes.group(2))
        if titled_quote:
            title = title.replace(quotes.group(0), "".join([mark, titled_quote, mark]))
    return title
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_cases = """Q&A With Steve Jobs: 'That's What Happens In Technology'
            What Is AT&T's Problem?
            Apple Deal With AT&T Falls Through
    
            this v that
            this vs that
            this v. that
            this vs. that
    
            The SEC's Apple Probe: What You Need to Know
    
            'by the Way, small word at the start but within quotes.'
    
            Small word at end is nothing to be afraid of
    
    
            Starting Sub-Phrase With a Small Word: a Trick, Perhaps?
            Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'
            Sub-Phrase With a Small Word in Quotes: "a Trick, Perhaps?"
    
            "Nothing to Be Afraid of?"
            "Nothing to Be Afraid Of?"
    
            a thing
    
    
    
            Known Issues
            ------------
    
            2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'
            """
            
            for line in test_cases.splitlines():
                line = line.strip()
                if line:
                    print "-"
                    print "Orginal: %s" % line
                    print "Titled:  %s" % title_case(line)
                    print "-"

        else:
            print title_case(sys.argv[1])
        
    else:
        print "Usage: <%s> \"title to case\"" % sys.argv[0]
        print 
        print "To test, use the title 'test'"
