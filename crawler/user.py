# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 14:51:57 2015

@author: NathanLvzs
"""

from zhihu import Question
from zhihu import Answer
from zhihu import User
from zhihu import Collection
import multiprocessing as mp
from datetime import datetime
import sys
import os
import Queue
import time
import requests

# control parameter
crawlLayerNum = 3#1 for testing
# seed user, act as the first item in the taskqueue
user_url = "https://www.zhihu.com/people/zhao-che"
# user_url = "https://www.zhihu.com/people/bao-jie-14"
# number of processes
processNum = 4

prefix_people = "https://www.zhihu.com/people/"
prefix_question = "https://www.zhihu.com/question/"


class UserInfo:
    """
    """
    def __init__(self, user_uuid, layer):
        user = User(prefix_people + user_uuid)
        self.user = user
        self.uuid = user_uuid
        self.user_id = user.get_user_id()
        self.followees = map(lambda x: x.user_url.replace(prefix_people, ""), user.get_followees()) if layer < 3 else []
        # self.followers = map(lambda x: x.user_url.replace(prefix_people, ""), user.get_followers())
        self.answer_num = user.get_answers_num()
        self.following_num = user.get_followees_num()
        self.follower_num = user.get_followers_num()
        self.upvote_num = user.get_agree_num()
        self.thank_num = user.get_thanks_num()
        self.layer = layer

    def tostring(self):
        return ("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (self.uuid, self.user_id, self.following_num, self.follower_num, self.answer_num, self.upvote_num, self.thank_num, self.layer))#.decode("gbk").encode('utf-8')

    def user_followee_tostring(self):
        return ("%s\t%s" % (self.uuid, "\t".join(self.followees)))#.decode("gbk").encode('utf-8')

class UserQuestion:
    """
    """
    def __init__(self, userinfo):
        self.user_uuid = userinfo.uuid
        self.questionids = set()
        answers = userinfo.user.get_answers()
        for a in answers:
            qurl = a.get_question().url
            qid = qurl.replace(prefix_question, "")
            self.questionids.add(qid)

    def tostring(self):
        return ("%s\t%s" % (self.user_uuid, "\t".join(self.questionids)))#.decode("gbk").encode('utf-8')

class QuestionTopic:
    """
    """
    def __init__(self, question_id):
        self.question_id = question_id
        que = Question(prefix_question + question_id)
        self.topics = que.get_topics()

    def __eq__(self, other):
        return self.question_id == other.question_id

    def __hash__(self):
        return hash(self.question_id)

    def tostring(self):
        return ("%s\t%s" % (self.question_id, "\t".join(self.topics)))#.decode("gbk").encode('utf-8')

class TaskItem:
    """
    TaskItem class for taskqueue
    """
    def __init__(self, user_uuid, layer):
        self.user_uuid = user_uuid
        self.layer = layer

    def __eq__(self, other):
        return self.user_uuid == other.user_uuid

    def __hash__(self):
        return hash(self.user_uuid)

    def tostring(self):
        return "%s\t%s" % (self.user_uuid, self.layer)

def crawlUserInfo(queue, flag, vset, equeue):
    pname = mp.current_process().name
    fh_userinfo = open('data/user_' + pname, 'w')
    fh_followee = open('data/followee_' + pname, 'w')
    fh_question = open('data/question_' + pname, 'w')
    # fh_topic = open('data/topic_' + pname, 'w')
    while True:
        if flag.value == 1:
            print '%s %s while loop breaks\n' % (str(datetime.now()), pname)
            break
        task = None
        try:
            task = queue.get(False)
        except Queue.Empty as inst:
            time.sleep(50.0 / 1000.0)
            continue
        # discard visited taskitem
        if vset.has_key(task.user_uuid):
            queue.task_done()
            continue
        print "%s %s user: %s\n" % (str(datetime.now()), pname, task.user_uuid)

        userinfo, userquestion, topicset = None, None, set()
        otherErrCnt, flagbreak = 0, False
        while True:
            try:
                userinfo = UserInfo(task.user_uuid, task.layer)
                if task.layer < 3:
                    userquestion = UserQuestion(userinfo)
                break
            except requests.ConnectionError as inst:
                print ("%s: " % pname) + repr(inst)
                time.sleep(50.0 / 1000)
                otherErrCnt = 0
                continue
            except: # try 5 times, if all failed, add to error queue and move on...
            # TODO: people | org
                print "%s: other error when processing user %s" % (pname, task.user_uuid) + str(sys.exc_info()) + '\n'
                otherErrCnt += 1
                if otherErrCnt < 5:
                    time.sleep(otherErrCnt * 30.0 / 1000)
                    continue
                else:
                    equeue.put(task)
                    queue.task_done()
                    print "%s: stopped %s, already maximum attempts" % (pname, task.user_uuid) + '\n'
                    flagbreak = True
                    break
        if flagbreak:
            continue
        # write to file
        fh_userinfo.write(userinfo.tostring() + '\n')
        fh_followee.write(userinfo.user_followee_tostring() + '\n')
        if userquestion:
            fh_question.write(userquestion.tostring() + '\n')
        # for topic in topicset:
        #     fh_topic.write(topic.tostring() + '\n')
        # update taskqueue
        if task.layer < crawlLayerNum:
            map(lambda x: queue.put(TaskItem(x, task.layer+1), False), userinfo.followees)
        # mark the taskitem as done
        queue.task_done()
        vset[task.user_uuid] = 0# add task to dict
        # time.sleep(30.0 / 1000)
    fh_userinfo.close()
    fh_followee.close()
    fh_question.close()
    #fh_topic.close()
    print "%s %s finished.\n" % (str(datetime.now()), pname)
    return

def main():
    print "---%s start ---" % str(datetime.now())
    if not os.path.exists('data'):
        os.makedirs('data')
    start_time = time.time()
    manager = mp.Manager()
    completeFlag = mp.Value('i', 0)
    # completeFlag = manager.Value('i', 0)
    visitedSet = manager.dict()# for deduplication
    errorItemQueue = mp.Queue()# collect error items
    taskqueue = mp.JoinableQueue()

    # normal mode
    user_uuid = user_url.replace(prefix_people, "")
    task = TaskItem(user_uuid, 0)
    taskqueue.put(task, False)

    # multiprocessing
    processes = [mp.Process(target=crawlUserInfo, args=(taskqueue, completeFlag, visitedSet, errorItemQueue)) for x in range(0, processNum)]
    # start processes
    for p in processes:
        p.start()
    # wait until all the items in taskqueue are processed
    taskqueue.join()
    completeFlag.value = 1

    for p in processes:
        p.join()

    # print "Active children:", mp.active_children()
    if not errorItemQueue.empty():
        with open('data/errors', 'w') as tempFH:
            while not errorItemQueue.empty():
                tempFH.write(errorItemQueue.get().tostring() + '\n')

    print("---%s elapsed %s seconds ---" % (str(datetime.now()), time.time() - start_time))

if __name__ == '__main__':
    main()
