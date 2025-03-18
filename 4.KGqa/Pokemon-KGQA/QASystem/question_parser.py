# coding: utf-8


class QuestionPaser:
    """
    res_classify = {'args': {'person': '小智'}, 'question_types': ['查询人物拥有哪些宝可梦']}
    """

    def parser_main(self, res_classify):
        args = res_classify["args"]
        question_types = res_classify["question_types"] 

        if(len(question_types) > 1):
            return "请勿一次性输入多个问题！"
        if(len(question_types) == 0 or question_types[0] == '未匹配'):
            return "未匹配！"
        
        question_type = question_types[0]
        return self.sql_transfer(question_type, args)


    def sql_transfer(self, question_type, entities):
        """
        针对不同的问题，分开进行处理 开始具体的模式匹配
        """
        if not entities:
            return []

        pokemon = entities.get('Pokémon','')
        person = entities.get('person','')
        town = entities.get('Town','')
        region = entities.get('Region','')
        identity = entities.get('identity','')
        
         # 初始化查询语句
        sql = ""

        # 根据问题类型生成查询
        if question_type == "查询宝可梦中文名":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.name AS chinese_name;"

        elif question_type == "查询宝可梦英文名":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.english_name AS english_name;"

        elif question_type == "查询宝可梦特性":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.ability AS ability;"

        elif question_type == "查询宝可梦隐藏特性":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.hidden_ability AS hidden_ability;"

        elif question_type == "查询宝可梦身高":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.height AS height;"

        elif question_type == "查询宝可梦体重":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.weight AS weight;"

        elif question_type == "查询宝可梦进化等级":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.evolution_level AS evolution_level;"

        elif question_type == "查询宝可梦属性抗性":
            sql = f"MATCH (p:Pokémon) WHERE p.name = '{pokemon}' RETURN p.attr_ability AS attr_ability;"

        elif question_type == "查询宝可梦进化形态":
            sql = f"MATCH (p1:Pokémon)-[:evolves_into]->(p2:Pokémon) WHERE p1.name = '{pokemon}' RETURN p2.name AS evolution_name;"

        elif question_type == "查询宝可梦属性":
            sql = f"MATCH (p:Pokémon)-[:has_type]->(i:identity) WHERE p.name = '{pokemon}' RETURN i.name AS identity_name;"

        elif question_type == "查询人物性别":
            sql = f"MATCH (per:Person) WHERE per.name = '{person}' RETURN per.gender AS gender;"

        elif question_type == "查询人物英文名":
            sql = f"MATCH (per:Person) WHERE per.name = '{person}' RETURN per.english_name AS english_name;"

        elif question_type == "查询人物日本名":
            sql = f"MATCH (per:Person) WHERE per.name = '{person}' RETURN per.japanese_name AS japanese_name;"

        elif question_type == "查询人物的挑战者":
            sql = f"MATCH (per1:Person)-[:challenge]->(per2:Person) WHERE per1.name = '{person}' RETURN per2.name AS challenger_name;"

        elif question_type == "查询人物的伙伴":
            sql = f"MATCH (per1:Person)-[:partner]->(per2:Person) WHERE per1.name = '{person}' RETURN per2.name AS partner_name;"

        elif question_type == "查询人物的敌对者":
            sql = f"MATCH (per1:Person)-[:hostility]->(per2:Person) WHERE per1.name = '{person}' RETURN per2.name AS hostility_name;"

        elif question_type == "查询人物的亲戚":
            sql = f"MATCH (per1:Person)-[:relative]->(per2:Person) WHERE per1.name = '{person}' RETURN per2.name AS relative_name;"

        elif question_type == "查询某个属性的宝可梦有哪些":
            sql = f"MATCH (p:Pokémon)-[:has_type]->(i:identity) WHERE i.name = '{identity}' RETURN p.name AS pokemon_name;"

        elif question_type == "查询城镇位于的地区":
            sql = f"MATCH (t:Town)-[:located_in]->(r:Region) WHERE t.name = '{town}' RETURN r.name AS region_name;"

        elif question_type == "查询地区的城镇有哪些":
            sql = f"MATCH (r:Region)<-[:located_in]-(t:Town) WHERE r.name = '{region}' RETURN t.name AS town_name;"

        elif question_type == "查询人物来自哪个地区":
            sql = f"MATCH (per:Person)-[:come_from]->(r:Region) WHERE per.name = '{person}' RETURN r.name AS region_name;"

        elif question_type == "查询地区有哪些人物":
            sql = f"MATCH (per:Person)-[:come_from]->(r:Region) WHERE r.name = '{region}' RETURN per.name AS person_name;"

        elif question_type == "查询人物拥有哪些宝可梦":
            sql = f"MATCH (per:Person)-[:has_pokemon]->(p:Pokémon) WHERE per.name = '{person}' RETURN p.name AS pokemon_name;"

        elif question_type == "查询拥有某个宝可梦的人物有哪些":
            sql = f"MATCH (per:Person)-[:has_pokemon]->(p:Pokémon) WHERE p.name = '{pokemon}' RETURN per.name AS person_name;"

        elif question_type == "查询城镇有哪些宝可梦":
            sql = f"MATCH (t:Town)-[:location_pokemon]->(p:Pokémon) WHERE t.name = '{town}' RETURN p.name AS pokemon_name;"

        elif question_type == "查询哪些城镇有某个宝可梦":
            sql = f"MATCH (t:Town)-[:location_pokemon]->(p:Pokémon) WHERE p.name = '{pokemon}' RETURN t.name AS town_name;"

        elif question_type == "查询城镇有哪些人物":
            sql = f"MATCH (t:Town)-[:has_celebrity]->(per:Person) WHERE t.name = '{town}' RETURN per.name AS person_name;"

        elif question_type == "查询人物来自哪个城镇":
            sql = f"MATCH (per:Person)-[:come_from]->(t:Town) WHERE per.name = '{person}' RETURN t.name AS town_name;"

        elif question_type == "查询某个地区有多少城镇":
            sql = f"MATCH (r:Region)<-[:located_in]-(t:Town) WHERE r.name = '{region}' RETURN COUNT(t) AS town_count;"

        elif question_type == "查询某个城镇有多少宝可梦":
            sql = f"MATCH (t:Town)-[:location_pokemon]->(p:Pokémon) WHERE t.name = '{town}' RETURN COUNT(p) AS pokemon_count;"

        elif question_type == "查询人物拥有多少宝可梦":
            sql = f"MATCH (per:Person)-[:has_pokemon]->(p:Pokémon) WHERE per.name = '{person}' RETURN COUNT(p) AS pokemon_count;"

        elif question_type == "查询宝可梦有多少种属性":
            sql = f"MATCH (p:Pokémon)-[:has_type]->(i:identity) WHERE p.name = '{pokemon}' RETURN COUNT(i) AS identity_count;"

        else:
            sql = "未匹配！"

        print(sql)
        return sql

if __name__ == "__main__":
    handler = QuestionPaser()

    # 模拟一个res_classify字典作为输入
    res_classify = {'args': {'person': '小智'}, 'question_types': ['查询人物拥有哪些宝可梦']}

    sql = handler.parser_main(res_classify)
    print("Generated SQL:", sql)
