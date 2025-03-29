import pickle
import pandas as pd
from langchain_graphrag.indexing import TextUnitExtractor, IndexerArtifacts
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_graphrag.indexing.graph_generation import EntityRelationshipExtractor, GraphsMerger, EntityRelationshipDescriptionSummarizer, GraphGenerator
from langchain_community.cache import SQLiteCache
from pyvis.network import Network
from langchain_graphrag.indexing.graph_clustering.leiden_community_detector import HierarchicalLeidenCommunityDetector
from langchain_graphrag.indexing.artifacts_generation import (
    CommunitiesReportsArtifactsGenerator,
    EntitiesArtifactsGenerator,
    RelationshipsArtifactsGenerator,
    TextUnitsArtifactsGenerator,
)
from langchain_graphrag.indexing.report_generation import (
    CommunityReportGenerator,
    CommunityReportWriter,
)
from langchain_graphrag.indexing import SimpleIndexer, TextUnitExtractor
from langchain_chroma.vectorstores import Chroma as ChromaVectorStore
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
import networkx as nx
import re

import warnings

warnings.filterwarnings("ignore")

# 读取pdf到一个Document对象中
def pdf_to_doc(pdf_path):
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()

    doc = Document(page_content=text)
    return doc
def generate_graph(graph, title='graph'):
    net = Network()
    for node in graph.nodes:
        net.add_node(node)

    for edge in graph.edges:
        net.add_edge(edge[0], edge[1])

    # 生成并显示图谱
    net.show(f"{title}.html", notebook=False)

doc1 = pdf_to_doc('test.pdf')
doc2 = pdf_to_doc('test1.pdf')

# 递归地将文本分割成块
spliter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
# 将分割后的文本块封装为结构化数据（如DataFrame）
text_unit_extractor = TextUnitExtractor(text_splitter=spliter)
textunit_df = text_unit_extractor.run([doc1, doc2])


# 配置大模型实例
llm = ChatOpenAI(
    # model="deepseek-chat",
    model="deepseek-chat",
    temperature=0.2,
    api_key='sk-b7d7105cd9634f3fbba34a3d59c1d500',
    # base_url='https://api.deepseek.com',
    base_url='https://api.deepseek.com/v1',
    cache=SQLiteCache('cache.db'),  # 使用SQLite作为缓存,用于存储模型的中间结果或重复请求的响应。
)



#1. 创建一个默认的实体抽取、关系提取
extractor = EntityRelationshipExtractor.build_default(llm=llm)

textunit_graph = extractor.invoke(textunit_df)

# for index, g in enumerate(textunit_graph):
#     print(f'nodes:{g.nodes()}')
#     print(f'edges:{g.edges()}')
#     print("---------------------------------")
#     generate_graph(g,title=f'graph_{index}')

#2.图合并
graphs_merger = GraphsMerger()
merged_graph = graphs_merger(textunit_graph)

# generate_graph(merged_graph,title='merged_graph')

#3.图清理
def sanitize_graph(graph: nx.Graph) -> nx.Graph:
    """
    清理图，删除以下节点及其对应的边：
    1. 包含英文字符的节点。
    2. 包含数字的节点。
    :param graph: 输入的图
    :return: 清理后的图
    """
    # 创建图的副本，避免直接修改原图
    def contains_english(s: str) -> bool:
        """
        判断字符串是否包含英文字符。
        :param s: 输入字符串
        :return: 如果包含英文字符，返回 True；否则返回 False
        """
        return bool(re.search(r'[a-zA-Z]', s))

    def contains_digit(s: str) -> bool:
        """
        判断字符串是否包含数字。
        :param s: 输入字符串
        :return: 如果包含数字，返回 True；否则返回 False
        """
        return bool(re.search(r'\d', s))
    sanitized_graph = graph.copy()

    # 找出包含英文字符或数字的节点
    nodes_to_remove = [
        node for node in sanitized_graph.nodes
        if contains_english(str(node)) or contains_digit(str(node))
    ]

    # 删除这些节点及其对应的边
    sanitized_graph.remove_nodes_from(nodes_to_remove)

    return sanitized_graph

sanitized_graph = sanitize_graph(merged_graph)
# generate_graph(sanitized_graph, title='sanitized_graph')


#4. 总结
summarizer = EntityRelationshipDescriptionSummarizer.build_default(llm=llm)
summarizer_graph = summarizer.invoke(sanitized_graph.copy())
generate_graph(summarizer_graph, title='summarizer_graph')

# for sanitized_node_key, summarizer_node_key in zip(sanitized_graph.nodes, summarizer_graph.nodes):
#     print(f'{sanitized_graph.nodes[sanitized_node_key]["description"]}')
#     print(f'{summarizer_graph.nodes[summarizer_node_key]["description"]}')
#     print("---------------------------------")

community_detector = HierarchicalLeidenCommunityDetector(max_cluster_size=10, use_lcc=True)
community_detection_result = community_detector.run(merged_graph)
# %% 实体报告
output_dir = Path()
output_dir.mkdir(parents=True, exist_ok=True)
cache_dir = Path()
cache_dir.mkdir(parents=True, exist_ok=True)
vector_store_dir = output_dir / "vector_stores"
artifacts_dir = output_dir / "llm_models"
artifacts_dir.mkdir(parents=True, exist_ok=True)

entities_vector_store = ChromaVectorStore(
    collection_name="entity-embedding",
    persist_directory=str(vector_store_dir),
    embedding_function=OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_base="https://api.chatanywhere.tech/v1",
        openai_api_key='',
    ),
)


entities_artifacts_generator = EntitiesArtifactsGenerator(
    entities_vector_store=entities_vector_store
)

df_entities = entities_artifacts_generator.run(
    community_detection_result,
    summarizer_graph,
)

# %%
# 关系报告
relationships_artifacts_generator = RelationshipsArtifactsGenerator()
df_relationships = relationships_artifacts_generator.run(summarizer_graph)
# %%
# 社区报告
report_generator = CommunityReportGenerator.build_default(
    llm=llm,
    chain_config={"tags": ["community-report"]},
)
report_writer = CommunityReportWriter()

communities_report_artifacts_generator = CommunitiesReportsArtifactsGenerator(
    report_generator=report_generator,
    report_writer=report_writer,
)

df_communities_reports = communities_report_artifacts_generator.run(
    community_detection_result,
    summarizer_graph,
)

# %% 文本报告
text_units_artifacts_generator = TextUnitsArtifactsGenerator()
df_text_units = text_units_artifacts_generator.run(
    textunit_df,
    df_entities,
    df_relationships,
)

# %% 建立索引
artifacts = IndexerArtifacts(
    entities=df_entities,
    relationships=df_relationships,
    text_units=df_text_units,
    communities_reports=df_communities_reports,
    summarized_graph=summarizer_graph,
    merged_graph=merged_graph,
    communities=community_detection_result,
)

artifacts.report()

#%% 保存数据
def save_artifacts(artifacts: IndexerArtifacts, path: Path):
    artifacts.entities.to_parquet(f"{path}/entities.parquet")
    artifacts.relationships.to_parquet(f"{path}/relationships.parquet")
    artifacts.text_units.to_parquet(f"{path}/text_units.parquet")
    artifacts.communities_reports.to_parquet(f"{path}/communities_reports.parquet")

    if artifacts.merged_graph is not None:
        with path.joinpath("merged-graph.pickle").open("wb") as fp:
            pickle.dump(artifacts.merged_graph, fp)

    if artifacts.summarized_graph is not None:
        with path.joinpath("summarized-graph.pickle").open("wb") as fp:
            pickle.dump(artifacts.summarized_graph, fp)

    if artifacts.communities is not None:
        with path.joinpath("community_info.pickle").open("wb") as fp:
            pickle.dump(artifacts.communities, fp)


save_artifacts(artifacts, artifacts_dir)


