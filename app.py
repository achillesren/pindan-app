import streamlit as st
import re 

st.set_page_config(page_title="微信拼单助手", page_icon="🐷")
st.title("🐷 微信群拼单自动记账器") 

raw_text = st.text_area("📋 把群里的接龙文字复制到这里：", height=300) 

if st.button("🚀 一键计算总账", type="primary"):
if not raw_text.strip():
st.warning("请先粘贴接龙文字。")
else: 

### 分离出每个带有【】的肉类块

blocks = re.findall(r'(【[^】]+】.*?)(?=【|$)', raw_text, re.DOTALL)
user_bills = {} 

for block in blocks:
lines = block.strip().split('\n')
header = lines 

### 提取单价

price = 0.0
price_match = re.search(r'([\d.]+)\s*/', header)
if price_match:
price = float(price_match.group(1)) 

### 提取人名和数量

for line in lines[1:]:
member_match = re.match(r'^\d+\s*[.\s、-]\s*([^\d\s\s]+.*?)\s*([\d.]+)', line.strip())
if member_match:
user_name = member_match.group(1).strip()
amount = float(member_match.group(2))
if user_name and user_name not in [".", "、"]:
cost = amount * price
if user_name not in user_bills:
user_bills[user_name] = 0.0
user_bills[user_name] += cost 

### 打印算账结果

st.subheader("💰 每个人应付总金额")
if not user_bills:
st.info("没找到人名或订购数量，请检查格式。")
else:
wechat_text = "📊 【拼单对账结果】\n大家核对好金额后可以私信转账啦：\n"
for user, total_cost in user_bills.items():
st.success(f"👤 {user} —— 总计应付: **{total_cost:.2f}**")
wechat_text += f"\n@{user}  应付：{total_cost:.2f}\n" 

st.write("---")
st.subheader("💬 微信群群发文本")
st.text_area("直接复制框内所有文本发到群里：", value=wechat_text, height=200)

