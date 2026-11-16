"""Combine grading_sheet_A.csv ... _D.csv into one workbook, grading_sheets.xlsx.

The workbook has a "Hướng dẫn" tab with the rubric, then one tab per
annotator (A, B, C, D) with wrapped text, sized columns, a frozen header,
a 1-5 dropdown on "score" and highlighted input columns. Upload it to
Google Drive and open it with Google Sheets; the formatting and dropdown
carry over.

Everyone with access can see every tab, so annotators can see each
other's scores; the team agreed to grade only their own tab.

It only reformats the CSVs, so answer ids and key.csv stay as they are.
make_grading_sheet.py calls it; to rebuild the workbook from the existing
CSVs without new ids:
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
    ("5", "Có đủ ý chính, và mọi thông tin trong câu trả lời đều có trong đoạn văn."),
    ("4", "Có đủ ý chính, nhưng thiếu một chi tiết nhỏ, hoặc có một ý suy diễn thêm không có trong đoạn văn (không sai với đoạn văn)."),
    ("3", "Chỉ có một phần ý chính, hoặc trả lời chung chung không nêu được ý cụ thể, hoặc có đủ ý chính nhưng kèm một thông tin sai so với đoạn văn."),
    ("2", "Không có ý chính, chỉ có ý phụ đúng (đúng với đoạn văn nhưng không trả lời câu hỏi)."),
    ("1", "Sai, lạc đề, bịa, hoặc ý chính mâu thuẫn với đoạn văn."),
    ("", None),
    ("Lưu ý", None),
    ("Ý chính là phần trả lời trực tiếp câu hỏi, thường chính là ý của đáp án chuẩn. Chấm theo ý, không cần khớp từng chữ. Làm hai bước: (1) có ý chính không, (2) phần còn lại có đúng với đoạn văn không.", None),
    ("Thông tin thêm: có trong đoạn văn thì không trừ, dù dài; suy diễn không có trong đoạn văn thì tối đa 4; sai so với đoạn văn thì tối đa 3.", None),
    ("Chấm nội dung, không chấm độ dài hay văn phong.", None),
    ("Đáp án chuẩn sai, không trả lời đúng câu hỏi, hoặc đoạn văn không có đáp án: chấm theo đoạn văn và ghi gold_sai vào note. Nếu đoạn văn không có đáp án và câu trả lời nói đúng như vậy thì cho 5.", None),
    ("Phân vân giữa hai mức thì chọn mức thấp hơn.", None),
    ("Câu trả lời chuyển sang ngôn ngữ khác giữa chừng: vẫn chấm theo nội dung và ghi vào note.", None),
]

HEADER_FILL = PatternFill("solid", fgColor="D9D9D9")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
WRAP_TOP = Alignment(wrap_text=True, vertical="top")


def add_grading_tab(wb: Workbook, csv_path: Path, title: str) -> int:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)

    ws = wb.create_sheet(title)
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
    return len(rows)


def add_guide_tab(wb: Workbook, names: list[str]) -> None:
    guide = wb.active
    guide.title = "Hướng dẫn"
    guide.column_dimensions["A"].width = 6
    guide.column_dimensions["B"].width = 100
    own_tab = (f"Mỗi người chấm đúng tab mang tên mình ({', '.join(names)}); "
               "không mở hay xem điểm ở tab của người khác.", None)
    lines = INSTRUCTIONS[:1] + [own_tab] + INSTRUCTIONS[1:]
    for left, right in lines:
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


def build_workbook(csv_paths: list[Path], out: Path) -> Path:
    """One tab per grading_sheet_X.csv, named X, after a guide tab."""
    names = [p.stem.removeprefix("grading_sheet_") for p in csv_paths]
    wb = Workbook()
    add_guide_tab(wb, names)
    for path, name in zip(csv_paths, names):
        n = add_grading_tab(wb, path, name)
        print(f"  tab {name}: {n} rows")
    wb.save(out)
    return out


def main() -> None:
    paths = sorted(DATA.glob("grading_sheet_*.csv"))
    if not paths:
        raise SystemExit("no grading_sheet_*.csv in data/; run make_grading_sheet.py first.")
    print(f"wrote {build_workbook(paths, DATA / 'grading_sheets.xlsx')}")


if __name__ == "__main__":
    main()
