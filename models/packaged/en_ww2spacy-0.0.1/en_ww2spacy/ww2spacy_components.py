import spacy
import glob
from spacy.language import Language
from spacy.tokens import Span
from collections import Counter
import re
import string
import toml

military_pattern = '((Private|PV1|Pvt)|(Private First Class|Pfc)|(Corporal|Cpl)|(Sergeant|Sgt)|(Staff Sergeant|SSG|S\/Sgt)|(Sergeant Sirst Class|SFC|T\/Sgt)|(First Sergeant|1SG|1sg|1st Sgt)|(Master Sergeant|MSG|m\/Sgt)|(Second Lieutenant|2lt)|(First Lieutenant|1Lt)|(Captain|Cap|Cpt|Capt)|(Major|Maj)|(Lieutenant Colonel|LTC|Lt Colonel|Lt\. Colonel)|(Colonel|Col)|(General|Gen)|(Grigadier General|Grigadier Gen)|(Major General|Major Gen)|(Lieutenant General|Lt\. Gen|Lt Gen)) [A-Z][a-z\.]*( [A-Z][a-z\.]*)*'

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

@Language.component("military_personel")
def military_personel(doc):
    text = doc.text
    new_ents = []
    original_ents = list(doc.spans["ruler"])
    for sent in doc.sents:
        for match in re.finditer(military_pattern, sent.text):

            start, end = match.span()
            start = start+sent.start_char
            end = end+sent.start_char
            span = doc.char_span(start, end)
            if span.text[-1] in string.punctuation:
                span.end = span.end-1
            start, end, name = span.start, span.end, span.text
            original_ents.append(Span(doc, start, end, label="MILITARY_PERSONELL"))
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
