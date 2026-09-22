import streamlit as st
import re
import pandas as pd
from io import BytesIO 

st.set_page_config(page_title="微信群拼单智能统计工具", page_icon="🐷", layout="wide") 

st.title("🐷 微信群拼单智能解析统计工具")
st.markdown("把微信群里拼单接龙的文本**直接复制粘贴**到下方，一键生成每个人的账单和商品统计。") 

with st.sidebar:
st.header("💡 使用说明")
st.write("1. 复制微信群里的接龙文本。")
st.write("2. 粘贴到右侧输入框。")
st.write("3. 点击『开始智能解析』。")
st.write("4. 即可查看【每人账单汇总】和【肉类拼单进度】。") 

raw_text = st.text_area("📋 请在此粘贴微信接龙文本：", height=350, placeholder="在此粘贴群里的文字...") 

def parse_pindan(text):
if not text.strip():
return {}, {} 

blocks = re.findall(r'(【[^】]+】.*?)(?=【|$)', text, re.DOTALL)
item_stats = {}
user_bills = {}

for block in blocks:
lines = block.strip().split('\n')
header = lines[0].strip()
item_name_match = re.search(r'【(.*?)】', header)
if not item_name_match:
    continue
item_name = item_name_match.group(1).strip()

price = 0.0
unit = "公斤"
price_match = re.search(r'([\d.]+)\s*/\s*([a-zA-Z\u4e00-\u9fa5\d]+)', header)
if price_match:
    price = float(price_match.group(1))
    unit = price_match.group(2)

box_weight = 0.0
weight_match = re.search(r'(\d+)\s*(公斤|kg|块)', header)
if weight_match:
    box_weight = float(weight_match.group(1))

if item_name not in item_stats:
    item_stats[item_name] = {"price": price, "unit": unit, "box_weight": box_weight, "total_booked": 0.0, "details": []}
    
for line in lines[1:]:
    line = line.strip()
    member_match = re.match(r'^\d+\s*[.\s、-]\s*([^\d\s\s]+.*?)\s*([\d.]+)\s*(公斤|kg|块|个)?', line, re.IGNORECASE)
    if member_match:
        user_name = member_match.group(1).strip()
        if not user_name or user_name in ["", ".", "、"]:
            continue
        
        amount = float(member_match.group(2))
        cost = amount * price
        
        item_stats[item_name]["total_booked"] += amount
        item_stats[item_name]["details"].append({"name": user_name, "amount": amount, "cost": cost})
        
        if user_name not in user_bills:
            user_bills[user_name] = {"total_cost": 0.0, "items": []}
        user_bills[user_name]["total_cost"] += cost
        user_bills[user_name]["items"].append({"item": item_name, "amount": amount, "unit": unit, "cost": cost})

return item_stats, user_bills

if st.button("🚀 开始智能解析", type="primary"):
if not raw_text.strip():
st.warning("请先粘贴一些文本内容。")
else:
item_stats, user_bills = parse_pindan(raw_text) 

tab1, tab2, tab3 = st.tabs(["💰 个人账单汇总", "📦 货物及成箱进度", "💬 微信群对账文本"])

with tab1:
    st.subheader("📋 每个人应付金额")
    if not user_bills:
        st.info("没有解析到有效的订购人信息。")
    else:

### 导出 Excel 准备

excel_data = []
for user, data in user_bills.items():
with st.expander(f"👤 {user} —— 总计应付: **{data['total_cost']:.2f}**"):
for it in data["items"]:
st.write(f"- {it['item']}: {it['amount']} {it['unit']} (金额: {it['cost']:.2f})")
excel_data.append({"微信昵称": user, "订购商品": it['item'], "数量": it['amount'], "单位": it['unit'], "单价": item_stats[it['item']]['price'], "小计金额": it['cost']}) 

# Excel 导出按钮
df = pd.DataFrame(excel_data)
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='拼单对账单')
st.download_button(label="📥 下载 Excel 账单表格", data=output.getvalue(), file_name="拼单明细汇总表.xlsx", mime="application/vnd.ms-excel")

with tab2:
st.subheader("🥩 货物订购总量与成箱缺口")
if not item_stats:
st.info("没有解析到商品信息。")
else:
for item_name, info in item_stats.items():
if info["total_booked"] > 0:
st.markdown(f"### 【{item_name}】")
st.write(f"单价: {info['price']} / {info['unit']} | 已订购总量: **{info['total_booked']}** {info['unit']}") 

        if info["box_weight"] > 0:
            box_weight = info["box_weight"]
            total_booked = info["total_booked"]
            current_boxes = total_booked / box_weight
            needed_next = box_weight - (total_booked % box_weight)
            if total_booked % box_weight == 0:
                st.success(f"🎉 刚好凑满 {int(current_boxes)} 箱！")
            else:
                st.info(f"📊 当前进度: 约 {current_boxes:.2f} 箱（还差 **{needed_next:.1f}** {info['unit']} 凑满整箱）")
        
        detail_text = ", ".join([f"{d['name']}({d['amount']}{info['unit']})" for d in info["details"]])
        st.caption(f"👥 订购明细: {detail_text}")
        st.write("---")

with tab3:
st.subheader("💬 复制下方文字发回微信群")
if not user_bills:
st.info("暂无账单数据。")
else:
wechat_text = "📊 【拼单对账结果通知】\n大家核对好金额后可以私信转账啦：\n"
for user, data in user_bills.items():
wechat_text += f"\n@{user}  应付：{data['total_cost']:.2f}\n"
for it in data["items"]:
wechat_text += f" └─ {it['item']} {it['amount']}{it['unit']}\n"
st.text_area("直接复制框内所有文本发到群里：", value=wechat_text, height=300)
