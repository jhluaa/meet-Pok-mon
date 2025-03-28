import pickle
import pandas as pd
from langchain_graphrag.indexing import TextUnitExtractor, IndexerArtifacts
from langchain_openai import ChatOpenAI
import keys
from langchain_community.cache import SQLiteCache
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from typing import cast
from langchain_chroma.vectorstores import Chroma as ChromaVectorStore
from langchain_graphrag.query.global_search import GlobalSearch
from langchain_graphrag.query.global_search.community_weight_calculator import (
    CommunityWeightCalculator,
)
from langchain_graphrag.query.global_search.key_points_aggregator import (
    KeyPointsAggregator,
    KeyPointsAggregatorPromptBuilder,
    KeyPointsContextBuilder,
)
from langchain_graphrag.query.global_search.key_points_generator import (
    CommunityReportContextBuilder,
    KeyPointsGenerator,
    KeyPointsGeneratorPromptBuilder,
)
from langchain_graphrag.query.local_search import (
    LocalSearch,
    LocalSearchPromptBuilder,
    LocalSearchRetriever,
)
from langchain_graphrag.query.local_search.context_builders import (
    ContextBuilder,
)
from langchain_graphrag.query.local_search.context_selectors import (
    ContextSelector,
)
from langchain_graphrag.types.graphs.community import CommunityLevel
from langchain_graphrag.utils import TiktokenCounter

import warnings
warnings.filterwarnings("ignore")


def load_artifacts(path: Path) -> IndexerArtifacts:
    entities = pd.read_parquet(f"{path}/entities.parquet")
    relationships = pd.read_parquet(f"{path}/relationships.parquet")
    text_units = pd.read_parquet(f"{path}/text_units.parquet")
    communities_reports = pd.read_parquet(f"{path}/communities_reports.parquet")

    merged_graph = None
    summarized_graph = None
    communities = None

    merged_graph_pickled = path.joinpath("merged-graph.pickle")
    if merged_graph_pickled.exists():
        with merged_graph_pickled.open("rb") as fp:
            merged_graph = pickle.load(fp)  # noqa: S301

    summarized_graph_pickled = path.joinpath("summarized-graph.pickle")
    if summarized_graph_pickled.exists():
        with summarized_graph_pickled.open("rb") as fp:
            summarized_graph = pickle.load(fp)  # noqa: S301

    community_info_pickled = path.joinpath("community_info.pickle")
    if community_info_pickled.exists():
        with community_info_pickled.open("rb") as fp:
            communities = pickle.load(fp)  # noqa: S301

    return IndexerArtifacts(
        entities,
        relationships,
        text_units,
        communities_reports,
        merged_graph=merged_graph,
        summarized_graph=summarized_graph,
        communities=communities,
    )


artifacts = load_artifacts(Path() / "llm_models")


# 将筛选好的社区报告转换为文档
report_context_builder = CommunityReportContextBuilder(
    community_level=cast(CommunityLevel, 0), #筛选出≤该等级的社区报告
    weight_calculator=CommunityWeightCalculator(),
    artifacts=artifacts,
    token_counter=TiktokenCounter(),
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=keys.openai,
    base_url='https://api.chatanywhere.tech/v1',
    cache=SQLiteCache('cache.db'),
)

# 利用语言模型（LLM）生成关键点（key points）
kp_generator = KeyPointsGenerator(
    llm=llm,
    prompt_builder=KeyPointsGeneratorPromptBuilder(
        show_references=True, repeat_instructions=True
    ),
    context_builder=report_context_builder,
)

kp_aggregator = KeyPointsAggregator(
    llm=llm,
    prompt_builder=KeyPointsAggregatorPromptBuilder(
        show_references=True,
        repeat_instructions=True,
    ),
    context_builder=KeyPointsContextBuilder(
        token_counter=TiktokenCounter(),
    ),
    output_raw=True,
)

global_search = GlobalSearch(
    kp_generator=kp_generator,
    kp_aggregator=kp_aggregator,
    generation_chain_config={"tags": ["kp-generation"]},
    aggregation_chain_config={"tags": ["kp-aggregation"]},
)

response = global_search.invoke("海龟交易策略")
print(response.content)
# 流式输出
for chunk in global_search.stream("海龟交易策略"):
    print(chunk.content, end="", flush=True)

entities_vector_store = ChromaVectorStore(
    collection_name="entity-embedding",
    persist_directory=str(Path() / "vector_stores"),
    embedding_function=OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_base="https://api.chatanywhere.tech/v1",
        openai_api_key=keys.freeoopenai,
    ),
)

context_selector = ContextSelector.build_default(
    entities_vector_store=entities_vector_store,
    entities_top_k=10,
    community_level=cast(CommunityLevel, 2),
)

context_builder = ContextBuilder.build_default(
    token_counter=TiktokenCounter(),
)


retriever = LocalSearchRetriever(
    context_selector=context_selector,
    context_builder=context_builder,
    artifacts=artifacts,
)

local_search = LocalSearch(
    prompt_builder=LocalSearchPromptBuilder(
        show_references=True,
        repeat_instructions=True,
    ),
    llm=llm,
    retriever=retriever,
)

search_chain = local_search()

for chunk in search_chain.stream("均线", config={"tags": ["local-search"]}):
    print(chunk.content, end="", flush=True)
