# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 15:39:46 2015

@author: Che
"""

import glob   
import sqlite3
import pandas as pd
import string

def user_to_sqlite():
    '''
    User's porfolio information
    '''    
    conn = sqlite3.connect("zhihu.db") 

    user_path = 'csv/user/edited/*'   
    user_files = glob.glob(user_path)   

    for ufile in user_files:     
        data = pd.read_csv(ufile, header=None)
        for row in data.iterrows():
            record_id = "NULL"        
            user_url = "\'" + str(row[1][0]) + "\'"
            #translate可以去掉string里所有標點符號, e.g. James Ch'i -> James Chi
            user_id = "\'" + str(row[1][1]).translate(string.maketrans("",""), string.punctuation) + "\'" 
            followee_num = str(row[1][2])
            follower_num = str(row[1][3])
            answer_num = str(row[1][4])
            agree_num = str(row[1][5])
            thanks_num = str(row[1][6])
            layer = str(row[1][7])
            is_crawled = "NULL"
            #handle duplicate wih OR REPLACE
            try:            
                command = "INSERT OR REPLACE INTO user VALUES(" + record_id + "," + user_url + "," + user_id + "," + \
                followee_num + "," + follower_num + "," + answer_num + "," + \
                agree_num + "," + thanks_num + "," + layer + "," + is_crawled + ")"
                conn.execute(command)
            except sqlite3.Error as e:
                print 'Error:', e.args[0]
                print 'at command:', command
                continue                
    conn.commit()
    conn.close()

def following_to_sqlite_1_to_n():
    '''
    User's followees
    '''
    conn = sqlite3.connect("zhihu.db") 

    following_path = 'csv/following/*'   
    following_files = glob.glob(following_path)

    for ffile in following_files:     
        data = pd.read_csv(ffile, header=None)
        for row in data.iterrows():
            record_id = "NULL"
            user_url = "\'" + str(row[1][0]) + "\'"
            #handle duplicate with distinct index
            for followee in str(row[1][1]).split('\t'):            
                followee_url = "\'" + followee + "\'"                
                try:
                    command = "INSERT INTO following VALUES(" + record_id + "," + user_url + "," + followee_url + ")"        
                    conn.execute(command)
                except sqlite3.Error as e:
                    print 'Error:', e.args[0]
                    print 'at command:', command
                    continue
    conn.commit()
    conn.close()

def following_to_sqlite_1_to_1():
    '''
    User's followees; This method is not used due to the format of crawling result csv.
    '''
    conn = sqlite3.connect("zhihu.db") 

    following_path = 'csv/following/*'   
    following_files = glob.glob(following_path)

    for ffile in following_files:     
        data = pd.read_csv(ffile, header=None)
        for row in data.iterrows():
            record_id = "NULL"
            user_url = "\'" + str(row[1][0]) + "\'"
            followee_url = "\'" + str(row[1][1]) + "\'"                
            #handle duplicate with distinct index
            try:
                command = "INSERT INTO following VALUES(" + record_id + "," + user_url + "," + followee_url + ")"        
                conn.execute(command)
            except sqlite3.Error as e:
                print 'Error:', e.args[0]
                print 'at command:', command
                continue
    conn.commit()
    conn.close()

def user_question_to_sqlite():
    '''
    User answered questions
    '''    
    conn = sqlite3.connect("zhihu.db") 

    following_path = 'csv/user_question/*'   
    following_files = glob.glob(following_path)

    for ffile in following_files:     
        data = pd.read_csv(ffile, header=None)
        for row in data.iterrows():
            record_id = "NULL"
            user_quesitons_pair = str(row[1][0]).split('\t', 1)
            user_url = "\'" + user_quesitons_pair[0] + "\'"
            for q in user_quesitons_pair[1].split('\t'):            
                question_id = "\'" + q + "\'"                
                #handle duplicate with distinct index
                try:
                    command = "INSERT INTO UserQuestion VALUES(" + record_id + "," + user_url + "," + question_id + ")"        
                    conn.execute(command)
                except sqlite3.Error as e:
                    print 'Error:', e.args[0]
                    print 'at command:', command
                    continue
    conn.commit()
    conn.close()

def question_topic_to_sqlite():
    '''
    question's topics
    '''
    conn = sqlite3.connect("zhihu.db") 

    following_path = 'csv/question_topic/*'   
    following_files = glob.glob(following_path)

    for ffile in following_files:     
        #sep to ensure the whole row is the only one field
        #use open() can work, too
        data = pd.read_csv(ffile, header=None, sep='\t\t') 
        for row in data.iterrows():
            record_id = "NULL"
            question_topics_pair = str(row[1][0]).split('\t', 1)
            question_id = "\'" + question_topics_pair[0] + "\'"

            #delete old topics, effeciency is low            
            try:
                command = "DELETE FROM Question WHERE question_id=" + question_id        
                conn.execute(command)
            except sqlite3.Error as e:
                print 'Error:', e.args[0]
                print 'at command:', command
                continue
            
            #insert new topics, handle duplicate with distinct index
            if len(question_topics_pair) == 2: #question has topics
                for t in question_topics_pair[1].split('\t'):                                
                    topic = "\'" + str(t).replace("'","''") + "\'" #escape "'" to "''" in sqlite                           
                    try:
                        command = "INSERT INTO Question VALUES(" + record_id + "," + question_id + "," + topic + ")"        
                        conn.execute(command)
                    except sqlite3.Error as e:
                        print 'Error:', e.args[0]
                        print 'at command:', command
                        continue
    conn.commit()
    conn.close()