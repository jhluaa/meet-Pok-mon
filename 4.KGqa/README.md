## 知识图谱构建及问答

1. 参考 https://github.com/liuhuanyong/QASystemOnMedicalKG  构建图谱neo4j 具体是build_medicalgraph 以及build_medicalgraph_from_json.py 写成我们自己的
2. 参考 Data Processing 文件夹下函数，改成我们自己的，然后替换生成不同实体类型的txt文件 比如宝可梦， 人物等
3. 参考QAsystem 文件夹下 函数构建查询cypher语句。使用api.py函数接入dify工作流。