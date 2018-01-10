#!/usr/bin/env python
# -*- coding: utf8 -*-
#print "Author: REVo, 12/12/2017,gm0648@hotmail.com"
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from corenlp_revo import StanfordCoreNLP

def convert_NER(coreNLP_output):
    sentence = ""
    for sent in coreNLP_output['sentences']:
        for index,token in enumerate(sent['tokens']):
            if 'normalizedNER' in token and token['ner'] != 'ORDINAL':
                #got a !
                now_NER = token['normalizedNER']
                #print "DEBUG:NER:",now_NER
                list_del = []
                for x in range(index+1,len(sent['tokens'])):
                    if 'normalizedNER' in sent['tokens'][x]:
                        if now_NER == sent['tokens'][x]['normalizedNER']:
                            #same
                            list_del.append(x)
                    else:
                        break
                for index,ele in enumerate(list_del):
                    del sent['tokens'][ele-index]

                #finished processing
                if 'before' in token:
                    sentence += token['before'] + token['normalizedNER']
                else:
                    sentence += token['normalizedNER']
            else:
                if token['originalText'] == "":
                    word = token['word']
                else:
                    word = token['originalText']
                if 'before' in token:
                    sentence += token['before'] + word
                else:
                    sentence += word
        #sentence += " "
    #print "sentence:",sentence
    return sentence


if __name__ == '__main__':
    import codecs
    import multiprocessing
    #
    if (sys.argv[1] == '-h'):
    	print "usage: python NER_replacer.py [en|zh] [NUM_processes] < input "
    	sys.exit()#
    import logging
    #
    try:
        lang = sys.argv[1]
    except:
        lang = 'en'
    if lang == 'en':
        nlp = StanfordCoreNLP('http://localhost:9000')
    else:
        nlp = StanfordCoreNLP('http://localhost:9001')

    try:
        totoal_cpu = int(sys.argv[2])
    except:
        totoal_cpu = multiprocessing.cpu_count()


    sys.stdin = codecs.getreader('utf-8')(sys.stdin)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    properties={
    'annotators': 'tokenize,ssplit,pos,lemma,ner',
    'outputFormat': 'json'
    }
    
    def batch_NER_process(source_list):
        tmp_sentences = []
        tmp_index = [ele[0] for ele in source_list]
        for index,ele in enumerate(source_list):
            sentence = ele[1]
            NER_output = nlp.annotate(sentence, properties=properties)
            tmp_sentences.append(convert_NER(NER_output).strip()+"\n")
        return tmp_index,tmp_sentences


    #read whole file
    #print "Starting reading files"
    # index = 0
    # while True:
    #     line = sys.stdin.readline()
    #     if not line:
    #         break
    #     NER_output = nlp.annotate(line, properties=properties)
    #     output_line = convert_NER(NER_output)
    #     sys.stdout.write(output_line.strip()+"\n")
    #     index+=1
    #     #if not(index % 1000):
    #     #    print "current line :",index
    #multiprocessing
    #SIZE = 500000
    #logging.basicConfig(filename='logger.log', level=logging.INFO)
    SIZE = 50000
    BATCH = 0
    BREAK = True
    while(BREAK):
        logging.critical("BATCH:"+str(BATCH))
        BATCH += 1
        #
        source = []
        for _ in xrange(SIZE):
            line = sys.stdin.readline()
            if not line:
                BREAK = False
                break
            source.append(line)
        #
        for index,sen in enumerate(source):
            source[index] = (index,sen)
        #generate multiprocessing data
        privot = len(source) / totoal_cpu
        source_list = [None] * totoal_cpu
        for cpu_id in range(0,totoal_cpu-1):
            source_list[cpu_id] = source[cpu_id*privot:(cpu_id+1)*privot]
        source_list[-1] = source[(totoal_cpu-1)*privot:]
        #
        p = multiprocessing.Pool(processes=totoal_cpu)
        result = p.map(batch_NER_process,source_list)
        p.close()
        logging.critical("Finished One BATCH")
        #write files
        #final_sentences = []
        final_tuple = []
        for process_data in result:
            for index,index_sent in enumerate(process_data[0]):
                final_tuple.append((index_sent,process_data[1][index]))
        #resort all sentence by id
        final_tuple = sorted(final_tuple, key=lambda x:x[0])
        for TUPLE in final_tuple:
            sys.stdout.write(TUPLE[1])
        #sys.exit()
        #print final_sentences[480:520]
            #tuple(index_list,sentences),they are sorted already
            #for sentence in process_data[1]:
            #    sys.stdout.write(sentence)
        #DONE one BATCH
