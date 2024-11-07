# 破解key
s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
s1 = 'moectf'.upper()
s2 = 'scsfct'.upper()
key = ''
for i in range(len(s1)):
    key += s[(s.find(s2[i]) - s.find(s1[i])) % 26]
print(key)