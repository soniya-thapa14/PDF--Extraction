from table_extractor import TableExtractor
from pdf_extractor import PDFPipeline

extractor = TableExtractor("sample-tables.pdf")

tables = extractor.extract()

output = ""

for i, table in enumerate(tables, start=1):
    output += f"## Table {i}\n\n"
    output += extractor.to_markdown(table)
    output += "\n\n"

with open("tables.md", "w", encoding="utf-8") as f:
    f.write(output)
print("saved to table")

pipeline = PDFPipeline("sample-tables.pdf")

result = pipeline.extract()

with open("output.md", "w", encoding="utf-8") as f:
    f.write(result)

print("Saved to output.md")