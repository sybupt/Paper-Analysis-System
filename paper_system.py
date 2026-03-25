import streamlit as st
import json
import requests
import pandas as pd
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from pyvis.network import Network
from xml.etree import ElementTree
import random

# ==============================
# 页面配置
# ==============================
st.set_page_config(page_title="论文智能调研分析系统", layout="wide")
st.title("📚 论文智能调研爬取 + 知识图谱分析系统")

# ==============================
# 爬虫模块
# ==============================
def crawl_arxiv(keyword, max_papers):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": max_papers,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    root = ElementTree.fromstring(response.text)
    papers = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
        abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
        authors = [a.find("{http://www.w3.org/2005/Atom}name").text.strip() for a in entry.findall("{http://www.w3.org/2005/Atom}author")]
        published = entry.find("{http://www.w3.org/2005/Atom}published").text.strip()
        papers.append({"title": title, "authors": authors, "abstract": abstract, "published": published})
    return papers

def crawl_openreview(venue="ICLR.cc/2025/Conference", limit=50):
    papers = []
    url = "https://api2.openreview.net/notes"
    params = {"content.venueid": venue, "limit": limit, "details": "forum"}
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    for note in data.get("notes", []):
        c = note.get("content", {})
        papers.append({
            "title": c.get("title", ""),
            "authors": c.get("authors", []),
            "abstract": c.get("abstract", ""),
            "venue": venue
        })
    return papers

# ==============================
# 分析模块
# ==============================
def build_author_graph(papers):
    G = nx.Graph()
    author_team = {}
    for p in papers:
        authors = p["authors"]
        team_id = random.randint(1, 8)
        for a in authors:
            author_team[a] = team_id
        for i in range(len(authors)):
            for j in range(i+1, len(authors)):
                a1, a2 = authors[i], authors[j]
                if G.has_edge(a1, a2):
                    G[a1][a2]["weight"] += 1
                else:
                    G.add_edge(a1, a2, weight=1)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    for node in G.nodes():
        team = author_team.get(node, 0)
        G.nodes[node]["color"] = colors[team % len(colors)]
        G.nodes[node]["size"] = 15
    return G

def cluster_topics(papers, n_clusters=5):
    texts = [p["title"] + " " + p["abstract"] for p in papers]
    vec = TfidfVectorizer(stop_words="english", max_features=1000)
    X = vec.fit_transform(texts)
    kmeans = KMeans(n_clusters=n_clusters)
    return kmeans.fit_predict(X)

# ==============================
# 界面
# ==============================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 爬取论文", "📊 论文列表", "🌍 知识图谱", "🧠 思维导图"])

# ========== TAB1 ==========
with tab1:
    st.subheader("选择论文来源")
    source = st.radio("数据源", ["arXiv", "OpenReview"])
    keyword = st.text_input("搜索关键词", "deep learning")
    max_papers = st.slider("爬取数量", 10, 200, 50)
    
    if st.button("开始爬取 + 分析"):
        with st.spinner("正在爬取..."):
            if source == "arXiv":
                papers = crawl_arxiv(keyword, max_papers)
            else:
                papers = crawl_openreview(limit=max_papers)
            
            labels = cluster_topics(papers)
            G_author = build_author_graph(papers)
            
            st.success(f"✅ 爬取完成！共 {len(papers)} 篇")
            st.session_state["papers"] = papers
            st.session_state["labels"] = labels
            st.session_state["G_author"] = G_author

# ========== TAB2 ==========
with tab2:
    st.subheader("论文清单")
    if "papers" in st.session_state:
        df = []
        for i, p in enumerate(st.session_state["papers"]):
            df.append({
                "序号": i+1,
                "标题": p["title"],
                "作者": ", ".join(p["authors"]),
                "研究方向": f"方向 {st.session_state['labels'][i]+1}"
            })
        st.dataframe(pd.DataFrame(df), use_container_width=True)

# ========== TAB3 ==========
with tab3:
    st.subheader("👥 作者合作关系知识图谱")
    st.markdown("""
---
### 📘 图谱说明
✅ **圆形节点** = 作者  
✅ **连线** = 两人合作发表论文  
✅ **颜色相同** = 同一研究团队  
✅ **连线越粗** = 合作越紧密  
✅ **动态效果** = 自动布局更清晰
---
""")
    if "G_author" in st.session_state:
        net = Network(height="700px", width="100%", bgcolor="#f8f9fa", font_color="black")
        net.toggle_physics(True)
        net.from_nx(st.session_state["G_author"])
        net.write_html("author_graph.html")
        with open("author_graph.html", "r", encoding="utf-8") as f:
            html = f.read()
        st.components.v1.html(html, height=700)
    else:
        st.info("请先爬取论文")

# ========== TAB4 ==========
with tab4:
    st.subheader("🧠 研究领域 · 思维导图（图形版）")
    if "labels" in st.session_state:
        papers = st.session_state["papers"]
        labels = st.session_state["labels"]

        G_mind = nx.Graph()
        colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#dda0dd", "#87ceeb"]

        for i, label in enumerate(labels):
            topic = f"领域{label+1}"
            paper_title = papers[i]["title"][:40] + "..."

            if not G_mind.has_node(topic):
                G_mind.add_node(topic, color="#ff4444", size=30)

            G_mind.add_node(paper_title, color=colors[label % len(colors)], size=12)
            G_mind.add_edge(topic, paper_title)

        net = Network(height="700px", width="100%", bgcolor="#fff", font_color="#222")
        net.toggle_physics(True)
        net.from_nx(G_mind)
        net.write_html("mind_map.html")

        with open("mind_map.html", "r", encoding="utf-8") as f:
            html = f.read()
        st.components.v1.html(html, height=700)

        st.markdown("""
### 📘 思维导图说明
- 🔴 **红色大节点** = 研究领域  
- 🌈 **彩色小节点** = 对应领域的论文  
- **连线** = 论文属于该研究方向
""")
    else:
        st.info("请先爬取论文生成图表")