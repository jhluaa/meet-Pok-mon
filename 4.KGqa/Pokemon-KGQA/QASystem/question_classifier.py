# coding: utf-8

import os
import ahocorasick

class QuestionClassifier:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        # 特征词路径
        self.identity_path = os.path.join(cur_dir, '../entity_data/identity.txt') # 宝可梦特性
        self.person_path = os.path.join(cur_dir, '../entity_data/person.txt') # 召唤师
        self.pokemon_path = os.path.join(cur_dir, '../entity_data/Pokémon.txt') # 宝可梦
        self.Region_path = os.path.join(cur_dir, '../entity_data/Region.txt') #地区
        self.Town_path = os.path.join(cur_dir, '../entity_data/Town.txt') # 镇
        # 停用词
        self.deny_path = os.path.join(cur_dir, '../raw_data/deny.txt')

        # 加载特征词
        self.identity_wds = [i.strip() for i in open(self.identity_path, 'r', encoding='utf-8') if i.strip()]
        self.person_wds = [i.strip() for i in open(self.person_path, 'r', encoding='utf-8') if i.strip()]
        self.Pokemon_wds = [i.strip() for i in open(self.pokemon_path, 'r', encoding='utf-8') if i.strip()]
        self.Region_wds = [i.strip() for i in open(self.Region_path, 'r', encoding='utf-8') if i.strip()]
        self.Town_wds = [i.strip() for i in open(self.Town_path, 'r', encoding='utf-8') if i.strip()]

        self.region_words = set(self.identity_wds + self.person_wds + self.Pokemon_wds +
                                self.Region_wds+self.Town_wds)
        self.deny_words = [i.strip() for i in open(self.deny_path, 'r', encoding='utf-8') if i.strip()]

        # 构造领域actree
        self.region_tree = self.build_actree(list(self.region_words))
        # 构建词典
        self.wdtype_dict = self.build_wdtype_dict()
        # 问句疑问词
        self.pokemon_qwds = [
            "有哪些宝可梦", "宝可梦","口袋","口袋妖怪","神奇宝贝","宠物","哪些"
        ]
        self.person_qwds = ["人物介绍", "中文名", "日文名", "英文名", "性别","人物关系","人"]
        self.region_qwds = ["地区", "区域", "地方", "地图位置", "镇","位置", "所属地区","抓","捕捉","哪里"]
        self.town_qwds = ["镇子", "小镇", "乡村", "城市", "村庄","哪里人","来自","家乡","地方","地点","抓","捕捉","哪里"]
        self.partner_qwds=["同伴","同学","伙伴","朋友"]
        self.hostility_qwds=["敌对","敌人","敌","交恶","对手"]
        self.relative_qwds=["亲戚","家人"]
        self.evolves_qwds=["进化","升级","进化等级",]
        self.qtype_qwds=["类型","特性", "能力"]
        self.celebrity_qwds=["名人","召唤师"]
        self.saas_qwds=["位于"]
        self.gen_qwds=["性别","男","女"]

        print('model init finished ......')

        return

    def classify(self, question):
        '''
        分类主函数
        '''
        data = {}
        pokemon_dict = self.check_pokemon(question) # 拿到实体

        if not pokemon_dict:
            return {}
        data['args'] = pokemon_dict
        # 收集问句当中所涉及到的实体类型
        types = []
        for type_ in pokemon_dict.values():
            types += type_

        question_type = ''
        question_types = []
        #print(types) ['identity']
        # 宝可梦特性

        #召唤师
        if self.check_words(self.person_wds, question) and ('Person' in types):
            if self.check_words(["英文"], question):
                question_type = 'person_en_name'
                question_types.append(question_type)
            elif self.check_words(["日本","日文"], question):
                question_type = 'person_jp_name'
                question_types.append(question_type)
            elif self.check_words(["中文","中国","名字"],question):
                question_type = 'person_en_name'
                question_types.append(question_type)
            elif self.check_words(self.gen_qwds,question_type):
                question_type = 'person_gen'
                question_types.append(question_type)
            else:
                question_type = 'person_info'
                question_types.append(question_type)


        # 宝可梦
        if self.check_words(self.Pokemon_wds, question) and ('Pokémon' in types):
            if self.check_words(["英文"], question):
                question_type = 'Pokemon_en_name'
                question_types.append(question_type)
            elif self.check_words(["日本","日文"], question):
                question_type = 'Pokemon_jp_name'
                question_types.append(question_type)
            elif self.check_words(["中文","中国","名字"],question):
                question_type = 'Pokemon_en_name'
                question_types.append(question_type)
            elif self.check_words(["特性","特点","长处"],question_type):
                question_type = 'Pokemon_ability'
                question_types.append(question_type)
            elif self.check_words(["身高"], question_type):
                question_type = 'Pokemon_height'
                question_types.append(question_type)
            elif self.check_words(["体重"], question_type):
                question_type = 'Pokemon_weight'
                question_types.append(question_type)
            elif self.check_words(["等级","级别","进化"], question_type):
                question_type = 'Pokemon_evolution'
                question_types.append(question_type)
            else:
                question_type = 'Pokemon_info'
                question_types.append(question_type)

   # 先拿到 具体的 实体

        # 问句中有召唤师  赤红有哪些同伴
        if self.check_words(self.partner_qwds, question) and 'Person' in types:
            question_type = 'person_partner'
            question_types.append(question_type)
        # 问句中有召唤师  赤红有敌对对手
        if self.check_words(self.hostility_qwds, question) and 'Person' in types:
            question_type = 'person_hostility'
            question_types.append(question_type)
            # 问句中有召唤师  赤红有亲戚
        if self.check_words(self.relative_qwds, question) and 'Person' in types:
            question_type = 'person_relative'
            question_types.append(question_type)

        #问句中召唤师有哪些宝可梦
        if self.check_words(self.pokemon_qwds, question) and 'Person' in types:
            question_type = 'person_pokemon'
            question_types.append(question_type)


            # 问句中召唤师来自哪里
        # if self.check_words(self.town_qwds, question) and 'Person' in types:
        #     question_type = 'person_town'
        #     question_types.append(question_type)
            # 问句中召唤师 地方
        if self.check_words(self.region_qwds, question) and 'Person' in types:
            question_type = 'person_region'
            question_types.append(question_type)
        # 问 宝可梦进化
        if self.check_words(self.evolves_qwds, question)  and 'Pokémon' in types :
            question_type = 'Pokemon_evolves'
            question_types.append(question_type)
        #问宝可梦类型
        if self.check_words(self.qtype_qwds, question) and 'Pokémon' in types:
            question_type = 'Pokemon_qtype'
            question_types.append(question_type)

        if self.check_words(self.region_qwds, question) and 'Pokémon' in types:
            question_type = 'Pokemon_Region'
            question_types.append(question_type)

        if self.check_words(self.person_qwds, question) and 'Pokémon' in types:
            question_type = 'pokemon_person'
            question_types.append(question_type)

        # 已知特性查宝可梦
        if self.check_words(self.pokemon_qwds, question) and 'identity' in types:
            question_type = 'identity_pokemon'
            question_types.append(question_type)

            # 小镇有哪些名人
        if self.check_words(self.celebrity_qwds, question) and 'Town' in types:
            question_type = 'Town_celebrity'
            question_types.append(question_type)
        # 地区有哪些宝可梦
        if self.check_words(self.pokemon_qwds, question) and 'Region' in types:
            question_type = 'Region_pokemon'
            question_types.append(question_type)
         # 在哪里
        if self.check_words(self.saas_qwds, question) and 'Town' in types:
            question_type = 'Town_Region'
            question_types.append(question_type)
        # 若没有查到相关的外部查询信息，那么则将人物的描述信息返回
        if question_types == [] and 'Person' in types:
            question_types = ['person_info']

        # 若没有查到相关的外部查询信息，那么则将该宝可梦的描述信息返回
        if question_types == [] and 'Pokémon' in types:
            question_types = ['Pokemon_info']

        # 将多个分类结果进行合并处理，组装成一个字典
        data['question_types'] = question_types
        return data

    def build_wdtype_dict(self):
        '''
        构造词对应的类型
        '''
        wd_dict = dict()
        for wd in self.region_words:
            wd_dict[wd] = []
            if wd in self.identity_wds:
                wd_dict[wd].append('identity')
            if wd in self.person_wds:
                wd_dict[wd].append('Person')
            if wd in self.Pokemon_wds:
                wd_dict[wd].append('Pokémon')
            if wd in self.Region_wds:
                wd_dict[wd].append('Region')
            if wd in self.Town_wds:
                wd_dict[wd].append('Town')
        return wd_dict


    def build_actree(self, wordlist):
        '''
        构造actree，加速过滤
        '''
        actree = ahocorasick.Automaton()
        for index, word in enumerate(wordlist):
            actree.add_word(word, (index, word))
        actree.make_automaton()
        return actree

#实体抽取以及类型分类
    def check_pokemon(self, question):
        '''问句过滤'''
        region_wds = [] #用于存储在后续过程中提取的所有相关词汇。
        for i in self.region_tree.iter(question):
            wd = i[1][1]
            region_wds.append(wd)
        stop_wds = []
        for wd1 in region_wds:
            for wd2 in region_wds:
                if wd1 in wd2 and wd1 != wd2:
                    stop_wds.append(wd1)
        final_wds = [i for i in region_wds if i not in stop_wds]
        final_dict = {i: self.wdtype_dict.get(i) for i in final_wds}

        return final_dict # findal_dict是一个字典，键是实体，值是实体对应的类型


    def check_words(self, wds, sent):
        '''
        基于特征词进行分类
        '''
        for wd in wds:
            if wd in sent:
                return True
        return False

if __name__ == '__main__':
    handler = QuestionClassifier()
    # while 1:
    for i in range(1):
        question = input('input an question:')
        data = handler.classify(question)
        print(data)

# input an question:怎么才能治疗腹泻
# {'args': {'腹泻': ['symptom']}, 'question_types': ['symptom_disease']}