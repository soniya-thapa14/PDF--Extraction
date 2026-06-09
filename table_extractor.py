from extractor import PDFTableExtractor

class TableExtractor:
    def __init__(self,pdf_path, tol=3, gap=30):
        self.tol = tol
        self.gap = gap
        self.extractor = PDFTableExtractor(pdf_path, tol, gap)
    def extract_tables(self, page):
        lines = self.extractor.get_lines(page)
        h_lines, v_lines = self.extractor.classify_lines(lines)

        h_snapped = self.extractor.snap_lines(h_lines)
        v_snapped = self.extractor.snap_lines(v_lines)

        clusters = self.extractor.detect_tables(h_snapped, v_snapped)

        tables = []

        for cluster in clusters:
            h, v = self.extractor.split_cluster(cluster)
            xs, ys = self.extractor.build_grid(h, v)
            table = self.extractor.assign_text(page, xs, ys)

            if table:
                tables.append(table)

        return tables

    def to_markdown(self, table):
        import pandas as pd
        df = pd.DataFrame(table[1:], columns=table[0])
        return df.to_markdown(index=False)
    
    def extract(self):
        all_tables = []

        for page in self.extractor.doc:
            tables = self.extract_tables(page)
            all_tables.extend(tables)

        return all_tables