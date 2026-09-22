import streamlit as st 

st.set_page_config(page_title="群友自助点菜", page_icon="🐷")
st.title("🐷 海外微信群——自助拼单系统")
st.markdown("群友请在下方**输入昵称、选择肉类和数量**提交下单。") 

### 初始化存储数据的地方

if "orders" not in st.session_state:
st.session_state.orders = [] 

### 定义菜单

prices = {"五花肉": 8.0, "大排骨": 7.0, "大肠": 9.5, "小排骨": 3.5, "猪筒骨": 3.5} 

### 1. 收集群友的下单信息

with st.form("my_form", clear_on_submit=True):
name = st.text_input("👤 您的微信昵称：")
meat = st.selectbox("🥩 选择要买的肉类：", list(prices.keys()))
num = st.number_input("🔢 订购数量(公斤)：", min_value=0.5, value=1.0, step=0.5)
submit = st.form_submit_button("🚀 提交我的拼单", type="primary") 

if submit:
if name.strip():
cost = num * prices[meat]
st.session_state.orders.append({"name": name.strip(), "meat": meat, "num": num, "cost": cost})
st.success(f"🎉 {name} 成功预订了 {meat} {num}公斤！")
else:
st.error("请输入名字后再提交！")
### 2. 实时展示对账单

st.write("---")
st.subheader("📊 实时拼单对账看板") 

if not st.session_state.orders:
st.info("当前还没有人下单，把网址发到群里让大家开始点菜吧！")
else:
wechat_text = "📊 【自助拼单实时对账单】\n" 

### 按名字归类算账

bills = {}
for o in st.session_state.orders:
if o["name"] not in bills:
bills[o["name"]] = 0.0
bills[o["name"]] += o["cost"] 

for user, total in bills.items():
st.warning(f"👤 **{user}** —— 累计应付: **{total:.2f}**")
wechat_text += f"\n@{user} 应付：{total:.2f}\n" 

st.write("---")
st.caption("💬 团长专用：复制下方文本发回微信群催款")
st.text_area("直接全选复制：", value=wechat_text, height=120)
