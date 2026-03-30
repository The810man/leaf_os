from typing import List


def fit_frame_to_box(frame: List[str], max_w: int, max_h: int, char_aspect: float = 2.0) -> List[str]:
    if not frame or max_w <= 0 or max_h <= 0:
        return []

    src_h = len(frame)
    src_w = max((len(line) for line in frame), default=0)
    if src_h == 0 or src_w == 0:
        return []

    padded = [line.ljust(src_w) for line in frame]

    scale_h = src_h / max_h if src_h > max_h else 1.0
    out_h = max(1, min(max_h, int(src_h / scale_h)))

    out_w_from_height = max(1, int(src_w / scale_h))

    if out_w_from_height < max_w:
        out_w = max_w
    else:
        out_w = min(max_w, out_w_from_height)

    result = []
    for oy in range(out_h):
        sy0 = int(oy * src_h / out_h)
        sy1 = max(sy0 + 1, int((oy + 1) * src_h / out_h))
        row_chars = []

        for ox in range(out_w):
            sx0 = int(ox * src_w / out_w)
            sx1 = max(sx0 + 1, int((ox + 1) * src_w / out_w))

            best = " "
            for sy in range(sy0, min(sy1, src_h)):
                for sx in range(sx0, min(sx1, src_w)):
                    ch = padded[sy][sx]
                    if ch != " ":
                        best = ch
                        break
                if best != " ":
                    break

            row_chars.append(best)

        result.append("".join(row_chars).rstrip())

    return result
