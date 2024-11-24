def format_number(num: int | float, add_sign: bool = True) -> str:
    """Format a number a into human-readable format using suffixes like K, M, B, T

    Args:
        num(int|float): The number to format
        add_sign(bool): Whether to append '+' if the number exceeds the threshold

    Returns:
        Appropriately formatted number

    """
    try:
        if num < 1_000:
            return str(num)
        num = float(num)
        value_dict = {
            1_000_000_000_000: "T",
            1_000_000_000: "B",
            1_000_000: "M",
            1_000: "K",
        }

        for k in sorted(value_dict.keys(), reverse=True):
            if num >= k:
                f_value = num / k
                suffix = value_dict[k]
                if add_sign and num > k:
                    suffix += "+"
                return f"{f_value:.0f}{suffix}"

        return str(num)

    except (ValueError, TypeError):
        return str(num)
