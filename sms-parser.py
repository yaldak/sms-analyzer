#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
import emoji
import json
import math
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pprint
import random
import re
import sys
from enum import Enum

def main():
    parser = argparse.ArgumentParser(
        description="""
    SMS backup analyzer.
        """,
    )

    parser.add_argument('DATAFILE', help='path to data file')
    parser.add_argument('NORMOUTFILE', help='path to output CSV file for normalized messages')
    parser.add_argument('CORPUSOUTFILE', help='path to output CSV file for corpus')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    datafile_path = args.DATAFILE
    normalized_outfile_path = args.NORMOUTFILE
    corpus_outfile_path = args.CORPUSOUTFILE

    # TODO: download nltk data
    nltk.download('stopwords')
    nltk.download('punkt')

    with open(datafile_path, 'r') as datafile:
        datafile_contents = datafile.read()

    data = json.loads(datafile_contents)

    # TODO: make this better
    conversation = data['conversations'][0]

    stats = messages_stats(conversation)
    pprint.pprint(stats)

    normalized = messages_normalize(conversation)
    with open(normalized_outfile_path, 'w') as normalized_outfile:
        # TODO: make this better
        writer = csv.DictWriter(normalized_outfile, fieldnames = normalized[0].keys())
        writer.writeheader()
        writer.writerows(normalized)

    corpus = messages_corpus(conversation)
    with open(corpus_outfile_path, 'w') as corpus_outfile:
        # TODO: make this better
        writer = csv.DictWriter(corpus_outfile, fieldnames = corpus[0].keys())
        writer.writeheader()
        writer.writerows(corpus)

def messages_per_day(conversation):
    results = {}

    for message in conversation:
        # skip null messages
        if ('body' not in message.keys()) or (not message['body']):
            continue

        message_date = datetime.fromtimestamp(message['date'] / 1000.0)
        message_date_fmt = message_date.strftime('%x')

        if message_date_fmt not in results:
            results[message_date_fmt] = {
                'date': message_date_fmt,
                'count': 1
            }
        else:
            results[message_date_fmt]['count'] += 1

    return list(results.values())

def messages_normalize(conversation):
    results = []

    for message in conversation:
        # skip null messages
        if ('body' not in message.keys()) or (not message['body']):
            continue

        message_date = datetime.fromtimestamp(message['date'] / 1000.0)

        results.append({
            'datetime': message_date.strftime('%x %X'), # Excel format
            'hour': message_date.hour,
            'month': message_date.month,
            'weekday': message_date.weekday(),
            'length': len(message['body'])
        })

    return results

def messages_stats(conversation):
    hour_metrics = [0] * 24
    month_metrics = [0] * 12
    weekday_metrics = [0] * 7

    for message in conversation:
        message_date = datetime.fromtimestamp(message['date'] / 1000.0)

        hour_metrics[message_date.hour] += 1
        month_metrics[message_date.month] += 1
        weekday_metrics[message_date.weekday()] += 1

    return {
        'count': len(conversation),
        'hour_metrics': hour_metrics,
        'month_metrics': month_metrics,
        'weekday_metrics': weekday_metrics
    }

def messages_corpus(conversation):
    results = {}

    for message in conversation:
        # skip null messages
        if ('body' not in message.keys()) or (not message['body']):
            continue

        normalized_text = emoji.demojize(message['body']).lower()
        normalized_text = normalized_text.strip().lower()
        normalized_text = re.sub(r'[^a-zA-Z0-9_\-\:\s]+', '', normalized_text)
        word_tokens = normalized_text.split()
        #word_tokens = word_tokenize(normalized_text)

        stop_words = set(stopwords.words('english'))
        words = [w for w in word_tokens if not w in stop_words]

        for word in words:
            if word not in results:
                results[word] = {
                    'word': word,
                    'count': 1
                }
            else:
                results[word]['count'] += 1

    return list(results.values())

if __name__ == '__main__':
    main()
