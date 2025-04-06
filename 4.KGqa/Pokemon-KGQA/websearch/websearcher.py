from typing import List, Dict
from .milvus_service import MilvusService
from .utils import *
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

class WebSearcher:
    def __init__(
        self,
        milvus_collection: str = "test",
        embedding_model: str = "bge-m3-pro",
        search_top_k: int = 10,
        rerank_top_k: int = 5,
        rag_top_k: int = 3,
        llm: str = "deepseek-ai/DeepSeek-V3"
    ):
        """
        初始化网络搜索器
        :param milvus_collection: Milvus集合名称
        :param embedding_model: 嵌入模型名称
        :param search_top_k: 初始搜索返回结果数量
        :param rerank_top_k: 重排序后保留结果数量
        """
        self.milvus = MilvusService(
            collection_name=milvus_collection,
            embedding_model=embedding_model,
            overwrite=True
        )
        self.search_top_k = search_top_k
        self.rerank_top_k = rerank_top_k
        self.rag_top_k = rag_top_k
        
        # 定义提示模板
        self.prompt_templates = {
            "with_context": PromptTemplate(
                template=(
                    "<指令>根据你实时联网检索到的信息，更加专业的来回答用户提出的问题。如果无法从中得到答案，请说 "
                    "'根据检索到的信息无法回答该问题'，同时，如果存在历史对话信息，请结合历史对话信息提供完整的回复，"
                    "不允许在答案中添加编造成分，答案请使用中文。</指令>\n"
                    "<联网检索到的信息>{context}</联网检索到的信息>\n"
                    "<问题>{question}</问题>\n"
                ),
                input_variables=["context", "question"]
            ),
            "without_context": PromptTemplate(
                template="请你回答我的问题:\n{question}\n\n",
                input_variables=["question"]
            )
        }
        self.llm = ChatOpenAI(
            model=llm,  # 模型名称（需与后端匹配）
            base_url="http://139.224.116.116:3000/v1",  # 本地或远程 API 地址
            api_key="sk-36oMlDApF5Nlg0v23014A4B69e864000944151Cd75D82076"  # 如果无需鉴权，可留空
)

    async def search(self, query: str) -> Dict[str, str]:
        """
        执行完整搜索流程并返回格式化结果
        :param query: 用户查询文本
        :return: {"prompt_template": str, "context": str}
        """
        # 1. 执行初始搜索
        raw_results = await search(query, self.search_top_k)
        
        # 2. 结果重排序
        ranked_results = reranking(query, raw_results, self.rerank_top_k)
        rerank_snippets = [doc.metadata['snippet'] for doc in ranked_results if 'snippet' in doc.metadata]
        # 3. 获取详情内容
        detailed_results = await fetch_details(ranked_results)
        
        # 4. 处理结果并生成prompt
        return self.generate_output(query, detailed_results, rerank_snippets)

    def generate_output(self, query: str, results: List[Document], rerank_snippets:List[str]) -> Dict[str, str]:
        """生成最终输出"""
        if not results and not rerank_snippets:
            return {
                "prompt_template": self.prompt_templates["without_context"],
                "context": ""
            }
        
        # 将结果存入向量库
        self.milvus.insert_documents(results)
        
        # 语义搜索最相关内容
        retrieved = self.milvus.similarity_search(query, k=self.rag_top_k)
        search_contents = [doc.page_content for doc in retrieved]
        
        # 合并并去重
        combined_contents = list(set(rerank_snippets + search_contents))
        # 拼接成最终context
        context = "\n\n".join(combined_contents)
        return {
            "prompt_template": self.prompt_templates["with_context"],
            "context": context
        }
        
    async def generate_answer(
        self,
        question: str,
        context: str
    ) -> str:
        """
        使用大模型生成回复
        :param question: 用户问题
        :param context: 检索到的上下文
        :return: 生成的回答
        """
        # 选择模板
        template = (
            self.prompt_templates["with_context"] 
            if context 
            else self.prompt_templates["without_context"]
        )
        
        # 构建输入
        input_dict = {
            "question": question,
            "context": context
        }
        
        # 构建处理链
        chain = template | self.llm
        
        # 生成回复
        response = await chain.ainvoke(input_dict)
        return response
    
    async def search_and_generate(
        self, 
        query: str
    ) -> str:
        # 1. 执行搜索
        search_result = await self.search(query)
        
        # 2. 如果有LLM则生成回复
        answer = ""
        if self.llm:
            answer = await self.generate_answer(
                question=query,
                context=search_result["context"]
            )
        
        return answer.content


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 示例用法
        searcher = WebSearcher()
        
        
        # 测试查询
        query = "苏州今天天气怎么样？"
        print(f"正在执行搜索查询: {query}")
        
        result = await searcher.search_and_generate(query)
        
        # print("\n=== 搜索结果 ===")
        # print("使用的模板:", result["prompt_template"])
        # print("检索到的内容:", result["context"])
        print("=====模型回复=====")
        print(result)
            
        
        # 清理资源
        searcher.milvus.close()
    
    # 运行主程序
    asyncio.run(main())