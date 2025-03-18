# coding: utf-8

from py2neo import Graph
import json

class AnswerSearcher:
    def __init__(self):
        self.g = Graph("bolt://localhost:7687", auth=("neo4j", "woshishamo630"))

    def search_main(self, sql):
        '''
        执行cypher查询，并返回相应结果
        '''
        final_answers = []
        if sql == "未匹配！" or sql == "请勿一次性输入多个问题！":
            final_answers.append(sql)
            return final_answers
        
        
        answers = []
        ress = self.g.run(sql).data()

        if not ress:
            final_answers.append("未匹配！")
            return final_answers
        answers += ress
        

        # 去重：将字典转换为字符串再去重，最后再转换回字典列表
        unique_answers = list({json.dumps(answer, ensure_ascii=False) for answer in answers})
        unique_answers = [json.loads(answer) for answer in unique_answers]  # 转回字典列表

        if unique_answers:
            final_answers.append(str(unique_answers))

        return final_answers
