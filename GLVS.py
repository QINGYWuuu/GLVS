from __future__ import division
from copy import deepcopy
from mcts import mcts
import ProcessDataFunc
import numpy as np
import time
import lvs as LocalSwapNeighbor
import pandas as pd
import matplotlib.pyplot as plt
import prettytable as pt


global Matrix, m, begintime, endtime, RecordReward, LVSiter
Matrix = ProcessDataFunc.GenerateMatrix()
m = len(Matrix)
begintime, endtime = ProcessDataFunc.TimeTable()
RecordReward = []
LVSiter=0
# 定义state
class ShiftState():
    def __init__(self):
        self.works = len(Matrix)  # 总的任务个数
        self.M = Matrix
        self.board = [[0 for i in range(self.works)] for j in range(self.works)]
        self.mission1 = [-1 for i in range(self.works)]  # 各个班次的后继
        self.mission2 = [-1 for i in range(self.works)]  # 各个班次的前任
        self.currentPlayer = 0

    # 返回在当前state下可以选择的action
    def getPossibleActions(self):
        possibleActions = []
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.M[i][j] == 1 and self.mission1[i] == -1 and self.mission2[j] == -1:  # i和j可以连接并且其都没有连接
                    possibleActions.append(Action(player=self.currentPlayer, x=i, y=j))
        return possibleActions

    # 执行action 返回新state
    def takeAction(self, action):
        newState = deepcopy(self)
        newState.board[action.x][action.y] = 1
        newState.mission1[action.x] = action.y
        newState.mission2[action.y] = action.x
        newState.currentPlayer = self.currentPlayer
        return newState

    # 判断当前state是否是Terminal
    def isTerminal(self):
        if self.getPossibleActions() == []:
            return True
        else:
            return False

    def getReward(self):
        G = Drivers(self)
        G.generateschedule()
        n = G.DriverNum # number of drivers
        workinghours = []
        for i in range(n):
            ftrip=G.DriverList[i].Task1[0]
            ltrip=G.DriverList[i].Task1[-1]
            start = begintime[ftrip]
            end = endtime[ltrip]
            workinghours.append(end-start)

        reward1 = n

        reward2 = np.var(workinghours)

        # 8 hours
        standardworkhour = 480
        reward3 = 0
        for i in range(n):
            workhours = workinghours[i]
            if workhours > standardworkhour:
                reward3 += workhours - standardworkhour

        # 出发和结束是同一地点
        reward4 = 0
        for i in range(n):
            if len(G.DriverList[i].Task1) // 2 == 1:
                reward4 = reward4 + 1

        reward5 = sum(workinghours)

        alpha1 = -100
        alpha2 = -0.1
        alpha3 = -1
        alpha4 = -50
        alpha5 = -0.5

        reward = alpha1 * reward1 + alpha2 * reward2 + alpha3 * reward3 + alpha4 * reward4 + alpha5 * reward5

        G.Score = reward

        lsv_reward = reward

        if n < 1000:
            LVS_G = LocalSwapNeighbor.LSN(G, LVSiter)
            n = LVS_G.DriverNum  # number of drivers
            lsv_workinghours = []
            for i in range(n):
                lsv_ftrip = LVS_G.DriverList[i].Task1[0]
                lsv_ltrip = LVS_G.DriverList[i].Task1[-1]
                lsv_start = begintime[lsv_ftrip]
                lsv_end = endtime[lsv_ltrip]
                lsv_workinghours.append(lsv_end - lsv_start)

            lsv_reward1 = n

            lsv_reward2 = np.var(lsv_workinghours)

            lsv_reward3 = 0
            for i in range(n):
                lsv_workhours = lsv_workinghours[i]
                if lsv_workhours > standardworkhour:
                    lsv_reward3 += lsv_workhours - standardworkhour

            # 出发和结束是同一地点
            lsv_reward4 = 0
            for i in range(n):
                if len(LVS_G.DriverList[i].Task1) // 2 == 1:
                    lsv_reward4 = lsv_reward4 + 1

            lsv_reward5 = sum(lsv_workinghours)

            lsv_reward = alpha1 * lsv_reward1 + alpha2 * lsv_reward2 + alpha3 * lsv_reward3 + alpha4 * lsv_reward4 + alpha5 * lsv_reward5

        tb = pt.PrettyTable()
        tb.field_names=["MCTS_LVS","Reward","reward1","reward2","reward3","reward4","reward5"]
        tb.add_row(["before",reward,reward1,reward2,reward3,reward4,reward5])
        tb.add_row(["after",lsv_reward,lsv_reward1,lsv_reward2,lsv_reward3,lsv_reward4,lsv_reward5])
        print(tb)
        RecordReward.append([lsv_reward, lsv_reward1, lsv_reward2, lsv_reward3, lsv_reward4, lsv_reward5])

        return lsv_reward


class Drivers():
    def __init__(self, state):
        self.DriverNum = 0
        self.DriverList = []
        self.state = state
        self.Reward = 0
        self.Variance = 0
        self.totalworkinghours = 0
        self.Score = 0

    def generateschedule(self):
        driverid = 0
        for i in range(len(self.state.board)):
            if self.state.mission2[i] == -1:
                driverid = driverid + 1
                driver = Driver(driverid)
                driver.Task1.append(i)
                m = 1  # 当前搜索到的司机任务个数
                nowmission = i  # 当前检索的任务序号
                while self.state.mission1[nowmission] != -1:
                    m = m + 1
                    nowmission = self.state.mission1[nowmission]
                    driver.Task1.append(nowmission)
                driver.TaskNum = m
                self.DriverList.append(driver)
        self.DriverNum = driverid

        self.totalworkinghours = 0
        for i in range(self.DriverNum):
            ftrip=self.DriverList[i].Task1[0]
            ltrip=self.DriverList[i].Task1[-1]
            start = begintime[ftrip]
            end = endtime[ltrip]
            self.DriverList[i].workinghours = end-start
            self.totalworkinghours += end-start



class Driver():
    def __init__(self, driverID):
        self.DriverID = driverID
        self.TaskNum = 0
        self.Task1 = []
        self.Task2 = []
        self.beginTime1 = 0
        self.endTime1 = 0
        self.divide = 0  # 表示shift是否为分开的
        self.beginTime2 = 0
        self.endTime2 = 0
        self.workinghours=0


class Action():
    def __init__(self, player, x, y):
        self.player = player
        self.x = x
        self.y = y

    def __str__(self):
        return str((self.x, self.y))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.x == other.x and self.y == other.y and self.player == other.player

    def __hash__(self):
        return hash((self.x, self.y, self.player))


if __name__ == '__main__':

    for iterationtimes in [1]:
        for ex_id in [0]:
            ex_begintime = time.time()
            initialState = ShiftState()
            MCTS = mcts(iterationLimit=iterationtimes)
            # MCTS = mcts(timeLimit=searchtime)
            for i in range(1000):
                print('iteration times=', iterationtimes)
                print('Iter:', i)
                action = MCTS.search(initialState=initialState)
                if action == None:
                    print('Final')
                    Schedule = Drivers(initialState)
                    Schedule.generateschedule()
                    break
                initialState = initialState.takeAction(action)
            ex_endtime = time.time()
            df = pd.DataFrame(RecordReward)
            print(df)
            file_name = 'Result/newresult/itertimes{}_exid{}_runtime{}_score{}.csv'.format(iterationtimes,ex_id,ex_endtime-ex_begintime,RecordReward[-1][0])
            df.to_csv(file_name, index=False)
