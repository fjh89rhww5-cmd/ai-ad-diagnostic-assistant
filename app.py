import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from html import escape as html_escape
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="AI 广告投放诊断助手", layout="wide")
st.markdown(
    """
    <style>
    :root {
      --ink: #2d3448;
      --muted: #7d879b;
      --line: #e7eaf2;
      --canvas: #f7f5fc;
      --purple: #7376d8;
      --purple-dark: #565bb8;
      --purple-soft: #f0f0ff;
      --green: #34866e;
      --green-soft: #e8f5ef;
      --primary-color: #7376d8;
    }
    [data-testid="stAppViewContainer"] { background: var(--canvas); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1480px; padding-top: 1.7rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }
    .app-heading {
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      margin: 0 0 1.2rem; padding: 1.15rem 1.35rem;
      border: 1px solid #e3e7f4; border-radius: 16px;
      background: linear-gradient(115deg, #fff 0%, #f7f8ff 100%);
    }
    .app-heading h1 { margin: .12rem 0 .28rem; font-size: 1.75rem; }
    .app-heading p { margin: 0; color: var(--muted); font-size: .92rem; }
    .app-eyebrow { color: var(--purple-dark); font-size: .72rem; font-weight: 700; letter-spacing: .08em; }
    .app-chip {
      flex: 0 0 auto; padding: .48rem .72rem; border: 1px solid #dfe3fb;
      border-radius: 999px; background: #f5f6ff; color: var(--purple-dark);
      font-size: .75rem; font-weight: 650;
    }
    .section-kicker {
      margin: 1.1rem 0 .55rem; color: var(--purple-dark);
      font-size: .92rem; font-weight: 700;
    }
    .diagnosis-label {
      display: inline-block; margin: .35rem 0 .15rem; padding: .35rem .65rem;
      border-radius: 999px; font-size: .78rem; font-weight: 700;
    }
    .diagnosis-observation { background: var(--purple-soft); color: var(--purple-dark); }
    .diagnosis-hypothesis { background: var(--purple-soft); color: var(--purple-dark); }
    .diagnosis-action { background: var(--green-soft); color: var(--green); }
    .rule-count { color: var(--purple-dark); font-size: .75rem; font-weight: 650; text-align: right; }
    .severity-item {
      display: flex; align-items: flex-start; gap: .65rem; margin: .45rem 0;
      padding: .68rem .78rem; border: 1px solid transparent; border-radius: 10px;
      font-size: .88rem; line-height: 1.55;
    }
    .severity-tag {
      flex: 0 0 auto; min-width: 3.6rem; padding: .12rem .42rem;
      border-radius: 999px; text-align: center; font-size: .7rem; font-weight: 750;
    }
    .severity-yellow { background: #fff9df; border-color: #f2e7b8; color: #705b1d; }
    .severity-yellow .severity-tag { background: #f8e7a2; color: #70550b; }
    .severity-orange { background: #fff1e4; border-color: #f3d6ba; color: #804813; }
    .severity-orange .severity-tag { background: #f6c18d; color: #713d0c; }
    .severity-red { background: #fff0f0; border-color: #f0cccc; color: #843b42; }
    .severity-red .severity-tag { background: #f3b8bc; color: #7a2e35; }
    .severity-green { background: var(--green-soft); border-color: #d1e8dc; color: #356f5c; }
    .severity-green .severity-tag { background: #cfe9dc; color: #2b6d55; }
    .severity-summary { padding: .25rem .55rem; border-radius: 999px; font-size: .7rem; font-weight: 700; text-align: center; }
    .severity-summary.severity-yellow { background: #fff4c7; color: #70550b; }
    .severity-summary.severity-orange { background: #ffe3c8; color: #713d0c; }
    .severity-summary.severity-red { background: #f9d9db; color: #7a2e35; }
    .severity-summary.severity-green { background: #dff0e7; color: #2b6d55; }
    .overview-attention {
      display: flex; align-items: center; justify-content: space-between; gap: .5rem;
      min-height: 4.2rem; padding: .75rem .9rem; border: 1px solid transparent;
      border-radius: 11px;
    }
    .overview-attention span { font-size: .78rem; font-weight: 700; }
    .overview-attention strong { font-size: 1.45rem; line-height: 1; }
    .overview-attention small { font-size: .68rem; }
    .top-attention {
      margin-top: .85rem; padding: .75rem .9rem; border: 1px solid #e5e3f6;
      border-radius: 10px; background: #f7f6ff; color: #4d527f;
      font-size: .86rem; line-height: 1.55;
    }
    .funnel-flow {
      display: grid; grid-template-columns: minmax(0, 1fr) 2rem minmax(0, 1fr) 2rem minmax(0, 1fr);
      align-items: center; gap: .55rem; margin: .75rem 0 .5rem;
    }
    .overview-chart-note {
      padding: .9rem 1rem; border: 1px solid #e7e6fa;
      border-radius: 12px; background: #f8f8ff; color: #606783;
      font-size: .84rem; line-height: 1.65;
    }
    .overview-chart-note strong { display: block; margin-bottom: .35rem; color: var(--ink); }
    .funnel-stage {
      min-width: 0; min-height: 8.4rem; padding: .9rem 1rem;
      border: 1px solid var(--line); border-top: 3px solid var(--purple);
      border-radius: 12px; background: #fff; box-shadow: 0 5px 18px #303b5508;
    }
    .funnel-stage-name { color: var(--muted); font-size: .8rem; font-weight: 650; line-height: 1.4; }
    .funnel-stage-value { margin: .55rem 0 .45rem; color: var(--purple-dark); font-size: 1.55rem; font-weight: 750; }
    .funnel-stage-count { color: #737d91; font-size: .76rem; line-height: 1.5; overflow-wrap: anywhere; }
    .funnel-arrow { color: var(--purple); font-size: 1.55rem; font-weight: 700; text-align: center; }
    [data-testid="stFileUploaderDropzone"] {
      border: 1px dashed #bfc8e9; border-radius: 12px; background: #fbfcff;
    }
    [data-testid="stMetric"] {
      height: 100%; padding: .9rem 1rem; border: 1px solid var(--line);
      border-radius: 13px; background: #fff; box-shadow: 0 5px 18px #303b5509;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); font-weight: 700; }
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
      border-color: var(--line); border-radius: 9px; background: #fff;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
      border-color: var(--line); border-radius: 13px; background: #fff;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
      gap: .35rem; border-bottom: 1px solid var(--line);
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
      height: 2.7rem; padding: 0 .9rem; border-radius: 9px 9px 0 0;
      color: #687187; font-weight: 600;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
      background: var(--purple-soft); color: var(--purple-dark);
    }
    button[kind="primary"], [data-testid="stBaseButton-primary"] {
      border-color: var(--purple) !important;
      background: var(--purple) !important;
      color: #fff !important;
    }
    button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
      border-color: var(--purple-dark) !important;
      background: var(--purple-dark) !important;
      color: #fff !important;
    }
    button[kind="secondary"], [data-testid="stBaseButton-secondary"],
    [data-testid="stFileUploader"] button {
      border-color: #dfe3fb !important;
      background: var(--purple-soft) !important;
      color: var(--purple-dark) !important;
    }
    button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stFileUploader"] button:hover {
      border-color: #c9cdf1 !important;
      background: #e8e9ff !important;
      color: var(--purple-dark) !important;
    }
    [data-testid="stAlert"] {
      border: 1px solid #cfe7dc !important;
      border-radius: 11px;
      background: #edf7f1 !important;
    }
    [data-testid="stAlert"] > div {
      border-radius: 11px;
      background: #edf7f1 !important;
      color: #356f5c !important;
    }
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
      color: #356f5c !important;
    }
    [data-testid="stAlert"] svg { color: #48836d !important; fill: #48836d !important; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 11px; overflow: hidden; }
    @media (max-width: 760px) {
      .block-container { padding: 1rem .8rem 2rem; }
      .app-heading { align-items: flex-start; flex-direction: column; padding: 1rem; }
      .app-heading h1 { font-size: 1.4rem; }
      .app-chip { align-self: flex-start; }
      [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .65rem; }
      [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 calc(50% - .65rem); min-width: calc(50% - .65rem) !important;
      }
      .funnel-flow { grid-template-columns: 1fr; gap: .25rem; }
      .funnel-stage { min-height: auto; }
      .funnel-arrow { transform: rotate(90deg); font-size: 1.3rem; line-height: 1; }
    }
    @media (max-width: 480px) {
      [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex-basis: 100%; min-width: 100% !important;
      }
    }
    </style>
    <div class="app-heading">
      <div>
        <div class="app-eyebrow">广告效果分析工作台</div>
        <h1>AI 广告投放诊断助手</h1>
        <p>上传一份广告报表，我们一起看看预算、流量和转化环节有哪些值得关注。</p>
      </div>
      <span class="app-chip">支持 CSV · Excel</span>
    </div>
    """,
    unsafe_allow_html=True,
)


FIELD_INFO = {
    "campaign_name": {
        "label": "广告系列名称（必需）",
        "required": True,
        "aliases": [
            "campaign_name", "campaign name", "campaign", "广告系列",
            "广告系列名称", "计划名称", "广告计划",
        ],
    },
    "duration_days": {
        "label": "投放周期（天）（可选）",
        "required": False,
        "aliases": [
            "duration_days", "duration days", "duration", "day", "days",
            "投放周期", "投放周期（天）", "周期（天）", "投放周期天数",
            "持续天数", "投放天数", "统计天数",
        ],
    },
    "audience_segment": {
        "label": "投放人群（可选）",
        "required": False,
        "aliases": [
            "audience", "audience segment", "audience_segment",
            "受众", "受众人群", "投放人群", "人群包",
        ],
    },
    "landing_page": {
        "label": "落地页版本（可选）",
        "required": False,
        "aliases": [
            "landing page", "landing_page", "landing page version",
            "落地页", "落地页版本", "页面版本",
        ],
    },
    "creative_type": {
        "label": "素材类型（可选）",
        "required": False,
        "aliases": [
            "creative type", "creative_type", "ad format", "素材类型",
            "素材形式", "广告形式",
        ],
    },
    "placement": {
        "label": "投放位置（可选）",
        "required": False,
        "aliases": [
            "placement", "ad placement", "投放位置", "广告版位", "版位",
        ],
    },
    "objective": {
        "label": "投放目标（可选）",
        "required": False,
        "aliases": [
            "objective", "campaign objective", "投放目标", "广告目标",
        ],
    },
    "cost": {
        "label": "花费（必需）",
        "required": True,
        "aliases": [
            "cost", "spend", "amount spent", "花费", "消耗",
            "广告花费", "总花费", "广告消耗",
        ],
    },
    "impressions": {
        "label": "曝光次数（必需）",
        "required": True,
        "aliases": ["impressions", "impression", "曝光", "曝光次数"],
    },
    "clicks": {
        "label": "点击次数（必需）",
        "required": True,
        "aliases": ["clicks", "click", "点击", "点击次数"],
    },
    "pv": {
        "label": "页面浏览次数 PV（可选）",
        "required": False,
        "aliases": [
            "pv", "page view", "page views", "pageviews",
            "页面浏览", "页面浏览量", "浏览量",
        ],
    },
    "uv": {
        "label": "访问用户数 UV（可选）",
        "required": False,
        "aliases": [
            "uv", "unique visitor", "unique visitors", "visitors",
            "访问用户", "独立访客", "访客数",
        ],
    },
    "paid_uv": {
        "label": "付费用户数 Paid UV（可选）",
        "required": False,
        "aliases": [
            "paid uv", "paid_uv", "paid users", "付费用户",
            "付费用户数", "付费uv",
        ],
    },
    "gmv": {
        "label": "成交金额 GMV（可选）",
        "required": False,
        "aliases": [
            "gmv", "revenue", "sales value", "成交金额",
            "成交额", "销售额",
        ],
    },
}

REQUIRED_FIELDS = [
    field for field, info in FIELD_INFO.items() if info["required"]
]
NUMERIC_FIELDS = [
    "cost", "impressions", "clicks", "pv", "uv", "paid_uv", "gmv"
]
INPUT_NUMERIC_FIELDS = NUMERIC_FIELDS + ["duration_days"]
CATEGORY_FIELDS = [
    "audience_segment", "landing_page", "creative_type", "placement", "objective"
]
CATEGORY_LABELS = {
    "audience_segment": "投放人群",
    "landing_page": "落地页版本",
    "creative_type": "素材类型",
    "placement": "投放位置",
    "objective": "投放目标",
}


def normalize_header(value):
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", value)


def find_matching_headers(headers, aliases):
    normalized_aliases = {normalize_header(alias) for alias in aliases}
    return [
        header
        for header in headers
        if normalize_header(header) in normalized_aliases
    ]


saved_upload = st.session_state.get("ad_data_file")
upload_expanded = saved_upload is None
upload_section_title = (
    "第一步 · 上传广告数据"
    if saved_upload is None
    else f"第一步 · 已上传 {saved_upload.name}（点击更换）"
)
with st.expander(upload_section_title, expanded=upload_expanded):
    uploaded_file = st.file_uploader(
        "选择广告数据文件", type=["csv", "xlsx"], key="ad_data_file"
    )

if uploaded_file is None:
    st.markdown(
        '<div class="section-kicker">开始一次广告诊断</div>',
        unsafe_allow_html=True,
    )
    st.caption("可以上传自己的报表，也可以先下载虚构示例数据体验完整流程。")
    upload_guide, sample_guide = st.columns([1.2, 1])
    with upload_guide.container(border=True):
        st.markdown("#### 上传自己的广告报表")
        st.write("支持 CSV 和 Excel（.xlsx）。飞书表格可以先导出为这两种格式。")
        st.caption("必需字段：广告系列名称、花费、曝光次数、点击次数。")
    with sample_guide.container(border=True):
        st.markdown("#### 先用示例数据试试看")
        st.write("示例内容为虚构广告数据，不含真实账户或公司信息。")
        st.caption("下载后，把文件拖入上方上传框，再确认字段对应关系。")
        sample_path = Path(__file__).with_name("sample_data.csv")
        if sample_path.is_file():
            st.download_button(
                "下载虚构示例 CSV",
                data=sample_path.read_bytes(),
                file_name="AI广告诊断_虚构示例.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        else:
            st.warning("当前没有找到示例数据文件。")
    st.stop()

file_bytes = uploaded_file.getvalue()
file_hash = hashlib.sha256(file_bytes).hexdigest()[:12]
file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

if file_extension == "xlsx":
    try:
        workbook = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
    except Exception as error:
        st.error(f"无法读取 Excel 文件，请确认文件未损坏。错误信息：{error}")
        st.stop()

    if not workbook.sheet_names:
        st.error("这个 Excel 文件没有工作表，请检查文件内容。")
        st.stop()

    selected_sheet = st.selectbox(
        "选择要分析的工作表",
        workbook.sheet_names,
        key=f"sheet_{file_hash}",
    )
    file_fingerprint = f"{file_hash}_{selected_sheet}"
    try:
        raw_data = pd.read_excel(
            io.BytesIO(file_bytes), sheet_name=selected_sheet, engine="openpyxl"
        )
    except Exception as error:
        st.error(f"无法读取所选工作表，请检查表格内容。错误信息：{error}")
        st.stop()
else:
    file_fingerprint = file_hash
    try:
        raw_data = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            raw_data = pd.read_csv(io.BytesIO(file_bytes), encoding="gb18030")
        except Exception as error:
            st.error(
                f"无法识别 CSV 的文字编码，请另存为 UTF-8 后重试。错误信息：{error}"
            )
            st.stop()
    except Exception as error:
        st.error(f"无法读取 CSV，请确认文件格式正确。错误信息：{error}")
        st.stop()

if st.session_state.get("mapping_file_fingerprint") != file_fingerprint:
    st.session_state["mapping_file_fingerprint"] = file_fingerprint
    st.session_state.pop("confirmed_mapping", None)

if raw_data.empty:
    st.error("这个 CSV 没有数据行，请检查文件内容。")
    st.stop()

st.caption(
    f"已读取 {len(raw_data)} 行、{len(raw_data.columns)} 列。"
    "额外列可以保留，系统只使用你确认的字段计算。"
)

headers = list(raw_data.columns)
placeholder_required = "— 请选择对应列 —"
placeholder_optional = "— 不使用 —"
suggestions = {
    field: find_matching_headers(headers, info["aliases"])
    for field, info in FIELD_INFO.items()
}

saved_mapping = st.session_state.get("confirmed_mapping", {})
mapping_is_current = (
    st.session_state.get("confirmed_mapping_fingerprint") == file_fingerprint
    and isinstance(saved_mapping, dict)
    and all(
        (
            None
            if st.session_state.get(
                f"mapping_{file_fingerprint}_{field}",
                placeholder_required if info["required"] else placeholder_optional,
            ) == (placeholder_required if info["required"] else placeholder_optional)
            else st.session_state.get(f"mapping_{file_fingerprint}_{field}")
        ) == saved_mapping.get(field)
        for field, info in FIELD_INFO.items()
    )
)

mapping_section_title = (
    "第二步 · 字段已确认（点击修改）"
    if mapping_is_current
    else "第二步 · 确认表格字段"
)
with st.expander(mapping_section_title, expanded=not mapping_is_current):
    st.caption(
        "系统已按列名预先匹配。请核对必需字段；可选字段没有对应列时保持“不使用”。"
        "已分配的列会从其他字段选项中隐藏。"
    )
    with st.container(border=True):
        if st.session_state.get("mapping_widget_fingerprint") != file_fingerprint:
            reserved_headers = set()
            for field, info in FIELD_INFO.items():
                matches = suggestions[field]
                placeholder = placeholder_required if info["required"] else placeholder_optional
                default_value = matches[0] if len(matches) == 1 else placeholder
                if default_value in reserved_headers:
                    default_value = placeholder
                elif default_value != placeholder:
                    reserved_headers.add(default_value)
                st.session_state[f"mapping_{file_fingerprint}_{field}"] = default_value
            st.session_state["mapping_widget_fingerprint"] = file_fingerprint

        selected_mapping = {}
        for field, info in FIELD_INFO.items():
            is_required = info["required"]
            placeholder = placeholder_required if is_required else placeholder_optional
            selection_key = f"mapping_{file_fingerprint}_{field}"
            selected_value = st.session_state.get(selection_key, placeholder)
            selected_by_other_fields = {
                st.session_state.get(f"mapping_{file_fingerprint}_{other_field}")
                for other_field in FIELD_INFO
                if other_field != field
            }
            options = [placeholder] + [
                header
                for header in headers
                if header not in selected_by_other_fields or header == selected_value
            ]
            if selected_value not in options:
                selected_value = placeholder

            selected_value = st.selectbox(
                info["label"],
                options,
                index=options.index(selected_value),
                key=selection_key,
                help=(
                    "必需字段，需选择一列。已分配给其他字段的列会从此列表中隐藏。"
                    if is_required
                    else "可选字段。没有对应列时保持“不使用”；已分配给其他字段的列会隐藏。"
                ),
            )
            selected_mapping[field] = None if selected_value == placeholder else selected_value

            if len(suggestions[field]) > 1:
                st.warning(
                    f"{info['label']}匹配到多列，请确认你选择的是正确的原始数据列。"
                )

        submitted = st.button("确认字段并分析", type="primary")

if submitted:
    st.session_state["confirmed_mapping"] = selected_mapping
    st.session_state["confirmed_mapping_fingerprint"] = file_fingerprint
    st.session_state.pop("duration_resolution_fingerprint", None)
    st.session_state.pop("duration_resolution_choice", None)
    st.session_state.pop("duration_override_days", None)
    st.session_state.pop("ai_diagnosis_text", None)
    st.session_state.pop("ai_diagnosis_fingerprint", None)
    st.rerun()

if (
    st.session_state.get("confirmed_mapping_fingerprint") != file_fingerprint
    or "confirmed_mapping" not in st.session_state
):
    st.info("检查上方字段对应关系，然后点击“确认字段并分析”。")
    st.stop()

if st.session_state["confirmed_mapping"] != selected_mapping:
    st.info("字段选择已变化，请点击“确认字段并分析”后再查看分析结果。")
    st.stop()

mapping = st.session_state["confirmed_mapping"]
missing_required = [
    field for field in REQUIRED_FIELDS if not mapping.get(field)
]

if missing_required:
    missing_labels = [FIELD_INFO[field]["label"] for field in missing_required]
    st.error("请为这些必需字段选择对应列：" + "、".join(missing_labels))
    st.stop()

used_source_columns = [
    source for source in mapping.values() if source is not None
]
duplicate_sources = sorted(
    {
        source
        for source in used_source_columns
        if used_source_columns.count(source) > 1
    }
)

if duplicate_sources:
    st.error(
        "同一列被分配给了多个字段，请检查选择："
        + "、".join(duplicate_sources)
    )
    st.stop()

data = pd.DataFrame(index=raw_data.index)
data["campaign_name"] = (
    raw_data[mapping["campaign_name"]].astype("string").str.strip()
)
data["campaign_name"] = data["campaign_name"].replace("", pd.NA)

for field in CATEGORY_FIELDS:
    if mapping.get(field):
        values = raw_data[mapping[field]].astype("string").str.strip()
        data[field] = values.replace("", pd.NA).fillna("未填写")

selected_numeric_fields = [
    field for field in INPUT_NUMERIC_FIELDS if mapping.get(field)
]
numeric_input_missing = {}
invalid_numeric_values = pd.Series(False, index=raw_data.index)

for field in selected_numeric_fields:
    source_values = raw_data[mapping[field]].astype("string").str.strip()
    is_blank = source_values.isna() | source_values.eq("")
    values = source_values
    values = (
        values
        .str.replace(",", "", regex=False)
        .str.replace("￥", "", regex=False)
        .str.replace("¥", "", regex=False)
        .str.replace("$", "", regex=False)
    )
    data[field] = pd.to_numeric(values, errors="coerce")
    numeric_input_missing[field] = int(is_blank.sum())
    invalid_numeric_values |= ~is_blank & data[field].isna()

blank_campaign_rows = data["campaign_name"].isna()
if blank_campaign_rows.any():
    row_numbers = [str(index + 2) for index in data.index[blank_campaign_rows][:10]]
    st.error(
        "广告系列名称有空白，请检查 CSV 第 "
        + "、".join(row_numbers)
        + " 行。"
    )
    st.stop()

if invalid_numeric_values.any():
    row_numbers = [
        str(index + 2)
        for index in data.index[invalid_numeric_values][:10]
    ]
    st.error(
        "已选择的数字字段中有非数字内容，请检查 CSV 第 "
        + "、".join(row_numbers)
        + " 行。真正为 0 的数据请填写 0；暂时未知的数据可以留空。"
    )
    st.stop()

missing_numeric_summary = [
    f"{FIELD_INFO[field]['label']} {count} 个空值"
    for field, count in numeric_input_missing.items()
    if count
]
if missing_numeric_summary:
    st.warning(
        "发现数值空值（" + "；".join(missing_numeric_summary) +
        "）。相关汇总将标为“—”，避免把缺失数据当成 0。"
    )

if "duration_days" in data.columns and (data["duration_days"] <= 0).any():
    row_numbers = [
        str(index + 2)
        for index in data.index[data["duration_days"] <= 0][:10]
    ]
    st.error(
        "投放周期必须大于 0 天，请检查 CSV 第 "
        + "、".join(row_numbers)
        + " 行。"
    )
    st.stop()

if "uv" in data.columns and (data["uv"] < 0).any():
    row_numbers = [
        str(index + 2) for index in data.index[data["uv"] < 0][:10]
    ]
    st.error(
        "UV 不能小于 0，请检查 CSV 第 "
        + "、".join(row_numbers)
        + " 行。"
    )
    st.stop()

duration_is_inconsistent = (
    "duration_days" in data.columns
    and (
        data["duration_days"].nunique() > 1
        or data["duration_days"].isna().any()
    )
)
can_calculate_dau = "uv" in data.columns and "duration_days" in data.columns
dau_period_days = None
dau_period_note = ""

if can_calculate_dau and duration_is_inconsistent:
    st.warning(
        "投放周期存在不同数值或空值。为避免周期口径不一致，请选择统一计算方式。"
    )
    with st.form("duration_resolution_form"):
        duration_choice = st.radio(
            "周期处理方式",
            ["统一使用手动输入的周期", "不计算 DAU 和 Cost/DAU"],
            help="手动周期仅用于本次 DAU 计算；CSV 中的原始周期值仍会保留显示。",
        )
        manual_duration_days = st.number_input(
            "统一计算周期（天）",
            min_value=1,
            max_value=3650,
            value=8,
            step=1,
            help="仅在选择“统一使用手动输入的周期”时生效。",
        )
        confirm_duration = st.form_submit_button(
            "确认周期处理方式", type="primary"
        )

    if confirm_duration:
        st.session_state["duration_resolution_fingerprint"] = file_fingerprint
        st.session_state["duration_resolution_choice"] = duration_choice
        st.session_state["duration_override_days"] = manual_duration_days
        st.session_state.pop("ai_diagnosis_text", None)
        st.session_state.pop("ai_diagnosis_fingerprint", None)

    if st.session_state.get("duration_resolution_fingerprint") != file_fingerprint:
        st.info("请选择一种周期处理方式并确认后，系统才会继续分析。")
        st.stop()

    if st.session_state["duration_resolution_choice"] == "统一使用手动输入的周期":
        dau_period_days = st.session_state["duration_override_days"]
        dau_period_note = f"周期不一致；DAU 按你确认的 {dau_period_days:g} 天统一计算。"
    else:
        dau_period_note = "周期不一致；按你的选择，未计算 DAU 和 Cost/DAU。"
elif can_calculate_dau:
    dau_period_days = float(data["duration_days"].iloc[0])
    dau_period_note = f"DAU 按 CSV 中统一的 {dau_period_days:g} 天周期计算。"

mapping_rows = [
    {
        "系统字段": info["label"],
        "对应的 CSV 列": mapping[field] or "未提供",
        "是否必需": "是" if info["required"] else "否",
    }
    for field, info in FIELD_INFO.items()
]
st.success(f"字段确认完成，共 {len(data)} 行数据。")
with st.expander("查看字段对应关系"):
    st.dataframe(pd.DataFrame(mapping_rows), use_container_width=True)

ignored_columns = [
    column for column in headers if column not in used_source_columns
]
if ignored_columns:
    with st.expander(f"查看未参与计算的其他列（{len(ignored_columns)} 列）"):
        st.write("这些列会被保留在原始预览中，但不会参与指标计算。")
        st.write("、".join(str(column) for column in ignored_columns))

with st.expander("查看原始 CSV 数据"):
    st.dataframe(raw_data, use_container_width=True)

analysis_numeric_fields = [
    field
    for field in NUMERIC_FIELDS
    if field in data.columns
]
def aggregate_numeric_by(group_field):
    grouped = data.groupby(
        group_field, as_index=False, sort=False
    )[analysis_numeric_fields].sum(min_count=1)
    for metric in analysis_numeric_fields:
        incomplete_groups = data.groupby(group_field, sort=False)[metric].apply(
            lambda values: values.isna().any()
        )
        grouped.loc[grouped[group_field].map(incomplete_groups), metric] = pd.NA
    return grouped


summary = aggregate_numeric_by("campaign_name")

if "duration_days" in data.columns:
    def format_period_values(values):
        unique_values = sorted(set(value for value in values if pd.notna(value)))
        formatted = [
            str(int(value)) if float(value).is_integer() else f"{value:g}"
            for value in unique_values
        ]
        return " / ".join(formatted)

    duration_summary = data.groupby("campaign_name", sort=False)[
        "duration_days"
    ].apply(format_period_values)
    summary = summary.merge(
        duration_summary.rename("CSV 投放周期（天）"),
        on="campaign_name",
        how="left",
    )

if "uv" in summary.columns:
    if dau_period_days is None:
        summary["dau"] = pd.NA
    else:
        summary["dau"] = summary["uv"] / dau_period_days


def safe_divide(numerator, denominator, multiplier=1):
    result = numerator / denominator.where(denominator != 0)
    return result * multiplier


def funnel_rate(numerator, denominator):
    """Return a percentage for funnel display, or None if unavailable."""
    if numerator is None or denominator is None:
        return None
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return None
    return round(float(numerator) / float(denominator) * 100, 2)


def display_metrics_with_undefined_dashes(display_frame, source_frame):
    """Show a dash for missing inputs or zero denominators, without changing calculations."""
    result = display_frame.copy()
    result = result.astype(object).where(result.notna(), "—")
    denominator_by_metric = {
        "CPM": "impressions",
        "CPC": "clicks",
        "CTR (%)": "impressions",
        "Click-PV rate (%)": "clicks",
        "CPPV": "pv",
        "CPUV": "uv",
        "Paid UV Rate (%)": "uv",
        "ROAS": "cost",
    }
    for metric, denominator in denominator_by_metric.items():
        if metric in result.columns and denominator in source_frame.columns:
            unavailable = (
                source_frame[denominator].isna()
                | source_frame[denominator].eq(0)
            )
            result[metric] = result[metric].astype(object)
            result.loc[unavailable, metric] = "—"
    return result


def add_calculated_metrics(grouped, name_column):
    grouped["CPM"] = safe_divide(
        grouped["cost"], grouped["impressions"], 1000
    )
    grouped["CPC"] = safe_divide(grouped["cost"], grouped["clicks"])
    grouped["CTR (%)"] = safe_divide(
        grouped["clicks"], grouped["impressions"], 100
    )

    columns = [
        name_column, "cost", "impressions", "clicks",
        "CPM", "CPC", "CTR (%)",
    ]

    if "pv" in grouped.columns:
        grouped["Click-PV rate (%)"] = safe_divide(
            grouped["pv"], grouped["clicks"], 100
        )
        grouped["CPPV"] = safe_divide(grouped["cost"], grouped["pv"])
        columns.extend(["Click-PV rate (%)", "CPPV"])

    if "dau" in grouped.columns:
        dau_values = pd.to_numeric(grouped["dau"], errors="coerce")
        grouped["DAU（日均）"] = dau_values.round(2).astype(object).where(
            dau_values.notna(), "—"
        )
        cost_per_dau = grouped["cost"] / dau_values
        valid_dau = dau_values.notna() & dau_values.gt(0)
        grouped["Cost/DAU"] = cost_per_dau.round(2).astype(object).where(
            valid_dau, "—"
        )
        columns.extend(["DAU（日均）", "Cost/DAU"])

    if "uv" in grouped.columns:
        grouped["CPUV"] = safe_divide(grouped["cost"], grouped["uv"])
        columns.append("CPUV")

    if "uv" in grouped.columns and "paid_uv" in grouped.columns:
        grouped["Paid UV Rate (%)"] = safe_divide(
            grouped["paid_uv"], grouped["uv"], 100
        )
        columns.append("Paid UV Rate (%)")

    if "gmv" in grouped.columns:
        grouped["ROAS"] = safe_divide(grouped["gmv"], grouped["cost"])
        columns.append("ROAS")

    return grouped, columns


def render_rounded_bar_chart(container, frame, category_field, metric_field, alt_text):
    chart_data = frame[[category_field, metric_field]].copy()
    chart_data[category_field] = chart_data[category_field].astype("string")
    chart_data[metric_field] = pd.to_numeric(
        chart_data[metric_field], errors="coerce"
    )
    chart_spec = {
        "mark": {
            "type": "bar",
            "color": "#7376D8",
            "cornerRadiusTopLeft": 8,
            "cornerRadiusTopRight": 8,
        },
        "encoding": {
            "x": {
                "field": category_field,
                "type": "nominal",
                "sort": chart_data[category_field].dropna().tolist(),
                "title": None,
                "axis": {
                    "labelAngle": 0,
                    "labelLimit": 180,
                    "labelOverlap": False,
                },
            },
            "y": {
                "field": metric_field,
                "type": "quantitative",
                "title": metric_field,
                "scale": {"zero": True},
            },
            "tooltip": [
                {
                    "field": category_field,
                    "type": "nominal",
                    "title": category_field,
                },
                {
                    "field": metric_field,
                    "type": "quantitative",
                    "title": metric_field,
                    "format": ".2f",
                },
            ],
        },
        "height": 310,
    }
    container.vega_lite_chart(
        chart_data, chart_spec, width="stretch", alt=alt_text
    )


summary, display_columns = add_calculated_metrics(summary, "campaign_name")
if "CSV 投放周期（天）" in summary.columns:
    display_columns.insert(1, "CSV 投放周期（天）")

factor_summaries_for_ai = {}
for field in CATEGORY_FIELDS:
    if field not in data.columns:
        continue
    factor_data = aggregate_numeric_by(field)
    factor_data["CSV记录行数"] = data.groupby(field, sort=False).size().to_numpy()
    if "uv" in factor_data.columns:
        if dau_period_days is None:
            factor_data["dau"] = pd.NA
        else:
            factor_data["dau"] = factor_data["uv"] / dau_period_days
    factor_data, factor_columns = add_calculated_metrics(factor_data, field)
    factor_columns.insert(1, "CSV记录行数")
    factor_data = factor_data.rename(columns={field: CATEGORY_LABELS[field]})
    factor_columns[0] = CATEGORY_LABELS[field]
    factor_data = factor_data.sort_values("cost", ascending=False).head(10)
    factor_ai_columns = factor_columns + [
        metric
        for metric in ["uv", "paid_uv"]
        if metric in factor_data.columns and metric not in factor_columns
    ]
    factor_ai_data = factor_data[factor_ai_columns].round(2)
    factor_ai_data = display_metrics_with_undefined_dashes(
        factor_ai_data, factor_data
    )
    factor_summaries_for_ai[CATEGORY_LABELS[field]] = factor_ai_data.to_dict(
        orient="records"
    )

campaign_ai_columns = display_columns + [
    metric
    for metric in ["uv", "paid_uv"]
    if metric in summary.columns and metric not in display_columns
]
campaign_summaries_for_ai = summary[campaign_ai_columns].round(2)
campaign_summaries_for_ai = display_metrics_with_undefined_dashes(
    campaign_summaries_for_ai, summary
)
campaign_summaries_for_ai.insert(
    1,
    "CSV记录行数",
    data.groupby("campaign_name", sort=False).size().to_numpy(),
)

def complete_total(field):
    if data[field].isna().any():
        return None
    return data[field].sum()


total_impressions = complete_total("impressions")
total_clicks = complete_total("clicks")
overall_ctr = (
    total_clicks / total_impressions * 100
    if total_clicks is not None
    and total_impressions is not None
    and total_impressions != 0
    else None
)
overall_pv = complete_total("pv") if "pv" in data.columns else None
overall_uv = complete_total("uv") if "uv" in data.columns else None
overall_paid_uv = complete_total("paid_uv") if "paid_uv" in data.columns else None


def optional_count(value):
    return int(value) if value is not None and pd.notna(value) else None


overall_funnel = {
    "曝光到点击": {
        "分母曝光次数": optional_count(total_impressions),
        "分子点击次数": optional_count(total_clicks),
        "CTR (%)": funnel_rate(total_clicks, total_impressions),
    },
    "点击到页面浏览": {
        "分母点击次数": optional_count(total_clicks),
        "分子页面浏览次数PV": optional_count(overall_pv),
        "Click-PV rate (%)": funnel_rate(overall_pv, total_clicks),
    },
    "访问用户到付费用户": {
        "分母访问用户数UV": optional_count(overall_uv),
        "分子付费用户数Paid UV": optional_count(overall_paid_uv),
        "Paid UV Rate (%)": funnel_rate(overall_paid_uv, overall_uv),
    },
}

st.subheader("初步诊断建议")
st.caption("以下比较基于本文件内的整体表现，不代表行业标准。")

total_cost = complete_total("cost")
if "gmv" in data.columns:
    total_gmv = complete_total("gmv")
    overall_roas = (
        total_gmv / total_cost
        if total_gmv is not None and total_cost is not None and total_cost != 0
        else None
    )
else:
    overall_roas = None

missing_metrics = []
if "pv" not in data.columns:
    missing_metrics.append("Click-PV rate、CPPV（需要 PV）")
if "uv" not in data.columns:
    missing_metrics.append("CPUV、Paid UV Rate、DAU、Cost/DAU（需要 UV）")
elif "paid_uv" not in data.columns:
    missing_metrics.append("Paid UV Rate（需要 Paid UV）")
if "uv" in data.columns and "duration_days" not in data.columns:
    missing_metrics.append("DAU、Cost/DAU（需要投放周期天数）")
if "gmv" not in data.columns:
    missing_metrics.append("ROAS（需要 GMV）")


def campaign_rule_observations(row):
    observations = []
    if pd.isna(row["clicks"]):
        observations.append((
            "red",
            "点击数存在空值，CTR、CPC 和点击到页面浏览阶段无法完整判断；"
            "请先核对点击数据回传，不能把空值当成 0。",
        ))
    elif pd.isna(row["impressions"]):
        observations.append((
            "red",
            "曝光数存在空值，CTR 和 CPM 无法完整判断；请先核对曝光数据回传。",
        ))
    elif row["clicks"] == 0 and row["impressions"] > 0:
        observations.append((
            "orange",
            f"有 {row['impressions']:,.0f} 次曝光，但记录点击数为 0，"
            "因此该系列 CTR 为 0.00%；建议先核对素材吸引力及点击事件回传。",
        ))

    if (
        "ROAS" in summary.columns
        and pd.notna(row["ROAS"])
        and pd.notna(row["cost"])
        and row["cost"] > 0
        and row["ROAS"] == 0
    ):
        observations.append((
            "red",
            "有花费但当前汇总 GMV 为 0，ROAS 为 0.00；"
            "这不代表达到良好表现。建议优先核对成交回传和归因口径，"
            "确认数据无误后再评估投放效果。",
        ))

    if (
        overall_roas is not None
        and pd.notna(row["cost"])
        and pd.notna(row["ROAS"])
        and row["cost"] > 0
        and row["ROAS"] > 0
        and overall_roas > 0
    ):
        if row["ROAS"] < overall_roas:
            observations.append((
                "orange",
                f"ROAS 为 {row['ROAS']:.2f}，低于文件整体的 {overall_roas:.2f}。"
                "可以检查该系列的素材、受众和落地页，并结合更多日期的数据判断。",
            ))
        else:
            observations.append((
                "green",
                f"ROAS 为 {row['ROAS']:.2f}，达到或高于文件整体的 "
                f"{overall_roas:.2f}。可以继续观察该系列的表现。",
            ))

    if (
        overall_ctr is not None
        and pd.notna(row["CTR (%)"])
        and row["impressions"] > 0
        and row["CTR (%)"] < overall_ctr
    ):
        observations.append((
            "yellow",
            f"CTR 为 {row['CTR (%)']:.2f}%，低于文件整体的 {overall_ctr:.2f}%。"
            "可以检查素材是否能吸引点击。",
        ))
    elif (
        overall_ctr is None
        and pd.notna(row["CTR (%)"])
        and row["impressions"] > 0
    ):
        observations.append((
            "yellow",
            f"该系列 CTR 为 {row['CTR (%)']:.2f}%，但文件整体 CTR 因数据缺失"
            "或曝光总数为 0 而无法计算，暂不进行整体高低比较。",
        ))
    return observations


severity_labels = {
    "yellow": "留意",
    "orange": "需要关注",
    "red": "优先核查",
    "green": "表现较好",
}
severity_order = {"green": 0, "yellow": 1, "orange": 2, "red": 3}
campaign_diagnostics = []
for _, campaign_row in summary.iterrows():
    campaign_observations = campaign_rule_observations(campaign_row)
    campaign_severity = (
        max(
            (severity for severity, _ in campaign_observations),
            key=severity_order.get,
        )
        if campaign_observations
        else "green"
    )
    campaign_diagnostics.append(
        (campaign_row, campaign_observations, campaign_severity)
    )

severity_counts = Counter(
    severity
    for _, observations, _ in campaign_diagnostics
    for severity, _ in observations
    if severity in {"yellow", "orange", "red"}
)
top_finding = next(
    (
        (campaign_row["campaign_name"], severity, message)
        for target_severity in ("red", "orange", "yellow")
        for campaign_row, observations, _ in campaign_diagnostics
        for severity, message in observations
        if severity == target_severity
    ),
    None,
)

st.markdown('<div class="section-kicker">分析结果 · 先看整体，再看细节</div>', unsafe_allow_html=True)
st.caption("先了解整体投放表现，再沿着转化链路定位值得关注的环节。")
if dau_period_note:
    st.info(dau_period_note)

kpi_columns = st.columns(4)
kpi_columns[0].metric("广告系列数", f"{len(summary):,}")
kpi_columns[1].metric(
    "总花费", f"{total_cost:,.2f}" if total_cost is not None else "—",
    help="花费数据存在空值，暂时无法完整汇总。" if total_cost is None else None,
)
kpi_columns[2].metric(
    "整体 CTR",
    f"{overall_ctr:.2f}%" if overall_ctr is not None else "—",
    help=(
        "曝光或点击字段存在空值，暂时无法完整计算 CTR。"
        if total_clicks is None or total_impressions is None
        else "曝光次数为 0，无法计算 CTR。"
    ) if overall_ctr is None else None,
)
if overall_roas is not None:
    kpi_columns[3].metric("整体 ROAS", f"{overall_roas:.2f}")
elif "gmv" not in data.columns:
    kpi_columns[3].metric("整体 ROAS", "—", help="CSV 需要提供 GMV 列")
else:
    roas_help = (
        "GMV 或花费数据存在空值，暂时无法计算完整 ROAS。"
        if total_gmv is None or total_cost is None
        else "总花费为 0，无法计算 ROAS。"
    )
    kpi_columns[3].metric("整体 ROAS", "—", help=roas_help)

with st.container(border=True):
    st.subheader("本次诊断重点")
    st.caption("按规则触发的线索数量汇总；同一广告系列可能有多条线索。")
    attention_columns = st.columns(3)
    attention_levels = [
        ("yellow", "留意"),
        ("orange", "需要关注"),
        ("red", "优先核查"),
    ]
    for column, (severity, label) in zip(attention_columns, attention_levels):
        column.markdown(
            f'<div class="overview-attention severity-{severity}">'
            f"<span>{label}</span><strong>{severity_counts.get(severity, 0)}</strong>"
            "<small>条线索</small></div>",
            unsafe_allow_html=True,
        )

    if top_finding:
        campaign_name, severity, message = top_finding
        st.markdown(
            '<div class="top-attention">'
            f"<strong>先查看 · {severity_labels[severity]} · "
            f"{html_escape(str(campaign_name))}</strong><br>"
            f"{html_escape(message)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("当前规则没有触发黄色及以上关注项；请结合数据覆盖情况综合判断。")

overview_tab, diagnosis_tab, factor_tab, detail_tab = st.tabs(
    ["效果总览", "诊断建议", "影响因素", "数据明细"]
)

with overview_tab:
    st.subheader("分阶段转化过程")
    st.caption("按先后顺序查看每一段的转化表现和计算分母。")
    funnel_steps = [
        (
            "曝光 → 点击",
            overall_funnel["曝光到点击"]["CTR (%)"],
            "点击次数",
            overall_funnel["曝光到点击"]["分子点击次数"],
            "曝光次数",
            overall_funnel["曝光到点击"]["分母曝光次数"],
            True,
        ),
        (
            "点击 → 页面浏览",
            overall_funnel["点击到页面浏览"]["Click-PV rate (%)"],
            "页面浏览次数 PV",
            overall_funnel["点击到页面浏览"]["分子页面浏览次数PV"],
            "点击次数",
            overall_funnel["点击到页面浏览"]["分母点击次数"],
            "pv" in data.columns,
        ),
        (
            "访问用户 UV → 付费用户",
            overall_funnel["访问用户到付费用户"]["Paid UV Rate (%)"],
            "付费用户数 Paid UV",
            overall_funnel["访问用户到付费用户"]["分子付费用户数Paid UV"],
            "访问用户数 UV",
            overall_funnel["访问用户到付费用户"]["分母访问用户数UV"],
            "uv" in data.columns and "paid_uv" in data.columns,
        ),
    ]

    with st.container(border=True):
        funnel_markup = ['<div class="funnel-flow" role="group" aria-label="分阶段转化链路">']
        for index, step in enumerate(funnel_steps):
            label, rate, numerator_label, numerator, denominator_label, denominator, available = step
            if not available:
                count_caption = "缺少所需字段，无法计算"
            elif rate is None:
                numerator_text = f"{numerator:,}" if numerator is not None else "—"
                denominator_text = f"{denominator:,}" if denominator is not None else "—"
                if numerator is None or denominator is None:
                    reason = "数据有空值，无法完整计算"
                else:
                    reason = "分母为 0"
                count_caption = (
                    f"{numerator_label} {numerator_text} / "
                    f"{denominator_label} {denominator_text}；{reason}"
                )
            else:
                count_caption = (
                    f"{numerator_label} {numerator:,} / "
                    f"{denominator_label} {denominator:,}"
                )

            rate_text = f"{rate:.2f}%" if available and rate is not None else "—"
            funnel_markup.append(
                '<article class="funnel-stage">'
                f'<div class="funnel-stage-name">{index + 1:02d} · {html_escape(label)}</div>'
                f'<div class="funnel-stage-value">{rate_text}</div>'
                f'<div class="funnel-stage-count">{html_escape(count_caption)}</div>'
                '</article>'
            )
            if index < len(funnel_steps) - 1:
                funnel_markup.append('<div class="funnel-arrow" aria-hidden="true">→</div>')

        funnel_markup.append('</div>')
        st.markdown("".join(funnel_markup), unsafe_allow_html=True)
        st.caption(
            "这是分阶段观察，不是严格连续的用户漏斗。PV 是浏览次数，UV 和 Paid UV 是去重人数；"
            "各阶段口径不同，Click-PV rate 也可能超过 100%。"
        )

    st.subheader("广告系列 ROAS 对比")
    st.caption("横向查看本文件中各广告系列的成交金额与花费效率。")
    with st.container(border=True):
        if "ROAS" in summary.columns:
            chart_columns = st.columns([2.2, 1])
            render_rounded_bar_chart(
                chart_columns[0], summary, "campaign_name", "ROAS",
                "各广告系列 ROAS 对比",
            )
            chart_columns[1].markdown(
                '<div class="overview-chart-note">'
                '<strong>读图提示</strong>'
                '柱形越高，表示该系列在当前归因口径下的 ROAS 越高。'
                '这只反映本文件中的相对表现，不能单独证明差异由某项因素造成。'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption("ROAS = 成交金额 GMV ÷ 花费。")
        else:
            st.info("CSV 未提供成交金额 GMV，暂时无法绘制 ROAS 对比图。")


def split_diagnosis_sections(text):
    section_names = ["数据观察", "可能原因（待验证）", "下一步建议"]
    sections = {name: [] for name in section_names}
    current_section = None
    for raw_line in text.splitlines():
        line = re.sub(r"^#+\s*", "", raw_line.strip()).replace("**", "")
        normalized = re.sub(r"\s+", "", line)
        if normalized.startswith(("一、数据观察", "一.数据观察", "数据观察")):
            current_section = "数据观察"
        elif normalized.startswith(("二、可能原因", "二.可能原因", "可能原因")):
            current_section = "可能原因（待验证）"
        elif normalized.startswith(("三、下一步建议", "三.下一步建议", "下一步建议")):
            current_section = "下一步建议"
        elif current_section and line:
            sections[current_section].append(line)
    return sections


def render_ai_diagnosis(text):
    sections = split_diagnosis_sections(text)
    if not all(sections.values()):
        with st.container(border=True):
            st.markdown(text)
        return

    section_styles = {
        "数据观察": "diagnosis-observation",
        "可能原因（待验证）": "diagnosis-hypothesis",
        "下一步建议": "diagnosis-action",
    }
    for section_name, lines in sections.items():
        with st.container(border=True):
            st.markdown(
                f'<div class="diagnosis-label {section_styles[section_name]}">'
                f"{section_name}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("\n".join(lines))


with diagnosis_tab:
    st.subheader("规则诊断")
    st.caption(
        "关注等级：黄色表示留意，橙色表示需要关注，红色表示优先核查。"
        "等级依据数据完整性和当前文件内的相对表现，不代表行业标准。"
    )
    if overall_roas is None:
        if "gmv" not in data.columns:
            st.info("未提供成交金额 GMV，因此跳过 ROAS 诊断。")
        elif total_gmv is None or total_cost is None:
            st.info("GMV 或花费存在空值，因此无法完整计算整体 ROAS。")
        else:
            st.info("总花费为 0，因此无法计算整体 ROAS。")

    for row, observations, highest_severity in campaign_diagnostics:
        with st.container(border=True):
            if observations:
                count_label = (
                    f"{len(observations)} 条线索 · "
                    f"{severity_labels[highest_severity]}"
                )
            else:
                count_label = "暂无提示"

            heading_col, count_col = st.columns([5, 1])
            heading_col.markdown(f"**{row['campaign_name']}**")
            count_col.markdown(
                f'<div class="severity-summary severity-{highest_severity}">'
                f"{count_label}</div>",
                unsafe_allow_html=True,
            )
            if observations:
                for severity, observation in observations:
                    st.markdown(
                        f'<div class="severity-item severity-{severity}">'
                        f'<span class="severity-tag">{severity_labels[severity]}</span>'
                        f"<span>{html_escape(observation)}</span></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption(
                    "当前没有可比较的有效指标；请结合上方数据完整性提示，"
                    "补齐数据后再做判断。"
                )

    if missing_metrics:
        st.info("因 CSV 未提供相关字段，以下指标未计算：" + "；".join(missing_metrics))

    st.markdown('<div class="section-kicker">AI 诊断建议</div>', unsafe_allow_html=True)
    st.caption(
        "公开体验使用者需要填写自己的 OpenAI API Key，费用由该密钥对应账户承担。"
        "提交后密钥仅用于本次请求，不写入文件或数据库，输入框会清空；"
        "密钥会经 HTTPS 传到本应用服务器，请只在信任本页面时填写。"
        "点击生成后，系统会把广告系列和已确认影响因素的汇总指标（包括 UV 和 Paid UV 汇总人数）发送给 OpenAI，"
        "不发送逐行原始记录；每种因素最多发送花费最高的 10 组。"
    )
    with st.form("ai_diagnosis_form", clear_on_submit=True):
        user_api_key = st.text_input(
            "你的 OpenAI API Key",
            type="password",
            placeholder="粘贴你自己的 API Key",
            help="建议使用权限受限、设置了支出限制的项目密钥。",
        )
        generate_ai = st.form_submit_button(
            "生成 AI 诊断建议", type="primary"
        )

    if generate_ai:
        st.session_state.pop("ai_diagnosis_text", None)
        st.session_state.pop("ai_diagnosis_fingerprint", None)
        if not user_api_key.strip():
            st.warning("请先填写你自己的 OpenAI API Key。")
        else:
            try:
                from openai import OpenAI
    
                client = OpenAI(api_key=user_api_key.strip())
                data_for_ai = {
                    "DAU计算口径": dau_period_note or "未计算 DAU",
                    "整体分阶段指标": overall_funnel,
                    "广告系列汇总": campaign_summaries_for_ai.to_dict(
                        orient="records"
                    ),
                    "影响因素分组汇总": factor_summaries_for_ai,
                }
    
                with st.spinner("AI 正在分析，请稍等..."):
                    response = client.responses.create(
                        model="gpt-6-luna",
                        instructions=(
                            "你是一位谨慎的广告数据分析助手。"
                            "只能依据输入的广告系列和影响因素汇总数据分析，不得补造数字。"
                            "请按输入的三个分阶段指标分析广告转化链路：曝光到点击看 CTR，"
                            "点击到页面浏览看 Click-PV rate，访问用户到付费用户看 Paid UV Rate。"
                            "只在同一阶段、同一指标口径内比较不同广告系列或影响因素分组，"
                            "不得直接比较不同阶段的百分比高低，也不要把 PV 次数当成去重用户数。"
                            "Click-PV rate 是 PV 次数除以点击次数，可能超过 100%；"
                            "UV 和 Paid UV 是去重人数，缺少字段或分母为 0 时应说明无法计算。"
                            "讨论 Paid UV Rate 时，优先同时列出 Paid UV 人数和 UV 人数作为分子、分母；"
                            "只能引用输入中对应广告系列或影响因素分组的汇总人数，不得自行推算或混用分组。"
                            "数值字段有空值时，相关指标应说明数据不完整、无法计算；不得把空值当作 0。"
                            "当有花费且 ROAS 为 0 时，应说明当前汇总 GMV 为 0，建议先核对成交回传和归因；"
                            "不得仅因 ROAS 等于整体 0 就评价为表现良好或建议继续投放。"
                            "不同广告系列或分组之间可能存在用户重复归因，不得将跨组人数相加后称为去重用户总数。"
                            "请严格使用以下三个标题和结构："
                            "一、数据观察：列出 2 到 4 条可核对的事实；"
                            "每条写明系列或因素分组、指标数值、对比对象及对比数值。"
                            "二、可能原因（待验证）：最多列 2 条假设；"
                            "明确标为假设，不得把相关性描述成因果。"
                            "三、下一步建议：最多列 3 条可执行动作；"
                            "每条都写明下一周期要复核的指标。"
                            "可以参考 CSV 记录行数判断数据覆盖情况，但不要把记录行数称为用户样本量。"
                            "记录行数较少或分组条件不一致时，只能给探索性判断，不能建议据此直接扩量。"
                            "不编造行业基准；没有某指标时明确说无法判断。"
                            "避免重复同一结论，使用简明中文，确保最后一句完整。"
                            "不要使用 Markdown 加粗符号，直接输出普通文字。"
                        ),
                        input=(
                            "请分析以下广告系列汇总数据，指出表现较好的地方、"
                            "值得关注的问题和下一步建议。"
                            "数据如下：\n\n"
                            f"{json.dumps(data_for_ai, ensure_ascii=False)}"
                        ),
                        max_output_tokens=2400,
                    )
    
                if response.status != "completed":
                    st.warning(
                        "AI 回复没有完整生成，这次内容没有保存。请稍后重新点击生成。"
                    )
                else:
                    diagnosis_text = (response.output_text or "").strip()
                    diagnosis_text = re.sub(r"\\?\*\*", "", diagnosis_text)
                    required_sections = [
                        "一、数据观察",
                        "二、可能原因",
                        "三、下一步建议",
                    ]
                    missing_sections = [
                        section for section in required_sections if section not in diagnosis_text
                    ]
                    if not diagnosis_text or missing_sections:
                        st.warning(
                            "AI 回复缺少完整的诊断部分，这次内容没有保存。"
                            "请稍后重新点击生成。"
                        )
                    else:
                        st.session_state["ai_diagnosis_text"] = diagnosis_text
                        st.session_state["ai_diagnosis_fingerprint"] = file_fingerprint
    
            except Exception:
                st.error(
                    "AI 调用失败。请检查密钥是否有效、账户是否有可用 API 额度，"
                    "或稍后重试。为保护密钥，页面不会显示原始 API 错误详情。"
                )

    if (
        st.session_state.get("ai_diagnosis_fingerprint") == file_fingerprint
        and st.session_state.get("ai_diagnosis_text")
    ):
        display_diagnosis = re.sub(
            r"\\?\*\*", "", st.session_state["ai_diagnosis_text"]
        )
        render_ai_diagnosis(display_diagnosis)

def build_factor_export(field):
    grouped_factor = data.groupby(
        field, as_index=False, sort=False
    )[analysis_numeric_fields].sum()
    if "uv" in grouped_factor.columns:
        if dau_period_days is None:
            grouped_factor["dau"] = pd.NA
        else:
            grouped_factor["dau"] = grouped_factor["uv"] / dau_period_days

    grouped_factor["数据行数"] = data.groupby(field, sort=False).size().to_numpy()
    grouped_factor, factor_columns = add_calculated_metrics(
        grouped_factor, field
    )
    factor_columns.insert(1, "数据行数")
    grouped_factor = grouped_factor.rename(
        columns={field: CATEGORY_LABELS[field]}
    )
    factor_columns[0] = CATEGORY_LABELS[field]
    factor_display = grouped_factor[factor_columns].round(2)
    return display_metrics_with_undefined_dashes(
        factor_display, grouped_factor
    )


with factor_tab:
    st.subheader("影响因素对比")
    st.caption(
        "选择 CSV 中的一个分类列，查看不同人群、落地页、素材类型等的汇总表现。"
    )
    available_factors = [
        field for field in CATEGORY_FIELDS if field in data.columns
    ]
    factor_exports = {
        field: build_factor_export(field) for field in available_factors
    }

    if not available_factors:
        st.info(
            "当前 CSV 没有已确认的影响因素列。上传包含投放人群、落地页版本、"
            "素材类型、投放位置或投放目标的 CSV，并在字段确认处选择对应列。"
        )
    else:
        selected_factor = st.selectbox(
            "选择要比较的因素",
            available_factors,
            format_func=lambda field: CATEGORY_LABELS[field],
        )
        factor_summary = factor_exports[selected_factor]
        factor_display_columns = list(factor_summary.columns)

        st.caption(
            "每一行汇总同一类因素对应的数据。数据行数较少时，结果只适合初步观察。"
        )
        st.dataframe(
            factor_summary[factor_display_columns].round(2),
            use_container_width=True,
            hide_index=True,
        )

        available_factor_metrics = [
            metric for metric in factor_display_columns
            if metric in {
                "CTR (%)", "Click-PV rate (%)", "Paid UV Rate (%)",
                "ROAS", "CPM", "CPC", "CPUV",
            }
        ]
        if available_factor_metrics:
            selected_metric = st.selectbox(
                "图表展示指标",
                available_factor_metrics,
                index=(
                    available_factor_metrics.index("ROAS")
                    if "ROAS" in available_factor_metrics
                    else 0
                ),
            )
            factor_label = CATEGORY_LABELS[selected_factor]
            render_rounded_bar_chart(
                st,
                factor_summary,
                factor_label,
                selected_metric,
                f"按{factor_label}对比{selected_metric}",
            )

        st.info(
            "这些对比展示的是数据中的共同变化，不能单独证明某个因素造成了效果差异。"
            "建议后续用控制其他条件的对照测试验证。"
        )

with detail_tab:
    st.subheader("数据明细")
    st.caption("可横向比较各广告系列的成本、流量和转化指标。")
    campaign_display = display_metrics_with_undefined_dashes(
        summary[display_columns].round(2), summary
    )
    st.dataframe(
        campaign_display,
        use_container_width=True,
        hide_index=True,
    )

    export_buffer = io.BytesIO()
    with pd.ExcelWriter(export_buffer, engine="openpyxl") as writer:
        campaign_display.to_excel(
            writer, sheet_name="广告系列汇总", index=False
        )
        if factor_exports:
            for field, factor_data in factor_exports.items():
                factor_data.to_excel(
                    writer,
                    sheet_name=CATEGORY_LABELS[field][:31],
                    index=False,
                )
        else:
            pd.DataFrame(
                {"说明": ["本次上传的数据没有已确认的影响因素列。"]}
            ).to_excel(writer, sheet_name="影响因素说明", index=False)

        if (
            st.session_state.get("ai_diagnosis_fingerprint") == file_fingerprint
            and st.session_state.get("ai_diagnosis_text")
        ):
            export_diagnosis = re.sub(
                r"\\?\*\*", "", st.session_state["ai_diagnosis_text"]
            )
            ai_lines = export_diagnosis.splitlines()
        else:
            ai_lines = ["尚未生成 AI 诊断建议。请先在“诊断建议”页点击生成。"]
        pd.DataFrame({"AI诊断建议": ai_lines}).to_excel(
            writer, sheet_name="AI诊断建议", index=False
        )
        from openpyxl.styles import Alignment

        ai_worksheet = writer.sheets["AI诊断建议"]
        ai_worksheet.column_dimensions["A"].width = 100
        for cell in ai_worksheet["A"]:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    st.download_button(
        "下载 Excel 分析结果",
        data=export_buffer.getvalue(),
        file_name="广告投放分析结果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="文件包含广告系列汇总、每个已确认影响因素的对比表，以及 AI 诊断建议。",
    )

    if missing_metrics:
        st.info("因 CSV 未提供相关字段，以下指标未计算：" + "；".join(missing_metrics))

    with st.expander("查看原始 CSV 数据"):
        st.dataframe(raw_data, use_container_width=True, hide_index=True)

