def main():
    # build with deleting pycs disabled
    # search for pycs, export to pycs_all.txt
    # delete all pycs and run program (remove -B from cmd)
    # search for pycs, export to pycs_to_keep.txt
    # run this script (make sure the trim path is correct)
    # done, enable pyc deleting again

    pycs_to_delete = []
    trim_path = r'C:\Users\trial\PycharmProjects\tf2 rich presence\TF2 Rich Presence v2.1.1\resources'

    with open('pycs_all.txt', 'r') as pyc_all_file:
        pycs_all = [path.rstrip('\n') for path in pyc_all_file.readlines()]
    with open('pycs_to_keep.txt', 'r') as pyc_keep_file:
        pycs_to_keep = [path.rstrip('\n') for path in pyc_keep_file.readlines()]

    for any_pyc in pycs_all:
        if any_pyc not in pycs_to_keep:
            pycs_to_delete.append(any_pyc.replace(trim_path, '')[1:])

    pycs_to_delete.sort()
    print(pycs_to_delete)
    with open('pycs_to_delete.txt', 'w') as pycs_to_delete_txt:
        pycs_to_delete_txt.write('\n'.join(pycs_to_delete))


if __name__ == '__main__':
    main()
