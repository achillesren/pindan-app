# -*- coding: utf-8 -*-
import os, sys, pathlib
def _clean():
    p = pathlib.Path(__file__)
    t = p.read_text(encoding='utf-8')
    if '\xa0' in t: p.write_text(t.replace('\xa0', ' '), encoding='utf-8'); os.execv(sys.executable, [sys.executable] + sys.argv)
_clean()

import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="海外自助拼单系统", page_icon="🐷", layout="wide")

def get_ss_id(url):
    import re
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else ""

def load_data():
    try:
        url = st.secrets["secrets"]["public_gsheets_url"]
        ss_id = get_ss_id(url)
        csv_url = f"https://google.com{ss_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(csv_url)
        df.columns = [c.lower().strip() for c in df.columns]
        for col in ["name", "item", "amount", "unit", "cost"]:
            if col not in df.columns: df[col] = None
        return df[["name", "item", "amount", "unit", "cost"]].dropna(subset=["name"])
    except:
        return pd.DataFrame(columns=["name", "item", "amount", "unit", "cost"])

if "df_cached" not in st.session_state:
    st.session_state.df_cached = load_data()

MEAT_MENU = {
    "五花肉": {"price": 8.00, "unit": "公斤", "box": 5.0},
    "大排骨": {"price": 7.00, "unit": "公斤", "box": 20.0},
    "大肠": {"price": 9.50, "unit": "公斤", "box": 20.0},
    "猪颈骨": {"price": 4.50, "unit": "公斤", "box": 20.0},
    "猪腰": {"price": 3.50, "unit": "公斤", "box": 11.0},
    "护心肉": {"price": 4.50, "unit": "公斤", "box": 11.0},
    "小排骨": {"price": 3.50, "unit": "公斤", "box": 12.0},
    "背脊骨": {"price": 3.50, "unit": "公斤", "box": 30.0},
    "猪扒边": {"price": 4.50, "unit": "公斤", "box": 30.0},
    "猪手": {"price": 4.50, "unit": "公斤", "box": 8.0},
    "猪耳朵": {"price": 8.00, "unit": "公斤", "box": 6.0},
    "猪筒骨": {"price": 3.50, "unit": "公斤", "box": 20.0},
    "猪板油": {"price": 4.50, "unit": "公斤", "box": 20.0},
    "猪舌头": {"price": 7.00, "unit": "公斤", "box": 10.0},
    "梅头肉": {"price": 8.00, "unit": "公斤", "box": 5.0},
    "猪头": {"price": 18.00, "unit": "个", "box": 1.0},
    "猪肘": {"price": 4.50, "unit": "公斤", "box": 20.0},
    "肉皮": {"price": 3.50, "unit": "公斤", "box": 20.0},
    "猪里脊": {"price": 7.50, "unit": "公斤", "box": 30.0},
    "猪肝": {"price": 4.00, "unit": "公斤", "box": 13.0}
}

title_from_secrets = st.secrets["secrets"]["title_text"] if "secrets" in st.secrets else "海外群自助拼单自提系统"
st.title(f"🐷 {title_from_secrets}")
st.markdown("群友请直接在下方**输入昵称、选择菜品**提交订购。所有数据将永久安全保存！")

with st.sidebar:
    st.header("⚙️ 团长对账面板")
    admin_key = st.text_input("🗝️ 输入清空钥匙：", type="password", placeholder="请输入清空授权码")
    if st.button("🗑️ 确认清空看板并开启下次拼单", type="secondary"):
        if admin_key == "1234":
            st.session_state.df_cached = pd.DataFrame(columns=["name", "item", "amount", "unit", "cost"])
            st.success("🎉 看板数据已成功归零！")
        else: st.error("钥匙输入错误，无法清空！")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🛒 群友点菜登记")
    with st.form("order_form", clear_on_submit=True):
        user_name = st.text_input("👤 您的微信昵称（必填）：", placeholder="请输入您的名字，方便对账")
        selected_meat = st.selectbox("🥩 选择您要买的肉类：", list(MEAT_MENU.keys()))
        current_unit = MEAT_MENU[selected_meat]["unit"]
        current_price = MEAT_MENU[selected_meat]["price"]
        st.caption(f"当前单价: **{current_price:.2f}** / {current_unit}")
        order_amount = st.number_input(f"🔢 订购数量（单位：{current_unit}）：", min_value=0.1, value=1.0, step=0.5)
        submit_btn = st.form_submit_button("🚀 提交我的拼单", type="primary")
        
        if submit_btn:
            if not user_name.strip(): st.error("请输入您的微信昵称后再提交！")
            else:
                cost = order_amount * current_price
                payload = {"name": user_name.strip(), "item": selected_meat, "amount": order_amount, "unit": current_unit, "cost": cost}
                new_row = pd.DataFrame([payload])
                st.session_state.df_cached = pd.concat([st.session_state.df_cached, new_row], ignore_index=True)
                
                # 显式捕获云端接口的真实反馈
                try:
                    api_url = st.secrets["secrets"]["script_api_url"]
                    res = requests.post(api_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
                    st.info(f"📡 传输状态反馈 ➔ 状态码: {res.status_code} | 返回信息: {res.text[:100]}")
                except Exception as e:
                    st.error(f"❌ 传输失败，网络原因: {str(e)}")
                
                st.success(f"🎉 登记成功！{user_name.strip()} 的订单已更新！")
                st.rerun()

df_display = st.session_state.df_cached
with col2:
    st.subheader("📊 实时拼单看板（整箱进度）")
    if df_display.empty or len(df_display) == 0: st.info("当前还没有人下单哦！")
    else:
        tab_box, tab_bill = st.tabs(["📦 货物成箱缺口", "💰 每人应付账单"])
        with tab_box:
            df_display["amount"] = pd.to_numeric(df_display["amount"], errors='coerce').fillna(0)
            summary = df_display.groupby("item")["amount"].sum().to_dict()
            for meat, total in summary.items():
                if meat in MEAT_MENU and total > 0:
                    box_w = MEAT_MENU[meat]["box"]; unit = MEAT_MENU[meat]["unit"]
                    current_boxes = total / box_w; needed_next = box_w - (total % box_w)
                    st.markdown(f"**【{meat}】** 已被预订：**{total:.1f}** {unit}")
                    if total % box_w == 0: st.success(f" └─ 🎉 刚好凑满 {int(current_boxes)} 箱！")
                    else: st.info(f" └─ 📊 当前进度: {current_boxes:.2f} 箱（还差 **{needed_next:.1f}** {unit} 凑满整箱）")
                    details = df_display[df_display["item"] == meat]
                    detail_strs = [f"{row['name']}({row['amount']}{unit})" for _, row in details.iterrows()]
                    st.caption(f" 👥 已订群友：{', '.join(detail_strs)}"); st.write("---")
        with tab_bill:
            df_display["cost"] = pd.to_numeric(df_display["cost"], errors='coerce').fillna(0)
            user_summary = df_display.groupby("name")["cost"].sum().to_dict()
            wechat_text = "📊 【自助拼单实时对账单】\n"
            for user, total_cost in user_summary.items():
                st.warning(f"👤 **{user}** —— 累计应付: **{total_cost:.2f}**")
                wechat_text += f"\n@{user} 应付：{total_cost:.2f}\n"
                user_details = df_display[df_display["name"] == user]
                for _, row in user_details.iterrows():
                    st.write(f" └─ {row['item']} : {row['amount']} {row['unit']}")
                    wechat_text += f" └─ {row['item']} {row['amount']}{row['unit']}\n"
            st.write("---"); st.subheader("💬 复制群发对账文本")
            st.text_area("点击框内复制发回微信群：", value=wechat_text, height=150)
