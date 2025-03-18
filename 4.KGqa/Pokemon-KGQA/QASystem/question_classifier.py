# coding: utf-8
import os
import sys
import Intent_Recognition

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
    
from NER.ner_model import *

base_dir = r"F:\bigmodel\meet-Pok-mon\4.KGqa\Pokemon-KGQA"
model_base_path = "F:/bigmodel/models/"  # 模型和权重的基础路径
model_name = os.path.join(model_base_path, "chinese-roberta-wwm-ext")
pt_path = os.path.join(model_name, "best_roberta.pt")

class QuestionClassifier:
    def __init__(self):
        # 初始化规则和 TF-IDF 对齐
        self.rule = rule_find()
        self.tfidf_r = tfidf_alignment()

        # 加载 tag2idx
        if os.path.exists('tag2idx.npy'):
            with open('tag2idx.npy', 'rb') as f:
                self.tag2idx = pickle.load(f)
                self.idx2tag = list(self.tag2idx)
        else:
            raise FileNotFoundError("tag2idx文件不存在！")

        # 初始化设备
        self.device = torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')

        # 加载 tokenizer
        self.tokenizer = BertTokenizer.from_pretrained(model_name, cache_dir=model_base_path)

        # 初始化模型
        hidden_size = 128
        bi = True
        self.model = Bert_Model(model_name, hidden_size, len(self.tag2idx), bi)

        # 加载模型权重
        if os.path.exists(pt_path):
            print("加载已有模型")
            self.model.load_state_dict(torch.load(pt_path, map_location=self.device))
        else:
            raise FileNotFoundError("未找到模型权重文件!!")

        # 将模型移动到设备
        self.model = self.model.to(self.device)

        print('模型初始化完成 ......')

    def ner(self, question):
        # 调用 NER 方法
        return get_ner_result(self.model, self.tokenizer, question, self.rule, self.tfidf_r, self.device, self.idx2tag)
    
    def classify(self, question):
        '''
        分类主函数
        '''
        data = {}
            
        entity_dict = self.ner(question)

        if not entity_dict:
            return {}
        data['args'] = entity_dict
        
        question_list = Intent_Recognition.Intent_Recognition(question)
        data['question_types'] = question_list
        
        print(data)
        
        return data
       
if __name__ == '__main__':
    handler = QuestionClassifier()
    # while 1:
    for i in range(1):
        question = input('input an question:')
        data = handler.classify(question)
        print(data)
 

#{'args': {'person': '小智'}, 'question_types': ['查询人物拥有哪些宝可梦']}