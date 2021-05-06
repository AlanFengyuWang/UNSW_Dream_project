def join_tuple_in_list():
    given_list = [(1, 'a'), (2, 'b'), (4, 'c')]
    joined_str = ''.join(''.join(tup[1]) for tup in given_list)
    print(joined_str)

if __name__ == '__main__':
    test = {2: 3, 1: 4, 5: 3, 0: 4}
    join_tuple_in_list()
