import ProcessDataFunc
import numpy as np
import copy

#INPUT：一个原始的schedule
#OUTPUT：LSN后schedule的方差

# 每个trip的开始和结束时间
begintime, endtime = ProcessDataFunc.TimeTable()
# 每个trip的性质0上行 1下行
trip_a = ProcessDataFunc.Attribute()
# 总任务数
TotalTaskNum = len(begintime)
# 邻接矩阵
Matrix = ProcessDataFunc.GenerateMatrix()

#确定切割顺序
def DecomposeRange(Tknum, Tmaxnum):
    DR = []
    middle = Tmaxnum // 2
    for i in range(middle, Tmaxnum - Tknum + 1):
        DR.append(i)
        DR.append(Tmaxnum - i)
    return DR

#将班从大到小排序
def resortshift(schedule):
    n = schedule.DriverNum
    for i in range(n):
        for j in range(0, n-i-1):
            if schedule.DriverList[j].TaskNum < schedule.DriverList[j + 1].TaskNum:
                schedule.DriverList[j], schedule.DriverList[j + 1] = schedule.DriverList[j + 1], schedule.DriverList[j]
    return schedule

#将该班分解为两个班
def Decompose(T, h):
    global begintime, endtime
    T.Task2 = T.Task1[h:]
    T.Task1 = T.Task1[:h]
    T.divide = 1
    T.TaskNum = len(T.Task1) + len(T.Task2)
    T.beginTime1 = begintime[T.Task1[0]]
    T.endTime1 = endtime[T.Task1[-1]]
    if T.Task2 == []:
        T.beginTime2 = 0
        T.endTime2 = 0
        T.divide = 0
    else:
        T.beginTime2 = begintime[T.Task2[0]]
        T.endTime2 = endtime[T.Task2[-1]]
# 没有Swap成功再将其结合
def Compose(T):
    global begintime, endtime
    T.Task1 = T.Task1 + T.Task2
    T.beginTime1 = begintime[T.Task1[0]]
    T.endTime1 = endtime[T.Task1[-1]]
    T.Task2 = []
    T.beginTime2 = 0
    T.endTime2 = 0
    T.divide = 0
    T.TaskNum = len(T.Task1) + len(T.Task2)

    # 1 采取分班制
    # 2 连续排班制
# Tk和Tmax1进行加结合
def combineshift1(Tmax, Tk):
    global trip_a
    # Tmax = Tmax1 + Tmax2 ---》Tmax1 + Tk
    # Tk   = Tk    + Null  ---》Tmax2 + Null
    #1 连接时间为1-15版本
    #if (Tmax.endTime1 + 1 < Tk.beginTime1) and (Tmax.endTime1 + 15 > Tk.beginTime1) and (trip_a[Tmax.Task1[-1]] != trip_a[Tk.Task1[0]]):#Tmax2和Tk互换 Tmax1 -》Tk
    #2 只要能连接上版本
    #if Tmax.endTime1 < Tk.beginTime1:
    #3 根据邻接矩阵连接版本
    if Matrix[Tmax.Task1[-1]][Tk.Task1[0]]==1:
        Tmax.Task2, Tk.Task1 = Tk.Task1, Tmax.Task2#Tmax2和Tk互换
        Tmax.divide = 1
        Tk.divide = 0
        return 1
    # Tmax = Tmax1 + Tmax2 ---》Tk    + Tmax1
    # Tk   = Tk    + Null  ---》Tmax2 + Null
    # 1 连接时间为1-15版本
    #elif (Tk.endTime1 + 1 < Tmax.beginTime1) and (Tk.endTime1 + 15 > Tmax.beginTime1) and (trip_a[Tmax.Task1[0]] != trip_a[Tk.Task1[-1]]):#Tmax2和Tk互换 Tk -》Tmax1
    # 2 只要能连接上版本
    #elif Tk.endTime1 < Tmax.beginTime1:
    # 3 根据邻接矩阵连接版本
    elif Matrix[Tk.Task1[-1]][Tmax.Task1[0]]==1:
        #先Tmax2 和Tk互换
        Tmax.Task2, Tk.Task1 = Tk.Task1, Tmax.Task2
        #再Tmax1和Tmax2互换
        Tmax.Task1, Tmax.Task2 = Tmax.Task2, Tmax.Task1
        Tmax.divide = 1
        Tk.divide = 0
        return 1
    else:
        return 0

# Tk和Tmax2进行加结合
def combineshift2(Tmax, Tk):
    # Tmax = Tmax1 + Tmax2 ---》Tk    + Tmax2
    # Tk   = Tk    + Null  ---》Tmax1 + Null
    # 1 连接时间为1-15版本
    #if (Tk.endTime1 + 1 < Tmax.beginTime2) and (Tk.endTime1 + 15 > Tmax.beginTime2) and (trip_a[Tmax.Task2[0]] != trip_a[Tk.Task1[-1]]):  # Tmax1和Tk互换 Tk -》Tmax2
    # 2 只要能连接上版本
    # if Tk.endTime1 < Tmax.beginTime2:
    # 3 根据邻接矩阵连接版本
    if Matrix[Tk.Task1[-1]][Tmax.Task2[0]]==1:
        Tmax.Task1, Tk.Task1 = Tk.Task1, Tmax.Task1  # Tmax1和Tk互换
        Tmax.divide = 1
        Tk.divide = 0
        return 1
    # Tmax = Tmax1 + Tmax2 ---》Tmax2 + Tk
    # Tk   = Tk    + Null  ---》Tmax1 + Null
    # 1 连接时间为1-15版本
    #elif (Tmax.endTime2 + 1 < Tk.beginTime1) and (Tmax.endTime2 + 15 > Tk.beginTime1) and (trip_a[Tmax.Task2[-1]] != trip_a[Tk.Task1[0]]):  # Tmax1和Tk互换 Tmax2 -》Tk
    # 2 只要能连接上版本
    #elif Tmax.endTime2 < Tk.beginTime1:
    # 3 根据邻接矩阵连接版本
    elif Matrix[Tmax.Task2[-1]][Tk.Task1[0]]==1:
        # 先Tmax1 和Tk互换
        Tmax.Task1, Tk.Task1 = Tk.Task1, Tmax.Task1  # Tmax1和Tk互换
        # 再Tmax1和Tmax2互换
        Tmax.Task1, Tmax.Task2 = Tmax.Task2, Tmax.Task1
        Tmax.divide = 1
        Tk.divide = 0
        return 1
    else:
        return 0

def SwapNeighbor(Tmax, Tk):
    Tmax1num = len(Tmax.Task1)
    Tmax2num = len(Tmax.Task2)
    if Tmax1num >= Tmax2num: #Tmax1大 优先选Tmax2与Tk结合
        if combineshift2(Tmax, Tk):
            return 1
        elif combineshift1(Tmax, Tk):
            return 1
        else:
            return 0
    else:
        if combineshift1(Tmax, Tk):
            return 1
        elif combineshift2(Tmax, Tk):
            return 1
        else:
            return 0

def Updateshift(schedule):
    global begintime, endtime
    schedule.DriverNum = len(schedule.DriverList)
    for i in range(schedule.DriverNum):
        T = schedule.DriverList[i]
        T.TaskNum = len(T.Task1) + len(T.Task2)
        if T.Task1 == [] and T.Task2 != []:
            T.Task1, T.Task2 = T.Task2, T.Task1
            T.divide = 0
        if T.Task2 == []:
            T.divide = 0
        T.beginTime1 = begintime[T.Task1[0]]
        T.endTime1 = endtime[T.Task1[-1]]
        if T.divide == 1:
            if T.Task2 == []:
                T.beginTime2 = 0
                T.endTime2 = 0
            else:
                T.beginTime2 = begintime[T.Task2[0]]
                T.endTime2 = endtime[T.Task2[-1]]
    for i in range(schedule.DriverNum):
        ftrip = schedule.DriverList[i].Task1[0]
        ltrip = schedule.DriverList[i].Task1[-1]
        start = begintime[ftrip]
        end = endtime[ltrip]
        schedule.DriverList[i].workinghours = end - start




def LSN(schedule, lvs_iter):
    # 更新shift 赋值begintime和endtime
    Updateshift(schedule)
    # 对其进行司机按照班次多少进行排序 多---》少
    resortshift(schedule)
    # 司机数保持不变
    n = schedule.DriverNum
    # 计算swap前的方差

    workinghours=[]
    for i in range(n):
        workinghours.append(schedule.DriverList[i].workinghours)

    Variance1 = np.var(workinghours)
    Variance2 = np.var(workinghours)
    print('Driver NUm=', n)
    print('Before Swap：', 'VarianceBefore = ', Variance1)


    print('lvs_iter=',lvs_iter)
    lvs_iter= lvs_iter+1
    # for LVSiter in range(lvs_iter):
    while Variance1 >= Variance2:
        lvs_schedule = copy.deepcopy(schedule) #备份
        # Local Swap Neighbor
        breakflag = 1 # 判断有没有进行swap，要不要update 重新LSN
        while breakflag == 1:
            # 选取Tmax
            for i in range(n):
                resortshift(schedule)
                breakflag = 0#表示没有swap
                Tmax = schedule.DriverList[i]
                Tmaxnum = Tmax.TaskNum
                if Tmax.divide == 1 or Tmaxnum <= 1:
                    continue
                else:
                    # 选取Tk
                    for j in range(n-1, -1, -1):
                        Tk = schedule.DriverList[j]
                        Tknum = Tk.TaskNum
                        if Tk.divide == 1:
                            continue
                        else:
                            if Tknum <= 0.5 * Tmaxnum:
                                Drange = DecomposeRange(Tknum, Tmaxnum)
                                for h in Drange:#h取值范围为Tk～Tmax-Tk
                                    Decompose(Tmax, h)
                                    if SwapNeighbor(Tmax, Tk) == 1:#swap成功
                                        Updateshift(schedule)
                                        breakflag = 1
                                        break
                                    else:
                                        Compose(Tmax)
                                        Updateshift(schedule)
                                        resortshift(schedule)
                        if breakflag == 1:
                            break
                if breakflag == 1:
                    break

        workinghours = []
        for i in range(n):
            Compose(schedule.DriverList[i])
            stime = begintime[schedule.DriverList[i].Task1[0]]
            etime = endtime[schedule.DriverList[i].Task1[-1]]
            workinghours.append(etime-stime)
        VarianceAfter = np.var(workinghours)
        Updateshift(schedule)
        resortshift(schedule)
        Variance1 = Variance2 #lvs_schedule
        Variance2 = VarianceAfter #schedule
        print('-->',VarianceAfter,end='')
        if Variance1==Variance2:
            break

    print('After Swap:', 'VarianceAfter = ', Variance1)
    resortshift(lvs_schedule)


    return lvs_schedule