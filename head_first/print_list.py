'''
This is the "print_list.py" module and it provide one function called print_list()
which print all entries from the nested lists
'''

def print_list(the_list):
    for each_item in the_list:
        if isinstance(each_item, list):
            print_list(each_item)
        else:
            print(each_item)
            
