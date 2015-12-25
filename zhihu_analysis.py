# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:03:22 2015

@author: Che
"""

import sqlite3
import pandas as pd
import pylab
import collections
import numpy as np
import networkx as nx
from collections import defaultdict


def plot_user_distribution():

    conn = sqlite3.connect("zhihu.db")
    user_data = pd.read_sql('select * from User', conn) #database data -> pandas.DataFrame    
    conn.close()
    
    feature_list = ['followee_num', 'follower_num', 'answer_num', 'agree_num', 'thanks_num']   
    
    for feature in feature_list:    
        pylab.figure(feature)
        pylab.title("Distribution of " + feature + ' to Individual User')
        pylab.xlabel("Individual User(sum=26161)")
        pylab.ylabel(feature + " of user")
        user = list(range(len(user_data)))
        feature_value = sorted(list(user_data[feature]), reverse=True)#DataFrame -> list -> do sort
        pylab.scatter(user, feature_value)
        print 'mean of', feature, np.mean(list(user_data[feature]))
        print 'median of', feature, np.median(list(user_data[feature]))
        print 'standard deviation of', np.std(list(user_data[feature])), '\n'

    pylab.show()

def plot_user_summary_log_log_distribution():
    '''
    for followee_num / follower_num, this is a plot of (out/in) degree distribution 
    '''
    conn = sqlite3.connect("zhihu.db")
    user_data = pd.read_sql('select * from User', conn) #database data -> pandas.DataFrame    
    conn.close()
    
    feature_list = ['followee_num', 'follower_num', 'answer_num', 'agree_num', 'thanks_num']   
    
    for feature in feature_list:    
        pylab.figure('log-log ' + feature)
        pylab.title('Log-log Distribution of ' + feature + ' to User Count')
        pylab.xlabel(feature + ' Count(log10)')
        pylab.ylabel("User Count(log10)")
        feature_count_pairs = collections.Counter(list(user_data[feature])).most_common()
        feature_value = np.log10(zip(*feature_count_pairs)[0])
        user_count = np.log10(zip(*feature_count_pairs)[1])
        pylab.scatter(feature_value, user_count)

    pylab.show()

def plot_user_agree_and_follower_correlation():
    '''
    '''
    conn = sqlite3.connect("zhihu.db")
    user_data = pd.read_sql('select * from User', conn) #database data -> pandas.DataFrame    
    conn.close()
    
    pylab.figure('agree and follower')    
    pylab.title('Correlation Between Agree Count and Follower Count')
    pylab.xlabel('Follower Count(log10)')
    pylab.ylabel("Agree Count(log10)")   
    agree_num = np.log10(list(user_data['agree_num']))
    follower_num = np.log10(list(user_data['follower_num']))
    pylab.scatter(follower_num, agree_num)
    
    pylab.show()

def density_centrality():
    conn = sqlite3.connect("zhihu.db")     
    following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 50000) and user_url in (select user_url from User where agree_num > 50000)', conn)        
    #following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 10000) and user_url in (select user_url from User where agree_num > 10000)', conn)        
    conn.close()

    G = nx.DiGraph()
    for d in following_data.iterrows():
        G.add_edge(d[1][0], d[1][1])

    ##print nx.average_shortest_path_length(G), '\n'
    print 'density of graph:', nx.density(G)

    user_betweenness_list = sorted(nx.betweenness_centrality(G).items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    betweenness_list = zip(*user_betweenness_list)[1]# tuple of elements like: 0.0006937913420042883

    #betweenness_count_pairs = collections.Counter(list(betweenness_list)).most_common() # list of element like: (0.0006937913420042883, 1)
    #b_value = zip(*betweenness_count_pairs)[0] #unzip to get 0.0006937913420042883
    #b_count = zip(*betweenness_count_pairs)[1]    
    #pylab.figure('Betweenness Distribution')
    #pylab.title('Betweenness Distribution')
    #pylab.xlabel('Betweenness')
    #pylab.ylabel('Count')    
    #pylab.scatter(b_value, b_count)

    pylab.figure('Betweenness Distribution')
    pylab.title('Betweenness Distribution')
    pylab.xlabel('Indivisual User')
    pylab.ylabel('Betweeness of the User')       
    pylab.scatter(list(range(len(betweenness_list))), betweenness_list)

    user_closeness_list = sorted(nx.closeness_centrality(G).items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    closeness_list = zip(*user_closeness_list)[1]   

    #closeness_count_pairs = collections.Counter(list(closeness_list)).most_common()
    #c_value = zip(*closeness_count_pairs)[0]
    #c_count = zip(*closeness_count_pairs)[0]    
    #pylab.figure('Closeness Distribution')
    #pylab.title('Closeness Distribution')
    #pylab.xlabel('Closeness')
    #pylab.ylabel('Count')        
    #pylab.scatter(c_value, c_count)

    pylab.figure('Closeness Distribution')
    pylab.title('Closeness Distribution')
    pylab.xlabel('Indivisual User')
    pylab.ylabel('Closeness of the User')       
    pylab.scatter(list(range(len(closeness_list))), closeness_list)
    
def pagerank_hits():
    conn = sqlite3.connect("zhihu.db")     
    #following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 50000) and user_url in (select user_url from User where agree_num > 50000)', conn)        
    following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 10000) and user_url in (select user_url from User where agree_num > 10000)', conn)        
    conn.close()
    
    G = nx.DiGraph()
    cnt = 0
    for d in following_data.iterrows():
        G.add_edge(d[1][0],d[1][1])
        cnt += 1
    print 'links number:', cnt
    pylab.figure(0)
    nx.draw_networkx(G)
    pylab.show()

    # PageRank
    pr = nx.pagerank(G)
    prsorted = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    print 'pagerank top 100:\n'
    for p in prsorted[:100]:
        print p[0], p[1]
    
    # HITS
    hub, auth = nx.hits(G)
    print 'hub top 100:\n'
    for h in sorted(hub.items(), key=lambda x: x[1], reverse=True)[:100]:
        print h[0], h[1]
    print '\nauth top 100:\n'    
    for a in sorted(auth.items(), key=lambda x: x[1], reverse=True)[:100]:     
        print a[0], a[1]

def strongly_connected_components():
    conn = sqlite3.connect("zhihu.db")     
    #following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 50000) and user_url in (select user_url from User where agree_num > 50000)', conn)        
    following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 10000) and user_url in (select user_url from User where agree_num > 10000)', conn)        
    conn.close()
    
    G = nx.DiGraph()
    cnt = 0
    for d in following_data.iterrows():
        G.add_edge(d[1][0],d[1][1])
        cnt += 1
    print 'links number:', cnt

    scompgraphs = nx.strongly_connected_component_subgraphs(G)
    scomponents = sorted(nx.strongly_connected_components(G), key=len, reverse=True)
    print 'components nodes distribution:', [len(c) for c in scomponents]
    
    #plot graph of component, calculate saverage_shortest_path_length of components who has over 1 nodes
    index = 0
    print 'average_shortest_path_length of components who has over 1 nodes:'
    for tempg in scompgraphs:
        index += 1
        if len(tempg.nodes()) != 1:
            print nx.average_shortest_path_length(tempg)
            print 'diameter', nx.diameter(tempg)
            print 'radius', nx.radius(tempg)
        pylab.figure(index)
        nx.draw_networkx(tempg)
        pylab.show()

    # Components-as-nodes Graph
    cG = nx.condensation(G)
    pylab.figure('Components-as-nodes Graph')
    nx.draw_networkx(cG)
    pylab.show()    

def dominant_set_topic_rank():
    #dominant_set
    conn = sqlite3.connect("zhihu.db")     
    following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 50000) and user_url in (select user_url from User where agree_num > 50000)', conn)        
    #following_data = pd.read_sql('select user_url, followee_url from Following where followee_url in (select user_url from User where agree_num > 10000) and user_url in (select user_url from User where agree_num > 10000)', conn)        
    G = nx.DiGraph()
    for d in following_data.iterrows():
        G.add_edge(d[1][0], d[1][1])
    dominant_set = nx.dominating_set(G)
    print 'user number in dominant set:', len(dominant_set)

    #topics answered by users in dominant_set
    user_topic_data = pd.read_sql('select user_url, topic from UserTopic', conn) 
       
    topicdict = defaultdict(int)
    i = 0#counter
    for row in user_topic_data.iterrows():
        user_url = row[1][0]
        topic = row[1][1]
        if user_url in dominant_set:
            topicdict[topic] += 1
        i += 1
        #if i % 100 == 0:
            #print i
    conn.close()
    
    topicsorted = sorted(topicdict.items(), key=lambda x: x[1], reverse=True)
    
    # topic top 100
    for t in topicsorted[:100]:
        print t[0],t[1]

#todo: def pagerank_topic_rank():
    