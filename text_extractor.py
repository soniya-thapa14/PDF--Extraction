def bbox_overlap(b1, b2):
    return not (
        b1[2] < b2[0] or
        b1[0] > b2[2] or
        b1[3] < b2[1] or
        b1[1] > b2[3]
    )


class TextExtractor:
    def is_inside_table(self, block_bbox, table_bboxes):
        bx0, by0, bx1, by1 = block_bbox[:4]

        cx = (bx0 + bx1) / 2
        cy = (by0 + by1) / 2

        for tx0, ty0, tx1, ty1 in table_bboxes:
            if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                return True

        return False

    def clean_text(self, text):
        return text.strip()