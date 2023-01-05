import spacy
import glob
from spacy.language import Language
from spacy.tokens import Span
from collections import Counter
import re
import string
import toml

military_pattern = '(Private|PV1|Pvt|Pvt\.|Private First Class|Pfc|Pfc\.|Corporal|Cpl|Cpl\.|Sergeant|Sgt|Sgt\.|Staff Sergeant|SSG|S\/Sgt|Staff Sgt\.|Staff Sgt|Sergeant First Class|SFC|T\/Sgt|First Sergeant|1SG|1sg|1st Sgt|1st Sgt\.|Master Sergeant|MSG|m\/Sgt|m \Sgt|M Sgt\.|Second Lieutenant|2lt|2Lt\.|2Lt|First Lieutenant|1Lt|2Lt\.|2Lt|Lt\.|Lieutenant|Captain|Cap|Cpt|Capt|Cpt\.|Capt\.|Cap\.|Major|Maj|Maj\.|Lieutenant Colonel|LTC|Lt Colonel|Lt\. Colonel|Lt\. Col\.|Colonel|Col|Col\.|General|Gen|Gen\.|Brigadier General|Brigadier Gen|Brig\. Gen\.|Brigadier Gen\.|Major General|Major Gen|Maj\. Gen\.|Lieutenant General|Lt\. Gen\.|Lt Gen) [A-Z][a-z\.]*( [A-Z][a-z\.]*)*'

@Language.component("clean_spans")
def clean_spans(doc):
    original_spans = list(doc.spans["ruler"])
    #remove the from spans
    new_spans = []
    for span in doc.spans["ruler"]:
        if span[0].text.lower() == "the":
            span.start = span.start+1
        new_spans.append(span)
    doc.spans["ruler"] = new_spans

    #filter the overlapping spans so that priority is given to the longest span unless all spans
    #are of equal length
    span_starts = [span.start for span in doc.spans["ruler"]]
    overlap_starts = set([i for i in span_starts if span_starts.count(i)>1])
    longest = {}
    for span in doc.spans["ruler"]:
        if span.start in overlap_starts:
            if span.text not in longest:
                longest[span.start] = [span.end, span.text]
            else:
                if longest[span.start][0] < span.end:
                    longest[span.start] = [span.end, span.text]
    final_spans = []
    for span in doc.spans["ruler"]:
        if span.start in longest:
            if [span.end, span.text] == longest[span.start]:
                final_spans.append(span)
        else:
            final_spans.append(span)

    doc.spans["ruler"] = final_spans
    return doc

@Language.component("military_personnel")
def military_personel(doc):
    text = doc.text
    new_ents = []
    original_ents = list(doc.spans["ruler"])

    for match in re.finditer(military_pattern, doc.text):
        start, end = match.span()
        span = doc.char_span(start, end, alignment_mode="expand")
        if span != None:
            if span.text[-1] in string.punctuation:
                span.end = span.end-1
            start, end, name = span.start, span.end, span.text
            tmp_span = Span(doc, start, end, label="MILITARY_PERSONNEL")
            for i, token in enumerate(tmp_span):
                if i > 2 and doc[(tmp_span.start+i)-2].text not in military_pattern.replace("\\", ""):
                    if token.is_sent_start == True:
                        tmp_span.end=tmp_span.start+i-1

            original_ents.append(tmp_span)
    doc.spans["ruler"] = original_ents
    return doc

@Language.component("clean_tank")
def clean_tank(doc):
    new_spans = []
    for span in doc.spans["ruler"]:
        if span.label_ == "TANK":
            if span.text.split()[-1] in ["tank", "tanks"]:
                span.end = span.end-1
        new_spans.append(span)
    doc.spans["ruler"] = new_spans
    return doc

@Language.component("clean_ships")
def clean_ships(doc):
    hit_words = ["crew", "sea", "marine", "water", "ship", "boat", "vessel", "aboard", "captain", "sail"]
    window_start, window_end = [25, 25]
    original_ents = list(doc.spans["ruler"])
    new_ents = []
    for span in original_ents:
        if span.label_ in ["CRUISER", "BATTLESHIP"]:
            if span.start_char < window_start:
                window_start = 0
            else:
                window_start = span.start_char-window_start
            if len(doc.text)-span.end_char > window_end:
                window_end = -1
            else:
                window_end = span.end_char+window_end
            window_text = doc.text[window_start: window_end]
            if any(hit in window_text for hit in hit_words):
                new_ents.append(span)
        else:
            new_ents.append(span)
    doc.spans["ruler"] = new_ents
    return doc

@Language.component("find_ghetto")
def find_ghetto(doc):
    original_ents = list(doc.spans["ruler"])
    for i, token in enumerate(doc):
        if token.text.lower() == "ghetto":
            prev_token = doc[i-1]
            if prev_token.text[0].isupper():
                original_ents.append(Span(doc, i-1, i, label="GHETTO"))
    doc.spans["ruler"] = original_ents
    return doc
