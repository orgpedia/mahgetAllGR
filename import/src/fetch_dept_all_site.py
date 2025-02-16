import datetime
import json
import sys
from pathlib import Path

import traverser as trav

DeptMap = {
    "01": (
       "Agriculture, Dairy Development, Animal Husbandry and Fisheries Department",
       "mahagri",
    ),
    "02": ("Co-operation, Textiles and Marketing Department", "mahcoop"),
    "04": ("Environment Department", "mahenv"),
    "05": ("Finance Department", "mahfin"),
    "06": ("Food, Civil Supplies and Consumer Protection Department", "mahfood"),
    "07": ("General Administration Department", "mahadmin"),
    "08": ("Higher and Technical Education Department", "mahtech"),
    "29": ("Home Department", "mahhome"),
    "09": ("Housing Department", "mahhouse"),
    "10": ("Industries, Energy and Labour Department", "mahind"),
    "11": ("Information Technology Department", "mahit"),
    "12": ("Law and Judiciary Department", "mahlaw"),
    "33": ("Marathi Language Department", "mahmar"),
    "13": ("Medical Education and Drugs Department", "mahmed"),
    "14": ("Minorities Development Department", "mahmin"),
    "34": ("Other Backward Bahujan Welfare Department", "mahbah"),
    "15": ("Parliamentary Affairs Department", "mahpar"),
    "35": ("Persons with Disabilities Welfare Department", "mahdis"),
    "16": ("Planning Department", "mahplan"),
    "17": ("Public Health Department", "mahhea"),
    "18": ("Public Works Department", "mahpwd"),
    "19": ("Revenue and Forest Department", "mahrev"),
    "20": ("Rural Development Department", "mahrural"),
    "21": ("School Education and Sports Department", "mahedu"), 
    "03": ("Skill Development and Entrepreneurship Department", "mahskill"),
    "22": ("Social Justice and Special Assistance Department", "mahsoc"),
    "26": ("Soil and Water Conservation Department", "mahsoail"),
    "23": ("Tourism and Cultural Affairs Department", "mahtour"),
    "24": ("Tribal Development Department", "mahtrib"),
    "25": ("Urban Development Department", "mahurb"),
    "27": ("Water Resources Department", "mahwater"),
    "28": ("Water Supply and Sanitation Department", "mahsanit"),
    "30": ("Women and Child Development Department", "mahwom"),
}


def get_date_str(date_obj):
    return date_obj.strftime("%d-%b-%Y")


def parse_date(date_str):
    # months = 'jan-feb-mar-apr-may-jun-jul-aug-sep-oct-nov-dec'.split('-')
    d, m, y = date_str.split("-")
    return datetime.date(year=int(y), month=int(m), day=int(d))


def save_doc_infos(doc_infos, output_dir):
    (output_dir / "GRs_log.json").write_text(json.dumps(doc_infos))


MaxPages = 1500
BaseURL = "https://gr.maharashtra.gov.in"


def get_additional_cols(crawler, table_id):
    def get_cell(row_idx, col_idx):
        r, c = row_idx, col_idx
        # increase row count by 2 (idx==0, and idx==1 is header)
        cells = table.query_selector_all(f"tr:nth-child({r + 2}) td:nth-child({c + 1})")
        if len(cells) != 1:
            import pdb
            pdb.set_trace()
        assert len(cells) == 1
        return cells[0].inner_text().strip()

    tables = crawler.get_tables(id_regex=table_id)
    assert len(tables) == 1
    table = tables[0]

    row_count, col_vals = len(table.query_selector_all("tr")), {}
    row_count -= 1  # remove the header

    for idx, field in enumerate(["dept", "text", "code", "date", "size_kb"]):
        col_idx = idx + 1
        cells = [get_cell(row_idx, col_idx) for row_idx in range(row_count)]
        col_vals[field] = cells

    return col_vals


def fetch_all_depts(crawler, dept_code, dept_name, start_page, output_dir):
    def strip_row(row):
        row = [c.strip() if c else c for c in row]
        row[3] = row[3].strip(".")
        return row

    print(f"Output_dir: {output_dir}")

    crawler.click(text="English", ignore_error=True)
    crawler.wait(2)

    crawler.set_form_element("SitePH_ddlDepartmentType", dept_name)
    crawler.wait(3)    


    has_next = crawler.click(text="Next >")
    crawler.wait(5)
    crawler.click(text="< Previous")
    crawler.wait(3)

    if start_page:
        crawler.set_form_element("SitePH_ucPaging_txtPageNo", start_page)
        crawler.wait(5)
        crawler.click(text="Go")
        crawler.wait(3)
        start_page = int(start_page)
    else:
        start_page = 0

    num_pages = crawler.get_text(id_="SitePH_ucPaging_lblTotalPages").strip()

    num_pages = int(num_pages) if num_pages else 0

    abbr = dept_code

    doc_infos = []
    #for start_idx in range(start_page, (num_pages + 1)):
    for start_idx in range(start_page, MaxPages):    
        # crawler.save_screenshot(output_dir / f"{abbr}-{start_idx}.png")
        crawler.save_html(output_dir / f"{abbr}-{start_idx}.html")

        print(f'\n** Processing: {dept_code} [{start_idx}/{num_pages}] **\n')

        tables = crawler.get_tables(id_regex="SitePH_dgvDocuments")
        assert len(tables) == 1
        table = tables[0]

        dt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")
        for row_texts, row_links in zip(table.rows_texts, table.rows_links):
            row_texts = strip_row(row_texts)
            row_texts[-1] = row_links[-1][0].url
            doc_info = dict(zip(table.header, row_texts))
            doc_info["download_dir"] = output_dir.name
            doc_info["html_file"] = f"{abbr}-{start_idx}.html"
            doc_info["download_time_utc"] = dt
            doc_infos.append(doc_info)

        save_doc_infos(doc_infos, output_dir)

        has_next = crawler.click(text="Next >", ignore_error=True)
        if not has_next:
            print(f"Next page not found on Page Number: {start_idx}+")
            break
        crawler.wait(4)
    print(f"Done crawling: {abbr}")


GovResolutionsURL = "https://gr.maharashtra.gov.in/1145/Government-Resolutions"
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {sys.argv[0]} <website_dir> <dept>")
        sys.exit(1)

    today = datetime.date.today()        
    dept_code = sys.argv[2]
    all_dept_codes = {v[1]:v[0] for v in DeptMap.values()}

    start_page = sys.argv[3] if len(sys.argv) > 3 else None
    assert dept_code in all_dept_codes

    website_dir = Path(sys.argv[1]) / dept_code
    website_dir.mkdir(exist_ok=True)

    dept_name = all_dept_codes[dept_code]

    date_str = get_date_str(today)
    existing_dirs = list(website_dir.glob(f"{date_str}*"))
    output_dir = website_dir / f"{date_str}_v{len(existing_dirs)+1}"
    output_dir.mkdir(exist_ok=False)

    crawler = trav.start(GovResolutionsURL, output_dir / "logs.txt")
    fetch_all_depts(crawler, dept_code, dept_name, start_page, output_dir)

    #ctl00$SitePH$ucPaging$txtPageNo
    # get_text(id="SitePH_ucPaging_lblTotalPages")
