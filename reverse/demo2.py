from devil import *

list1 = ['d', 'n', 'c', 'e', 'y', 'h', 'w', 'l', 'i', ']', 'a', 'm', 'f', 'g', ']', 'k', 'q', ']', 'd', 'w', 'l', 'l',
         '{']

list2 = list(map(ord, list1))
print(list2)
SimpleCrack(list2)