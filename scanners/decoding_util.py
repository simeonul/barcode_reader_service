class DecodingUtil:
    BAR_DIGIT_PATTERNS = {
        (3, 2, 1, 1): {"digit": "0", "parity": "O"},
        (2, 2, 2, 1): {"digit": "1", "parity": "O"},
        (2, 1, 2, 2): {"digit": "2", "parity": "O"},
        (1, 4, 1, 1): {"digit": "3", "parity": "O"},
        (1, 1, 3, 2): {"digit": "4", "parity": "O"},
        (1, 2, 3, 1): {"digit": "5", "parity": "O"},
        (1, 1, 1, 4): {"digit": "6", "parity": "O"},
        (1, 3, 1, 2): {"digit": "7", "parity": "O"},
        (1, 2, 1, 3): {"digit": "8", "parity": "O"},
        (3, 1, 1, 2): {"digit": "9", "parity": "O"},
        (1, 1, 2, 3): {"digit": "0", "parity": "E"},
        (1, 2, 2, 2): {"digit": "1", "parity": "E"},
        (2, 2, 1, 2): {"digit": "2", "parity": "E"},
        (1, 1, 4, 1): {"digit": "3", "parity": "E"},
        (2, 3, 1, 1): {"digit": "4", "parity": "E"},
        (1, 3, 2, 1): {"digit": "5", "parity": "E"},
        (4, 1, 1, 1): {"digit": "6", "parity": "E"},
        (2, 1, 3, 1): {"digit": "7", "parity": "E"},
        (3, 1, 2, 1): {"digit": "8", "parity": "E"},
        (2, 1, 1, 3): {"digit": "9", "parity": "E"}
    }

    FIRST_DIGIT_PATTERNS = {
        "OOOOOO": "0",
        "OOEOEE": "1",
        "OOEEOE": "2",
        "OOEEEO": "3",
        "OEOOEE": "4",
        "OEEOOE": "5",
        "OEEEOO": "6",
        "OEOEOE": "7",
        "OEOEEO": "8",
        "OEEOEO": "9"
    }

    @staticmethod
    def row_to_lengths_array(row):
        lengths = []
        current_digit = row[0]
        current_length = 1
        for i in range(1, len(row)):
            if row[i] == current_digit:
                current_length += 1
            else:
                lengths.append(current_length)
                current_digit = row[i]
                current_length = 1
        lengths.pop(0)
        return lengths[3:27], lengths[32:56]

    @staticmethod
    def adjust_bar_length(length):
        if length < 1.5 / 7:
            return 1
        if length < 2.5 / 7:
            return 2
        elif length < 3.5 / 7:
            return 3
        else:
            return 4

    @staticmethod
    def decode_digit(bar1, bar2, bar3, bar4):
        total = float(bar1 + bar2 + bar3 + bar4)
        bar1_adj = DecodingUtil.adjust_bar_length(bar1 / total)
        bar2_adj = DecodingUtil.adjust_bar_length(bar2 / total)
        bar3_adj = DecodingUtil.adjust_bar_length(bar3 / total)
        bar4_adj = DecodingUtil.adjust_bar_length(bar4 / total)
        pattern_key = (bar1_adj, bar2_adj, bar3_adj, bar4_adj)
        pattern = DecodingUtil.BAR_DIGIT_PATTERNS.get(pattern_key)
        return {"digit": pattern["digit"], "parity": pattern["parity"]}

    @staticmethod
    def decode_first_digit(encoding):
        pattern_key = ''.join(code['parity'] for code in encoding)
        return DecodingUtil.FIRST_DIGIT_PATTERNS.get(pattern_key)
