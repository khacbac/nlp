"""Turn grading_sheet_X.csv into a ready-to-grade grading_sheet_X.xlsx.

The workbook has wrapped text, sized columns, a frozen header, a 1-5
dropdown on "score", highlighted input columns, and a "Hướng dẫn" tab
with the rubric. Upload it to Google Drive and open it with Google Sheets;
the formatting and dropdown carry over.

It only reformats the CSV, so answer ids and key.csv stay as they are.
make_grading_sheet.py calls it; to rebuild the .xlsx files from the
existing CSVs without new ids:
    python grading_xlsx.py
"""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

DATA = Path(__file__).parent / "data"

# column -> (width in characters, header shown to annotators)
LAYOUT = {
    "answer_id": (11, "answer_id"),
    "context": (80, "context (đoạn văn)"),
    "question": (30, "question (câu hỏi)"),
    "gold_answer": (30, "gold_answer (đáp án chuẩn)"),
    "answer": (60, "answer (câu trả lời cần chấm)"),
    "score": (9, "score (1-5)"),
    "note": (30, "note (ghi chú)"),
}
INPUT_COLUMNS = ("score", "note")
HEADINGS = ("Cách chấm", "Thang điểm", "Lưu ý")

INSTRUCTIONS = [
    ("Cách chấm", None),
    ("Mỗi dòng là một câu trả lời. Đọc đoạn văn, câu hỏi và đáp án chuẩn, rồi chấm câu trả lời ở cột answer.", None),
    ("Chỉ điền hai cột tô vàng: score (chọn 1-5 trong danh sách) và note (không bắt buộc).", None),
    ("Không sửa, sắp xếp hay xoá các cột khác, nhất là answer_id.", None),
    ("Chấm từng dòng độc lập, không so sánh với các dòng khác.", None),
    ("", None),
    ("Thang điểm", None),
    ("5", "Đúng và đủ: có nội dung của đáp án chuẩn, không có gì sai."),
    ("4", "Đúng, nhưng thiếu một chi tiết nhỏ hoặc thừa chi tiết không cần."),
    ("3", "Đúng một phần: có một phần đáp án chuẩn, hoặc đúng nhưng mơ hồ."),
    ("2", "Phần lớn sai, chỉ có một ý đúng nhỏ."),
    ("1", "Sai, lạc đề, hoặc mâu thuẫn với đoạn văn."),
    ("", None),
    ("Lưu ý", None),
    ("Đáp án chuẩn là một đoạn trích ngắn từ đoạn văn. Chấm theo ý: câu trả lời có chứa đúng ý đó không, không cần khớp từng chữ.", None),
    ("Giải thích thêm không bị trừ điểm nếu đúng với đoạn văn; thông tin sai hoặc không có trong đoạn văn thì bị trừ.", None),
    ("Chấm nội dung, không chấm độ dài hay văn phong.", None),
    ("Câu trả lời chuyển sang ngôn ngữ khác giữa chừng: vẫn chấm theo nội dung và ghi vào note.", None),
]

HEADER_FILL = PatternFill("solid", fgColor="D9D9D9")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
WRAP_TOP = Alignment(wrap_text=True, vertical="top")


def csv_to_xlsx(csv_path: Path) -> Path:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)

    wb = Workbook()
    ws = wb.active
    ws.title = "Chấm điểm"
    ws.append([LAYOUT.get(c, (20, c))[1] for c in columns])
    for r in rows:
        ws.append([r[c] for c in columns])

    for i, c in enumerate(columns, 1):
        letter = ws.cell(row=1, column=i).column_letter
        ws.column_dimensions[letter].width = LAYOUT.get(c, (20, c))[0]
        head = ws.cell(row=1, column=i)
        head.font = Font(bold=True)
        head.fill = INPUT_FILL if c in INPUT_COLUMNS else HEADER_FILL
        head.alignment = WRAP_TOP
        for cell in ws.iter_rows(min_row=2, min_col=i, max_col=i):
            cell[0].alignment = WRAP_TOP
            if c in INPUT_COLUMNS:
                cell[0].fill = INPUT_FILL
    ws.freeze_panes = "B2"  # header row and answer_id stay visible

    letter = ws.cell(row=1, column=columns.index("score") + 1).column_letter
    dv = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Điểm không hợp lệ",
                        error="Chọn một điểm từ 1 đến 5.")
    dv.add(f"{letter}2:{letter}{len(rows) + 1}")
    ws.add_data_validation(dv)

    guide = wb.create_sheet("Hướng dẫn")
    guide.column_dimensions["A"].width = 6
    guide.column_dimensions["B"].width = 100
    for left, right in INSTRUCTIONS:
        if right is not None:  # a rubric score and its meaning
            guide.append([left, right])
            guide.cell(row=guide.max_row, column=1).font = Font(bold=True)
        elif left in HEADINGS:
            guide.append([None, left])
            guide.cell(row=guide.max_row, column=2).font = Font(bold=True, size=12)
        else:
            guide.append([None, left])
        for cell in guide[guide.max_row]:
            cell.alignment = WRAP_TOP

    out = csv_path.with_suffix(".xlsx")
    wb.save(out)
    return out


def main() -> None:
    paths = sorted(DATA.glob("grading_sheet_*.csv"))
    if not paths:
        raise SystemExit("no grading_sheet_*.csv in data/; run make_grading_sheet.py first.")
    for p in paths:
        print(f"wrote {csv_to_xlsx(p)}")


if __name__ == "__main__":
    main()
