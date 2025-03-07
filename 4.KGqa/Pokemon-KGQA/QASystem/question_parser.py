# coding: utf-8


class QuestionPaser:
    """
    构建实体节点
    """

    def build_entitydict(self, args):
        entity_dict = {}
        for arg, types in args.items():
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)
        return entity_dict

    def parser_main(self, res_classify):
        args = res_classify["args"]
        entity_dict = self.build_entitydict(args)

        # 打印实体字典，确认构建是否正确
        # print("Entity Dictionary:", entity_dict)  #Entity Dictionary: {'person': ['赤红']}
        # exit()
        question_types = res_classify["question_types"] #['person_ino', 'person_pokemon']

        sqls = []
        for question_type in question_types:
            sql_ = {}
            sql_["question_type"] = question_type
            sql = []
            # 根据问题类型选择相应的实体类型

            if question_type == "person_info":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_en_name":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_jp_name":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_gen":
                sql = self.sql_transfer(question_type, entity_dict)

            elif question_type == "Pokemon_info":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_en_name":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_jp_name":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_ability":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_height":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_weight":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_evolution":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type=="pokemon_person":
                sql=self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_partner":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_hostility":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_relative":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_pokemon":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_town":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_region":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_evolves":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_qtype":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokemon_Region":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "identity_pokemon":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Town_celebrity":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Region_pokemon":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Town_Region":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "person_attr":
                sql = self.sql_transfer(question_type, entity_dict)
            elif question_type == "Pokémon_attr":
                sql = self.sql_transfer(question_type, entity_dict)
            # 打印查询语句，确认sql是否正确构建
            # print(f"SQL for {question_type}:", sql)

            if sql:
                sql_["sql"] = sql
                sqls.append(sql_)

        return sqls

    def sql_transfer(self, question_type, entities):
        """
        针对不同的问题，分开进行处理 开始具体的模式匹配
        """
        if not entities:
            return []

        keys = list(entities.keys())[0]  # 获取实体类型
        entities = entities[keys]  # 获取具体实体名称列表
        sql = []

        if keys == "Person":
            if question_type == "person_info":
                sql = [
                    "MATCH (a:Person) WHERE a.name='{0}' RETURN  a.japanese_name, a.english_name, a.gender".format(
                        i)
                    for i in entities
                ]
            elif question_type == "person_en_name":
                sql = [
                    "MATCH (a:Person) WHERE a.name='{0}' RETURN a.english_name".format(i)
                    for i in entities
                ]
            elif question_type == "person_jp_name":
                sql = [
                    "MATCH (a:Person) WHERE a.name='{0}' RETURN a.japanese_name".format(i)
                    for i in entities
                ]
            elif question_type == "person_gen":
                sql = [
                    "MATCH (a:Person) WHERE a.name='{0}' RETURN a.gender".format(i)
                    for i in entities
                ]
            elif question_type == "person_partner":
                sql = [
                    "MATCH (a:Person)-[:partner]-(b:Person) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            elif question_type == "person_hostility":
                sql = [
                    "MATCH (a:Person)-[:hostility]-(b:Person) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            elif question_type == "person_relative":
                sql = [
                    "MATCH (a:Person)-[:relative]-(b:Person) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            elif question_type == "person_pokemon":
                sql = [
                    "MATCH (a:Person)-[:has_pokemon]-(b:Pokémon) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            # elif question_type == "person_town":
            #     sql = [
            #         "MATCH (a:Person)-[:come_from]-(b:Town) WHERE a.name='{0}' RETURN b.name".format(i)
            #         for i in entities
            #     ]
            elif question_type == "person_region":
                sql = [
                    "MATCH (a:Person)-[:come_from]-(b:Region) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]

        elif keys == "Pokémon":
            if question_type == "Pokemon_info":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_en_name":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.english_name".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_jp_name":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.japanese_name".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_ability":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.ability,a.hidden_ability,a.attr_ability".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_height":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.height".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_weight":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.weight".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_evolution":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.name='{0}' RETURN a.evolution_level".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_qtype":
                sql = [
                    "MATCH (a:Pokémon)-[:has_type]-(b:Type) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            elif question_type == "Pokemon_evolves":
                sql = [
                    "MATCH (a:Pokémon)-[:evolves_into]-(b:Pokémon) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]

            elif question_type == "Pokemon_Region":
                sql = [
                    "MATCH (a:Pokémon)-[:location_pokemon]-(b:Region) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]

        elif keys == "identity":
            if question_type == "identity_pokemon":
                sql = [
                    "MATCH (a:Pokémon) WHERE a.ability='{0}' RETURN a.name".format(i)
                    for i in entities
                ]

        elif keys == "Town":
            if question_type == "Town_celebrity":
                sql = [
                    "MATCH (a:Town)-[:has_celebrity]-(b:Person) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]
            elif question_type == "Town_Region":
                sql = [
                    "MATCH (a:Town)-[:located_in]-(b:Region) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]

        elif keys == "Region":
            if question_type == "Region_pokemon":
                sql = [
                    "MATCH (a:Region)-[:location_pokemon]-(b:Pokémon) WHERE a.name='{0}' RETURN b.name".format(i)
                    for i in entities
                ]

        return sql


if __name__ == "__main__":
    handler = QuestionPaser()

    # 模拟一个res_classify字典作为输入
    res_classify = {
        # 'args': {'赤红': ['Person']}, 'question_types': ['person_info', 'person_partner']
        # 'args': {'皮卡丘': ['Pokemon']}, 'question_types': ['Pokemon_info']
        'args': {'皮卡丘': ['Pokémon']}, 'question_types': ['Pokemon_info', 'Pokemon_evolves']
    }

    sqls = handler.parser_main(res_classify)
    print("Generated SQLs:", sqls)
