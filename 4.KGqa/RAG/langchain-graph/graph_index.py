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


doc1 = pdf_to_doc('./海龟交易法则_130-135.pdf')
doc2 = pdf_to_doc('./海龟交易法则_136-142.pdf')

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



graph_generator = GraphGenerator(
    er_extractor=EntityRelationshipExtractor.build_default(llm=llm),
    graphs_merger=GraphsMerger(),
    graph_sanitizer=sanitize_graph,
    er_description_summarizer=EntityRelationshipDescriptionSummarizer.build_default(llm=llm),
)
merged_graph, summarized_graph = graph_generator.run(textunit_df)


community_detector = HierarchicalLeidenCommunityDetector(max_cluster_size=10, use_lcc=True)
community_detection_result = community_detector.run(merged_graph)


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
        model="bge-zh",
        openai_api_base="http://139.224.116.116:3000/v1",
        openai_api_key='sk-7egdiZg0g9LaGJnX4973895138C148FbAcF5E96e1cAdEd00',
    ),
)


entities_artifacts_generator = EntitiesArtifactsGenerator(
    entities_vector_store=entities_vector_store
)
relationships_artifacts_generator = RelationshipsArtifactsGenerator()
df_relationships = relationships_artifacts_generator.run(summarized_graph)
text_units_artifacts_generator = TextUnitsArtifactsGenerator()


report_generator = CommunityReportGenerator.build_default(
    llm=llm,
    chain_config={"tags": ["community-report"]},
)
report_writer = CommunityReportWriter()

communities_report_artifacts_generator = CommunitiesReportsArtifactsGenerator(
    report_generator=report_generator,
    report_writer=report_writer,
)

# %%
indexer = SimpleIndexer(
    text_unit_extractor=text_unit_extractor,
    graph_generator=graph_generator,
    community_detector=community_detector,
    entities_artifacts_generator=entities_artifacts_generator,
    relationships_artifacts_generator=relationships_artifacts_generator,
    text_units_artifacts_generator=text_units_artifacts_generator,
    communities_report_artifacts_generator=communities_report_artifacts_generator,
)

artifacts = indexer.run([doc1, doc2])
# %%
