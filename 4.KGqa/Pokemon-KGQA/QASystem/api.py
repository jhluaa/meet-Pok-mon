from flask import Flask, request, jsonify
from neo4j import GraphDatabase, exceptions
from question_classifier import *
from question_parser import *
from answer_search import *

app = Flask(__name__)

# Neo4j 连接配置
uri = "neo4j://10.168.2.232:7687"  # Neo4j 服务器 URI
username = "neo4j"
password = "n91msw52PSOrM#7#"

driver = GraphDatabase.driver(uri, auth=(username, password))


# 直接验证 Cypher 查询语法
def validate_cypher_query(cypher_query: str) -> bool:
    try:
        with driver.session() as session:
            # 验证查询语法
            session.run(f"EXPLAIN {cypher_query}")
        return True
    except exceptions.CypherSyntaxError as e:
        print(f"Cypher 语法错误: {e}")
        return False
    except Exception as e:
        print(f"意外错误: {e}")
        return False


# 执行 Cypher 查询并返回结果
def execute_cypher_query(cypher_query: str) -> list:
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            records = [record.data() for record in result]
        return records
    except Exception as e:
        raise Exception(f"查询执行错误: {str(e)}")


# ChatBotGraph 类
class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()

    def chat_main(self, sent):
        answer = "你好，根据现在建立的图谱，不存在所需的查询内容。"

        # 分类
        res_classify = self.classifier.classify(sent)
        if not res_classify:
            return answer

        # 解析
        res_sql = self.parser.parser_main(res_classify)

        # 保存最终答案
        final_answers = []

        # 遍历所有的 SQL 查询
        for sql_ in res_sql:
            question_type = sql_["question_type"]
            queries = sql_["sql"]

            # 处理每个 SQL 语句
            for query in queries:
                # 执行查询
                ress = execute_cypher_query(query)

                # 如果查询有结果，格式化后返回
                if ress:
                    result_str = "\n".join([str(record) for record in ress])
                    final_answers.append(result_str)

        # 返回查询结果
        if final_answers:
            return "\n\n".join(final_answers)
        else:
            return "未找到相关数据。"


# Flask 路由处理查询请求
@app.route("/execute_query", methods=["POST"])
def execute_query():
    data = request.get_json()

    # 获取问句
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "缺少 'question' 参数。"}), 400

    # 创建 ChatBotGraph 实例
    handler = ChatBotGraph()

    # 获取处理后的查询结果
    answer = handler.chat_main(question)

    return jsonify({"result": answer})


if __name__ == "__main__":
    # 创建 ChatBotGraph 实例并启动 Flask
    app.run(host="0.0.0.0", port=5003, debug=True)
