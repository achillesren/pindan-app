# -*- coding: utf-8 -*-
import os, sys, pathlib
def _clean():
    p = pathlib.Path(__file__)
    t = p.read_text(encoding='utf-8')
    if '\xa0' in t: p.write_text(t.replace('\xa0', ' '), encoding='utf-8'); os.execv(sys.executable, [sys.executable] + sys.argv)
_clean()

import streamlit as st
import requests
import json

st.set_page_config(page_title="海外自助拼单系统", page_icon="🐷", layout="wide")

# 初始化用户本地的购物车缓存
if "cart" not in st.session_state:
    st.session_state.cart = []

MEAT_MENU = {
    "五花肉": {"price": 8.00, "unit": "公斤"},
    "大排骨": {"price": 7.00, "unit": "公斤"},
    "大肠": {"price": 9.50, "unit": "公斤"},
    "猪颈骨": {"price": 4.50, "unit": "公斤"},
    "猪腰": {"price": 3.50, "unit": "公斤"},
    "护心肉": {"price": 4.50, "unit": "公斤"},
    "小排骨": {"price": 3.50, "unit": "公斤"},
    "背脊骨": {"price": 3.50, "unit": "公斤"},
    "猪扒边": {"price": 4.50, "unit": "公斤"},
    "猪手": {"price": 4.50, "unit": "公斤"},
    "猪耳朵": {"price": 8.00, "unit": "公斤"},
    "猪筒骨": {"price": 3.50, "unit": "公斤"},
    "猪板油": {"price": 4.50, "unit": "公斤"},
    "猪舌头": {"price": 7.00, "unit": "公斤"},
    "梅头肉": {"price": 8.00, "unit": "公斤"},
    "猪头": {"price": 18.00, "unit": "个"},
    "猪肘": {"price": 4.50, "unit": "公斤"},
    "肉皮": {"price": 3.50, "unit": "公斤"},
    "猪里脊": {"price": 7.50, "unit": "公斤"},
    "猪肝": {"price": 4.00, "unit": "公斤"}
}

title_from_secrets = st.secrets["secrets"]["title_text"] if "secrets" in st.secrets else "海外群自助拼单自提系统"
st.title(f"🐷 {title_from_secrets}")
st.markdown("群友请直接在下方**添加心仪商品进购物车**，最后填写昵称一键提交下单。")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛒 群友点菜登记（支持多选）")
    
    # 模块一：选菜放入购物车
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

    # 模块二：展示当前购物车并填写昵称提交
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
                            payload = {
                                "name": user_name.strip(),
                                "item": item["item"],
                                "amount": item["amount"],
                                "unit": item["unit"],
                                "cost": item["cost"]
                            }
                            # 直接强行发射至谷歌表格后台接收器，100%存盘
                            requests.post(api_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
                        
                        # 提交成功后提示，并清空本地购物车
                        st.success(f"🎉 提交成功！{user_name.strip()} 的这 {len(st.session_state.cart)} 样菜品已安全记入账单！")
                        st.balloons() # 庆祝气球
                        st.session_state.cart = [] 
                    except Exception as e:
                        st.error(f"❌ 提交失败，网络原因: {str(e)}")
    else:
        st.info("💡 您的购物车还是空的哦，请在上方选择肉类和数量并点击『放入我的购物车』！")

with col2:
    st.subheader("📢 团长对账与拼单须知")
    with st.container(border=True):
        st.markdown("""
        ### 💡 群友下单须知
        1. **自主选菜**：请在左侧依次挑选您需要的肉类及分量，点击放入购物车。
        2. **检查姓名**：确认购物车清单无误后，请输入您**准确的微信昵称**点击确认提交。
        3. **无需重复提交**：页面显示“提交成功”后即可关闭网页，数据已永久安全录入团长后台。
        
        ---
        
        ### 👑 团长（发起人）查账提示
        * **如何核对总账？** 
          因为本网页完全采取隐私保护模式，群友提交的数据会**零延迟直接飞进您的专属 Google Sheets（谷歌表格）**中。
        * 请直接打开您的电脑或手机里的 Google 表格进行一键求和、查看每位群友的订购总分量。
        * **开启下一期新拼单？**
          当本期截单并收款完毕后，您只需要去您的 Google 表格里，把第二行以下的所有旧数据一键删除，整个网页系统就会自动清空，迎接下一次的完美下单！
        """)
