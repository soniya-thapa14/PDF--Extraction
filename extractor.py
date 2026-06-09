import fitz
import pandas as pd


class PDFTableExtractor:
   
    def __init__(self, pdf_path, tol=3, gap=30):
        self.doc = fitz.open(pdf_path)
        self.tol = tol
        self.gap = gap
        self.output = []

    def get_lines(self, page):
        lines = []

        for d in page.get_drawings():
            for item in d["items"]:

                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    lines.append((p1.x, p1.y, p2.x, p2.y))

                elif item[0] == "qu":
                    r = item[1].rect

                    lines.extend([
                        (r.x0, r.y0, r.x1, r.y0),
                        (r.x0, r.y1, r.x1, r.y1),
                        (r.x0, r.y0, r.x0, r.y1),
                        (r.x1, r.y0, r.x1, r.y1),
                    ])

                elif item[0] == "re":
                    r = item[1]
                    lines.extend([
                        (r.x0, r.y0, r.x1, r.y0),
                        (r.x0, r.y1, r.x1, r.y1),
                        (r.x0, r.y0, r.x0, r.y1),
                        (r.x1, r.y0, r.x1, r.y1),
                    ])

        return lines

    def classify_lines(self, lines):
        h_lines, v_lines = [], []

        for x1, y1, x2, y2 in lines:
            if abs(y2 - y1) <= self.tol:
                h_lines.append((x1, y1, x2, y2))
            elif abs(x2 - x1) <= self.tol:
                v_lines.append((x1, y1, x2, y2))

        return h_lines, v_lines


    def snap_lines(self, lines):
        def normalize(line):
            x1, y1, x2, y2 = line
            return (x2, y2, x1, y1) if (x1 > x2 or (x1 == x2 and y1 > y2)) else line

        snapped = []

        for line in lines:
            line = normalize(line)

            if not any(
                abs(line[0] - s[0]) <= self.tol and
                abs(line[1] - s[1]) <= self.tol and
                abs(line[2] - s[2]) <= self.tol and
                abs(line[3] - s[3]) <= self.tol
                for s in snapped
            ):
                snapped.append(line)

        return snapped


    def detect_tables(self, h_lines, v_lines):
        all_lines = h_lines + v_lines
        if not all_lines:
            return []

        all_lines.sort(key=lambda l: (l[1] + l[3]) / 2)

        clusters = []
        current = [all_lines[0]]

        for line in all_lines[1:]:
            prev = current[-1]

            prev_y = (prev[1] + prev[3]) / 2
            curr_y = (line[1] + line[3]) / 2

            if abs(curr_y - prev_y) <= self.gap:
                current.append(line)
            else:
                clusters.append(current)
                current = [line]

        clusters.append(current)
        return clusters

    def split_cluster(self, cluster):
        h_lines, v_lines = [], []

        for x1, y1, x2, y2 in cluster:
            if abs(y2 - y1) <= self.tol:
                h_lines.append((x1, y1, x2, y2))
            elif abs(x2 - x1) <= self.tol:
                v_lines.append((x1, y1, x2, y2))

        return h_lines, v_lines

    def build_grid(self, h_lines, v_lines):
        ys, xs = [], []

        for x1, y1, x2, y2 in h_lines:
            if not any(abs(y1 - y) <= self.tol for y in ys):
                ys.append(y1)

        for x1, y1, x2, y2 in v_lines:
            if not any(abs(x1 - x) <= self.tol for x in xs):
                xs.append(x1)

        return sorted(xs), sorted(ys)

    def assign_text(self, page, xs, ys):
        words = page.get_text("words")
        rows = []

        for i in range(len(ys) - 1):
            row = []

            for j in range(len(xs) - 1):
                cell_x0, cell_y0 = xs[j], ys[i]
                cell_x1, cell_y1 = xs[j + 1], ys[i + 1]

                cell_words = []

                for w in words:
                    wx0, wy0, wx1, wy1, text = w[:5]
                    cx = (wx0 + wx1) / 2
                    cy = (wy0 + wy1) / 2

                    if (
                        cell_x0 - self.tol <= cx <= cell_x1 + self.tol and
                        cell_y0 - self.tol <= cy <= cell_y1 + self.tol
                    ):
                        cell_words.append((wx0, text))

                cell_words.sort(key=lambda x: x[0])
                row.append(" ".join(w[1] for w in cell_words))

            rows.append(row)

        return rows

    def get_table_bboxes(self, clusters, gap):
        bboxes = []

        for cluster in clusters:
            xs, ys = [], []

            for line in cluster:
                x1, y1, x2, y2 = line
                xs.extend([x1, x2])
                ys.extend([y1, y2])

            if not xs or not ys:
                continue

            bboxes.append((
                min(xs) - gap,
                min(ys) - gap,
                max(xs) + gap,
                max(ys) + gap
            ))

        return bboxes