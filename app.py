import streamlit as st
import re 

### 设置页面标题

st.set_page_config(page_title="微信群拼单智能统计工具", page_icon="🐷", layout="wide") 

st.title("🐷 微信群拼单智能解析统计工具")
st.markdown("把微信群里拼单接龙的文本**直接复制粘贴**到下方，一键生成每个人的账单和商品统计。") 

### 侧边栏说明

with st.sidebar:
st.header("💡 使用说明")
st.write("1. 复制微信群里的接龙文本。")
st.write("2. 粘贴到右侧输入框。")
st.write("3. 点击『开始智能解析』。")
st.write("4. 即可查看【每人账单汇总】和【肉类拼单进度】。") 

### 输入框

raw_text = st.text_area("📋 请在此粘贴微信接龙文本：", height=400, placeholder="在此粘贴群里的文字...") 

def parse_pindan(text):
if not text.strip():
return {}, {} 

### 匹配商品块，形如：【商品名】规格/箱 价格/公斤

### 匹配规则：查找【...】以及它后面直到下一个【 出现前的所有内容

blocks = re.findall(r'(【[^】]+】.*?)(?=【|$)', text, re.DOTALL) 

item_stats = {} # 统计商品拼单量
user_bills = {} # 统计每人账单 

for block in blocks:
lines = block.strip().split('\n')
header = lines.strip() 

### 提取商品名

item_name_match = re.search(r'【(.*?)】', header)
if not item_name_match:
continue
item_name = item_name_match.group(1).strip() 

### 提取单价 (寻找类似 8.00/公斤, 7/公斤, 18/1个, 8/kg 的格式)

price = 0.0
unit = "公斤"
price_match = re.search(r'([\d.]+)\s*/\s*([a-zA-Z\u4e00-\u9fa5]+)', header)
if price_match:
price = float(price_match.group(1))
unit = price_match.group(2)
else: 

### 兼容【猪头】18/1个 这种直接接数字的

price_match_alt = re.search(r'】\s*([\d.]+)\s*/\s*([\d\w\u4e00-\u9fa5]+)', header)
if price_match_alt:
price = float(price_match_alt.group(1))
unit = price_match_alt.group(2) 

### 提取整箱规格

box_weight = 0.0
weight_match = re.search(r'(\d+)\s*(公斤|kg|块)', header)
if weight_match:
box_weight = float(weight_match.group(1)) 

### 初始化商品统计

if item_name not in item_stats:
item_stats[item_name] = {"price": price, "unit": unit, "box_weight": box_weight, "total_booked": 0.0, "details": []} 

### 解析接龙的人

for line in lines[1:]:
line = line.strip() 

### 匹配形如 "1. joker 5kg" 或 "2. 艾  5公斤" 或 "1. joker  1块"

member_match = re.match(r'^\d+\s*[.\s、-]\s*([^\d\s\s]+.*?)\s*([\d.]+)\s*(公斤|kg|块|个)?', line, re.IGNORECASE)
if member_match:
user_name = member_match.group(1).strip() 

### 过滤掉明显的空行或者只是数字序号的行

if not user_name or user_name in ["", ".", "、"]:
continue 

amount = float(member_match.group(2))
cost = amount * price 

### 累加到商品统计

item_stats[item_name]["total_booked"] += amount
item_stats[item_name]["details"].append({"name": user_name, "amount": amount, "cost": cost}) 

        # 累加到个人账单
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

### 展示结果布局

tab1, tab2 = st.tabs(["💰 个人账单汇总", "📦 货物及成箱进度"]) 

with tab1:
st.subheader("📋 每个人应付金额")
if not user_bills:
st.info("没有解析到有效的订购人信息。")
else:
for user, data in user_bills.items():
with st.expander(f"👤 {user} —— 总计应付: **{data['total_cost']:.2f} 元**"):
for it in data["items"]:
st.write(f"- {it['item']}: {it['amount']} {it['unit']} (金额: {it['cost']:.2f} 元)") 

with tab2:
st.subheader("🥩 货物订购总量与成箱缺口")
if not item_stats:
st.info("没有解析到商品信息。")
else:
for item_name, info in item_stats.items():
if info["total_booked"] > 0:
st.markdown(f"### 【{item_name}】")
st.write(f"单价: {info['price']} / {info['unit']} | 已订购总量: **{info['total_booked']}** {info['unit']}") 

### 如果有箱体重量，计算箱数和缺口

if info["box_weight"] > 0:
box_weight = info["box_weight"]
total_booked = info["total_booked"]
current_boxes = total_booked / box_weight
needed_next = box_weight - (total_booked % box_weight)
if total_booked % box_weight == 0:
st.success(f"🎉 刚好凑满 {int(current_boxes)} 箱！")
else:
st.info(f"📊 当前进度: 约 {current_boxes:.2f} 箱（还差 **{needed_next:.1f}** {info['unit']} 凑满整箱）") 

### 打印这个商品谁买了

detail_text = ", ".join([f"{d['name']}({d['amount']}{info['unit']})" for d in info["details"]])
st.caption(f"👥 订购明细: {detail_text}")
st.write("---")
