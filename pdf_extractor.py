from extractor import PDFTableExtractor
from table_extractor import TableExtractor
from text_extractor import TextExtractor


class PDFPipeline:
    def __init__(self, pdf_path, tol=3, gap=30):
        self.pdf_path = pdf_path
        self.extractor = PDFTableExtractor(pdf_path, tol, gap)

        self.table_extractor = TableExtractor(pdf_path, tol, gap)
        self.text_extractor = TextExtractor()

        self.output = ""

    def process_page(self, page, page_num):

        lines = self.extractor.get_lines(page)

        h_lines, v_lines = self.extractor.classify_lines(lines)

        h_snapped = self.extractor.snap_lines(h_lines)
        v_snapped = self.extractor.snap_lines(v_lines)

        clusters = self.extractor.detect_tables(h_snapped, v_snapped)

        table_bboxes = self.extractor.get_table_bboxes(
            clusters,
            gap=2
        )
        blocks = page.get_text("blocks")

        processed_tables = set()

        for block in blocks:
            bx0, by0, bx1, by1, block_text, *_ = block
            inside_table = False

            for idx, bbox in enumerate(table_bboxes):

                if self.text_extractor.is_inside_table(
                    (bx0, by0, bx1, by1),
                    [bbox]
                ):

                    inside_table = True

                    if idx not in processed_tables:

                        h, v = self.extractor.split_cluster(
                            clusters[idx]
                        )

                        xs, ys = self.extractor.build_grid(h, v)

                        table_rows = self.extractor.assign_text(page, xs, ys)

                        if table_rows:
                            self.output += (
                                self.table_extractor.to_markdown(table_rows)
                            )

                            self.output += "\n\n"

                        processed_tables.add(idx)

                    break

            if not inside_table:

                clean_text = self.text_extractor.clean_text(
                    block_text
                )
                if clean_text:
                    self.output += clean_text + "\n\n"
                    
    def extract(self):
        for page_num, page in enumerate(self.extractor.doc, start=1):
            self.process_page(page, page_num)
        return self.output