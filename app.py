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

# 强制每次刷新都实时去 Google 表格拉取最新完整数据，完全取消缓存
def load_data_live():
    try:
        url = st.secrets["secrets"]["public_gsheets_url"]
        ss_id = get_ss_id(url)
        csv_url = f"https://google.com{ss_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(csv_url)
        
        # 强制格式化列名
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # 【超级列名自动纠错对齐网】针对当前表格列移位进行完美自适应修复
        # 如果C列(amount)为空，而D列和E列有值，说明发生了列移位，我们把数据强行复位
        if len(df) > 0:
            for idx, row in df.iterrows():
                # 检查原本的第3列(amount)是否未捕获到数字，若是，则自动从后面的列中抽取数量和金额
                if pd.isna(df.loc[idx, "amount"]) or str(df.loc[idx, "amount"]).strip() == "":
                    # 尝试从第4列提取数量
                    if "unit" in df.columns and not pd.isna(df.loc[idx, "unit"]):
                        try:
                            df.loc[idx, "amount"] = float(df.loc[idx, "unit"])
                            df.loc[idx, "unit"] = "公斤"
                        except: pass
                    # 尝试从第5列提取总价
                    if "cost" in df.columns and not pd.isna(df.loc[idx, "cost"]):
                        try:
                            df.loc[idx, "cost"] = float(df.loc[idx, "cost"])
                        except: pass
        
        # 补齐缺少的列名模板
        for col in ["name", "item", "amount", "unit", "cost"]:
            if col not in df.columns: df[col] = 0
            
        # 名字去空格净化器
        df["name"] = df["name"].astype(str).str.strip()
        df["item"] = df["item"].astype(str).str.strip()
        
        return df[["name", "item", "amount", "unit", "cost"]].dropna(subset=["name"])
    except Exception as e:
        return pd.DataFrame(columns=["name", "item", "amount", "unit", "cost"])

df_display = load_data_live()

# 初始化每位用户本地独立的购物车缓存
if "cart" not in st.session_state:
    st.session_state.cart = []

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
st.markdown("群友请直接在下方**添加心仪商品进购物车**，最后填写昵称一键提交下单。所有数据永久多端同步！")

with st.sidebar:
    st.header("⚙️ 团长对账面板")
    st.info("提示：开启新一轮拼单时，您直接在您的谷歌表格里删除第2行以下的所有数据清空即可，网页会自动同步全部清零复位！")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛒 群友点菜登记（支持多选）")
    
    with st.container(border=True):
        st.caption("第一步：挑选肉类和数量")
        selected_meat = st.selectbox("🥩 选择您要买的肉类：", list(MEAT_MENU.keys()))
        current_unit = MEAT_MENU[selected_meat]["unit"]
        current_price = MEAT_MENU[selected_meat]["price"]
        st.write(f"当前单价: **{current_price:.2f}** / {current_unit}")
        order_amount = st.number_input(f"🔢 欲购数量（单位：{current_unit}）：", min_value=0.1, value=1.0, step=0.5)
        
        if st.button("➕ 放入我的购物车", type="secondary", use_container_width=True):
            cost = order_amount * current_price
            st.session_state.cart.append({
                "item": selected_meat,
                "amount": order_amount,
                "unit": current_unit,
                "cost": cost
            })
            st.toast(f"已将 {selected_meat} {order_amount}{current_unit} 放入购物车！")
            st.rerun()

    if len(st.session_state.cart) > 0:
        with st.form("cart_form", clear_on_submit=True):
            st.caption("第二步：核对购物车并提交")
            st.write("📋 **您当前挑选的菜品清单：**")
            total_cart_cost = 0.0
            for idx, item in enumerate(st.session_state.cart):
                st.write(f" ├─ {item['item']} : {item['amount']} {item['unit']} (小计: {item['cost']:.2f})")
                total_cart_cost += item["cost"]
            st.markdown(f"💰 购物车总额: **{total_cart_cost:.2f}**")
            
            user_name = st.text_input("👤 您的微信昵称（必填）：", placeholder="请输入您的名字，方便对账")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit_btn = st.form_submit_button("🚀 确认提交拼单", type="primary", use_container_width=True)
            with col_btn2:
                clear_cart = st.form_submit_button("❌ 清空购物车", type="secondary", use_container_width=True)
            
            if clear_cart:
                st.session_state.cart = []
                st.rerun()
                
            if submit_btn:
                if not user_name.strip():
                    st.error("请输入您的微信昵称后再提交！")
                else:
                    try:
                        api_url = st.secrets["secrets"]["script_api_url"]
                        for item in st.session_state.cart:
                            # 严格匹配当前 Google 脚本送出的物理列序列，确保数据对齐
                            payload = {
                                "name": user_name.strip(),
                                "item": item["item"],
                                "amount": item["amount"],
                                "unit": item["unit"],
                                "cost": item["cost"]
                            }
                            requests.post(api_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
                        st.success(f"🎉 恭喜！{user_name.strip()} 的这 {len(st.session_state.cart)} 样菜品已完美合并提交成功！")
                        st.session_state.cart = [] 
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 云端保存失败，网络原因: {str(e)}")
    else:
        st.info("💡 您的购物车还是空的哦，请在上方选择肉类和数量并点击『放入我的购物车』！")

with col2:
    st.subheader("📊 实时拼单看板（整箱进度）")
    # 彻底清除未解析到名字的脏行
    df_clean_display = df_display[df_display["name"].str.lower() != "nan"]
    
    if df_clean_display.empty or len(df_clean_display) == 0:
        st.info("当前还没有人下单哦，赶紧把链接发到群里让大家选菜吧！")
    else:
        tab_box, tab_bill = st.tabs(["📦 货物成箱缺口", "💰 每人应付账单"])
        with tab_box:
            df_clean_display["amount"] = pd.to_numeric(df_clean_display["amount"], errors='coerce').fillna(0)
            summary = df_clean_display.groupby("item")["amount"].sum().to_dict()
            for meat, total in summary.items():
                if meat in MEAT_MENU and total > 0:
                    box_w = MEAT_MENU[meat]["box"]; unit = MEAT_MENU[meat]["unit"]
                    current_boxes = total / box_w; needed_next = box_w - (total % box_w)
                    st.markdown(f"**【{meat}】** 已被预订：**{total:.1f}** {unit}")
                    if total % box_w == 0: st.success(f" └─ 🎉 刚好凑满 {int(current_boxes)} 箱！")
                    else: st.info(f" └─ 📊 当前进度: {current_boxes:.2f} 箱（还差 **{needed_next:.1f}** {unit} 凑满整箱）")
                    details = df_clean_display[df_clean_display["item"] == meat]
                    detail_strs = [f"{row['name']}({row['amount']}{unit})" for _, row in details.iterrows()]
                    st.caption(f" 👥 已订群友：{', '.join(detail_strs)}"); st.write("---")
        with tab_bill:
            df_clean_display["cost"] = pd.to_numeric(df_clean_display["cost"], errors='coerce').fillna(0)
            user_summary = df_clean_display.groupby("name")["cost"].sum().to_dict()
            wechat_text = "📊 【自助拼单实时对账单】\n"
            for user, total_cost in user_summary.items():
                st.warning(f"👤 **{user}** —— 累计应付: **{total_cost:.2f}**")
                wechat_text += f"\n@{user} 应付：{total_cost:.2f}\n"
                user_details = df_clean_display[df_clean_display["name"] == user]
                for _, row in user_details.iterrows():
                    st.write(f" └─ {row['item']} : {row['amount']} {row['unit']}")
                    wechat_text += f" └─ {row['item']} {row['amount']}{row['unit']}\n"
            st.write("---"); st.subheader("💬 复制群发对账文本")
            st.text_area("点击框内复制发回微信群：", value=wechat_text, height=150)
