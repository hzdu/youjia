import requests
from bs4 import BeautifulSoup
import gradio as gr
from urllib.parse import urljoin

headers = {'User-Agent': 'Mozilla/5.0'}
county_links = {}


def get_provinces():
    url = 'https://www.icauto.com.cn/oil/'
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='bordered')
        provinces = {}
        for row in table.find_all('tr')[1:]:
            if (td := row.find('td')) and (a := td.find('a')):
                provinces[a.get_text(strip=True)] = urljoin(url, a['href'])
        return provinces
    except:
        return {}


def get_counties(province):
    global county_links
    county_links.clear()
    provinces = get_provinces()
    if not (link := provinces.get(province)):
        return []

    try:
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        county_list = soup.find('ul', {'id': 'shilist'}).find_all('a')[1:]
        counties = []
        for a in county_list:
            county_name = a.get_text(strip=True)
            county_links[county_name] = urljoin(link, a['href'])
            counties.append(county_name)
        return counties
    except:
        return []


def get_oil_markdown(county):
    if not (link := county_links.get(county)):
        return "**无有效数据**"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='bordered historyOil')

        if not table:
            return "**未找到油价表格**"

        # 动态解析表头（文献5）
        headers = [th.get_text(strip=True) for th in table.select("thead th")]

        # 提取全部数据行（文献7）
        data_rows = []
        for tr in table.select("tr"):
            if not tr.find("th"):  # 排除表头行
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cells:
                    data_rows.append(cells[:len(headers)])  # 对齐列数

        # 构建Markdown表格（文献1）
        if not data_rows:
            return "**无历史油价数据**"

        # 表头与分隔线
        md_table = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]

        # 数据行格式化
        for row in data_rows:
            formatted_row = [f"{float(cell):.2f}" if cell.replace('.', '').isdigit() else cell
                             for cell in row]
            md_table.append("| " + " | ".join(formatted_row) + " |")

        return '\n'.join(md_table)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return f"**数据解析失败：{str(e)}**"


with gr.Blocks(title="全国实时油价查询", css="footer {display: none !important;} #settings-menu {display: none !important;}") as youjia_ui:
    gr.Markdown("# 全国实时油价查询")

    with gr.Row():
        province_dd = gr.Dropdown(label="选择省份", choices=list(get_provinces().keys()))
        county_dd = gr.Dropdown(label="选择县市", interactive=False)

    # 修改输出组件类型
    output = gr.Markdown(
        label="历史油价数据",
        value="选择县市后显示表格..."
    )


    def update_county(province):
        counties = get_counties(province)
        return gr.Dropdown(
            choices=counties,
            interactive=bool(counties),
            visible=bool(counties)
        )


    # 更新回调函数
    def update_output(county):
        return get_oil_markdown(county) if county else "请先选择县市"


    province_dd.change(update_county, inputs=province_dd, outputs=county_dd)
    county_dd.change(update_output, inputs=county_dd, outputs=output)

if __name__ == "__main__":
    youjia_ui.launch(show_api=False, show_error=False)