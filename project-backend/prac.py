from functools import reduce
#filter
test = [1,2,3,4]
test = list(filter(lambda a: a > 2, test))
print(test)

test = {4: 2, 2: 1, 5: 3}
test = sorted(test.items(), key=lambda item: item[1])
print(test)

given_list = [(1,'a'),(1,'b'),(1,'c')]
given_list = ''.join([''.join(tup[1]) for tup in given_list])
print(given_list)


string = 'abcabcd'
count = {}
for i, each in enumerate(string):
    count[each] = count.get(each, 0) + 1
print(count)

