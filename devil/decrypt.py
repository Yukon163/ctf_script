def rc4decrypt(c,key):
    s=[]
    t=[]
    for i in range(256):
        s.append(i)
    for i in range(256):
        t.append(ord(key[i%len(key)]))
    j=0
    for i in range(256):
        j=(j+s[i]+t[i])%256
        s[i],s[j]=s[j],s[i]
    i=0
    j=0
    flag=""
    for k in range(len(c)):
        i=(i+1)%256
        j=(j+s[i])%256
        s[i], s[j] = s[j], s[i]
        x=(s[i]+s[j])%256
        flag+=chr((c[k]^s[x])&0xff)
    return flag

class Dmaze():
    def __init__(self,maze,startposition,endposition):
        self.maze=maze
        self.startposition=startposition
        self.endposition=endposition
        self.flag=""
    def dfsdecrypt(self):
        maze=self.maze
        usedmap = [[0 for i in range(len(maze))] for i in range(len(maze[0]))]
        sti,stj=self.startposition
        edi,edj=self.endposition
        self.flag=""
        def dfs(x, y):
            if x == edi and y == edj:
                print(self.flag)
                return
            if maze[x + 1][y] == 0 and usedmap[x + 1][y] == 0:
                usedmap[x][y] = 1
                self.flag += 's'
                dfs(x + 1, y)
                self.flag = self.flag[:-1]
                usedmap[x][y] = 0
            if maze[x - 1][y] == 0 and usedmap[x - 1][y] == 0:
                usedmap[x][y] = 1
                self.flag += 'w'
                dfs(x - 1, y)
                self.flag = self.flag[:-1]
                usedmap[x][y] = 0
            if maze[x][y + 1] == 0 and usedmap[x][y + 1] == 0:
                usedmap[x][y] = 1
                self.flag += 'd'
                dfs(x, y + 1)
                self.flag = self.flag[:-1]
                usedmap[x][y] = 0
            if maze[x][y - 1] == 0 and usedmap[x][y - 1] == 0:
                usedmap[x][y] = 1
                self.flag += 'a'
                dfs(x, y - 1)
                self.flag = self.flag[:-1]
                usedmap[x][y] = 0
        dfs(sti, stj)
    def seemaze(self):
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 当前位置四个方向的偏移量
        path = []  # 存找到的路径

        def mark(maze, pos):  # 给迷宫maze的位置pos标"2"表示“倒过了”
            maze[pos[0]][pos[1]] = 2

        def passable(maze, pos):  # 检查迷宫maze的位置pos是否可通行
            return maze[pos[0]][pos[1]] == 0

        def find_path(maze, pos, end):
            mark(maze, pos)
            if pos == end:
                print(pos, end=" ")  # 已到达出口，输出这个位置。成功结束
                path.append(pos)
                return True
            for i in range(4):  # 否则按四个方向顺序检查
                nextp = pos[0] + dirs[i][0], pos[1] + dirs[i][1]
                # 考虑下一个可能方向
                if passable(maze, nextp):  # 不可行的相邻位置不管
                    if find_path(maze, nextp, end):  # 如果从nextp可达出口，输出这个位置，成功结束
                        print(pos, end=" ")
                        path.append(pos)
                        return True
            return False

        def see_path(maze, path):  # 使寻找到的路径可视化
            for i, p in enumerate(path):
                if i == 0:
                    maze[p[0]][p[1]] = "E"
                elif i == len(path) - 1:
                    maze[p[0]][p[1]] = "S"
                else:
                    maze[p[0]][p[1]] = 3
            print("\n")
            for r in maze:
                for c in r:
                    if c == 3:
                        print('\033[0;31m' + "*" + " " + '\033[0m', end="")
                    elif c == "S" or c == "E":
                        print('\033[0;34m' + c + " " + '\033[0m', end="")
                    elif c == 2:
                        print('\033[0;32m' + "#" + " " + '\033[0m', end="")
                    elif c == 1:
                        print('\033[0;;40m' + " " * 2 + '\033[0m', end="")
                    else:
                        print(" " * 2, end="")
                print()


        find_path(self.maze, self.startposition, self.endposition)
        see_path(self.maze, path)
def tranmazes(mazes,n=0):
    if n:
        k=n
    else:
        k=int(len(mazes)**0.5)
    maze=[]
    for i in range(0,len(mazes),k):
        maze.append(list(map(int,list(mazes[i:i+k]))))
    return maze

def transtartend(mazes,start,end):
    return mazes.replace(start,"8").replace(end,"9")

def getmazestart(maze):
    for i in range(len(maze)):
        for j in range(len(maze[i])):
            if maze[i][j]==8:
                return (i,j)

def getmazeend(maze):
    for i in range(len(maze)):
        for j in range(len(maze[i])):
            if maze[i][j]==9:
                return (i,j)