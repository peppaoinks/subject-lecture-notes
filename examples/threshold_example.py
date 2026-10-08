"""Original teaching fixture; not a measured course experiment."""


def count_at_least(scores, tau=60):
    count = 0
    for score in scores:
        if score >= tau:
            count += 1
    return count


if __name__ == "__main__":
    cases = [([59, 60, 80], 2), ([], 0), ([59, 60, 60], 2), ([60], 1)]
    for values, expected in cases:
        actual = count_at_least(values)
        assert actual == expected, (values, actual, expected)
        print(f"scores={values}, count={actual}")
