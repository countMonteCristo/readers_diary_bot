def reshape(array1d, nrows, ncols):
    '''
    reshape([1,2,3,4,5,6], 2, 3) -> [[1,2,3], [4,5,6]]
    '''
    # assert len(array1d) >= nrows * ncols
    result = []
    for y in range(nrows):
        row = []
        if y*ncols < len(array1d):
            for x in range(ncols):
                index = y*ncols + x
                if index < len(array1d):
                    row.append(array1d[index])
            result.append(row)
        else:
            break

    return result


if __name__ == '__main__':
    assert reshape([1, 2, 3, 4, 5, 6], 2, 3) == [[1, 2, 3], [4, 5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 3, 2) == [[1, 2], [3, 4], [5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 2, 2) == [[1, 2], [3, 4]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 3, 3) == [[1, 2, 3], [4, 5, 6], [7]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 5, 3) == [[1, 2, 3], [4, 5, 6], [7]]
