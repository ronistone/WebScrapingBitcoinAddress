

while True:
    try:
        line = input("")

        if line.find("  ->  ") != -1:
            print('assert check_bc(\'' + line.split('  ->  ')[0] + '\')')
    except EOFError:
        break
