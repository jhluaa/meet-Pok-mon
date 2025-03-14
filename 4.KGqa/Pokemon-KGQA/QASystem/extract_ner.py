import os
import pickle
import torch
from torch import nn
from transformers import BertModel, BertTokenizer
import ahocorasick
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



#全局标识，确保模型只加载一次
model_loaded = False

##########################################
# 1. 定义必要的类与函数
##########################################
class Bert_Model(nn.Module):
    """
    简化的BERT+ 双向RNN+Linear的实体识别模型
    """
    def __init__(self, model_name, hidden_size, tag_num, bi=True):
        super().__init__()
        # 载入预训练的BERT
        self.bert = BertModel.from_pretrained(model_name)
        # 使用双向RNN也可换为 GRU/LSTM 等）
        self.gru = nn.RNN(input_size=768, hidden_size=hidden_size,
                          num_layers=2, batch_first=True, bidirectional=bi)
        # 如果是双向，则输出维度是hidden_size * 2
        out_size = hidden_size * 2 if bi else hidden_size
        self.classifier = nn.Linear(out_size, tag_num)

        # 忽略掉index=0（一般是 <PAD>）
        self.loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    def forward(self, x, label=None):
        """
        x: [batch_size, seq_len]
        label: [batch_size, seq_len]，可选
        """
        # BERT 编码
        bert_out, _ = self.bert(x, attention_mask=(x > 0), return_dict=False)
        # RNN 编码
        rnn_out, _ = self.gru(bert_out)
        # 分类器输出
        logits = self.classifier(rnn_out)  # [batch_size, seq_len, tag_num]

        if label is not None:
            # 计算损失
            loss = self.loss_fn(
                logits.reshape(-1, logits.shape[-1]),
                label.reshape(-1)
            )
            return loss
        else:
            # 推断时，返回每个token的最大概率标签索引
            # [batch_size, seq_len]
            return torch.argmax(logits, dim=-1)


class rule_find:
    """
    使用 Aho-Corasick 自动机进行规则匹配的类
    可在 data/ent 目录下放若干 .txt 文件，每个文件对应一种实体类型。
    """
    def __init__(self):
        # 你可以根据实际实体类型进行调整
        self.idx2type = idx2type = ["identity", "person", "Pokémon", "Region", "Town"]
        self.type2idx = type2idx = {"identity": 0, "person": 1, "Pokémon": 2, "Region": 3, "Town": 4}
        # 建立实体类型到索引的映射
        self.type2idx = {
            t: i for i, t in enumerate(self.idx2type)
        }
        # 为每个实体类型构建一个 Aho-Corasick Automaton
        self.ahos = [ahocorasick.Automaton() for _ in range(len(self.type2idx))]

        # 假设 data/ent/Affair.txt, data/ent/Area.txt 等文件中每行一个实体
        ent_dir = "/data/KGqa/Pokemon-KGQA/entity_data"
        for t in self.idx2type:
            txt_path = os.path.join(ent_dir, f"{t}.txt")
            if not os.path.exists(txt_path):
                continue
            with open(txt_path, "r", encoding="utf-8") as f:
                all_en = f.read().split("\n")
            # 加入AC自动机
            for en in all_en:
                en = en.split(' ')[0]  # 如果一行有多列，取第1列
                if len(en) >= 2:      # 自定义最小匹配长度
                    self.ahos[self.type2idx[t]].add_word(en, en)

        # 构建AC自动机
        for aho in self.ahos:
            aho.make_automaton()

    def find(self, sentence):
        """
        在给定句子中进行规则匹配。
        返回: [(start, end, type, matched_str), ...]
        """
        rule_result = []
        used_positions = {}
        temp_matches = []
        match_types = []

        # 对每个实体类型对应的 AC 自动机逐个匹配
        for i, aho in enumerate(self.ahos):
            matches = list(aho.iter(sentence))
            temp_matches.extend(matches)
            for _ in range(len(matches)):
                match_types.append(self.idx2type[i])

        # 如果匹配结果不为空，则按实体长度从大到小排序
        if len(temp_matches) > 0:
            # temp_matches 中每个元素形如 (end_index, matched_str)
            # end_index 是字符串下标
            # matched_str 是匹配到的实体
            # 按长度逆序排列
            sorted_matches = sorted(
                zip(temp_matches, match_types),
                key=lambda x: len(x[0][1]),
                reverse=True
            )
            for (match, ent_type) in sorted_matches:
                end_index = match[0]
                matched_str = match[1]
                start_index = end_index - len(matched_str) + 1
                # 检查是否有重叠
                if any(pos in used_positions for pos in range(start_index, end_index+1)):
                    continue
                # 记录
                rule_result.append((start_index, end_index, ent_type, matched_str))
                for pos in range(start_index, end_index+1):
                    used_positions[pos] = True

        return rule_result


class tfidf_alignment:
    def __init__(self):
        eneities_path = os.path.join(base_dir, 'entity_data/')
        files = os.listdir(eneities_path)
        # 排除 .py 文件
        files = [docu for docu in files if '.py' not in docu]
        self.tag_2_embs = {}
        self.tag_2_tfidf_model = {}
        self.tag_2_entity = {}
        for ty in files:
            with open(os.path.join(eneities_path, ty), 'r', encoding='utf-8') as f:
                entities = f.read().split('\n')
                # 过滤长度过长或过短的实体
                entities = [
                    ent for ent in entities
                    if 1 <= len(ent.split(' ')[0]) <= 15
                ]
                # 只取每行的第一个词
                en_name = [ent.split(' ')[0] for ent in entities]
                # 去掉文件名后缀 .txt
                ty = ty.strip('.txt')
                # 记录实体列表
                self.tag_2_entity[ty] = en_name
                # 初始化 TF-IDF，
                tfidf_model = TfidfVectorizer(analyzer="char")
                embs = tfidf_model.fit_transform(en_name)  # 稀疏矩阵
                self.tag_2_tfidf_model[ty] = tfidf_model
                self.tag_2_embs[ty] = embs  # 保持稀疏格式
    def align(self, ent_list):
        """
        ent_list 为 [(start_idx, end_idx, cls, ent), ...]
        返回一个 dict：{cls: best_matched_entity_name}
        """
        new_result = {}
        for s, e, cls, ent in ent_list:
            #若该类型不在词典中，则跳过
            if cls not in self.tag_2_tfidf_model:
                continue

            # 对当前实体做TF-IDF编码
            ent_emb = self.tag_2_tfidf_model[cls].transform([ent])  # 稀疏矩阵
            # 和已知实体向量self.tag_2_embs[cls]做相似度
            sim_score = cosine_similarity(ent_emb, self.tag_2_embs[cls])
            max_idx = sim_score[0].argmax()
            max_score = sim_score[0, max_idx]

            # 如果相似度大于阈值0.5，就认为匹配
            if max_score >= 0.5:
                new_result[cls] = self.tag_2_entity[cls][max_idx]

        return new_result


def find_entities(tag_seq):
    """
    根据序列标注（如 ['O','B-LOC','I-LOC','O',...]）提取实体区间。
    返回: [(start_idx, end_idx, type), ...]
    """
    res = []
    i = 0
    while i < len(tag_seq):
        if tag_seq[i].startswith("B-"):
            ent_type = tag_seq[i][2:]  # 去掉"B-"
            start = i
            i += 1
            #连续的I-与之前同一个类型
            while i < len(tag_seq) and tag_seq[i].startswith("I-"):
                i += 1
            end = i - 1
            res.append((start, end, ent_type))
        else:
            i += 1
    return res


def merge(model_result_word, rule_result):
    """
    将模型识别的实体和规则识别的实体合并，按实体长度逆序去重
    model_result_word: [(start, end, type, text), ...]
    """
    merged_list = model_result_word + rule_result
    # 根据实体文本长度降序排序
    merged_list.sort(key=lambda x: len(x[-1]), reverse=True)

    final_result = []
    used = set()
    for (st, ed, tp, txt) in merged_list:
        # 如果区间有重叠，则跳过
        if any(pos in used for pos in range(st, ed+1)):
            continue
        final_result.append((st, ed, tp, txt))
        for pos in range(st, ed+1):
            used.add(pos)
    return final_result


def get_ner_result(sentence, rule, tfidf_r):
    """
    使用Roberta +规则匹配+TF-IDF对齐来获取最终的实体识别结果。
    返回一个字典: {实体类型: 对齐后的实体文本, ...}
    """
    # 1)将输入句子编码
    sen_tensor = bert_tokenizer.encode(sentence, add_special_tokens=True, return_tensors='pt').to(device)
    # 2)模型预测
    # logits取 argmax -> shape: [batch_size, seq_len]
    pred_ids = bert_model(sen_tensor).tolist()[0]

    # 3)映射到标签名
    # 注意去掉[CLS]和[SEP] 索引位置：pred_ids[1:-1]
    pred_tags = [idx2tag[t] for t in pred_ids[1:-1]]

    # 4)找出模型结果的实体区间
    model_spans = find_entities(pred_tags)  # [(start, end, type), ...]
    model_result_word = []
    for (start, end, ent_type) in model_spans:
        text_span = sentence[start : end+1]  # 根据字符索引提取
        model_result_word.append((start, end, ent_type, text_span))

    # 5)规则匹配
    rule_result = rule.find(sentence)  # 同样返回 [(start, end, type, text), ...]

    # 6)合并两部分实体识别结果
    merged_result = merge(model_result_word, rule_result)

    # 7)TF-IDF对齐
    final_aligned = tfidf_r.align(merged_result)

    return final_aligned


##########################################
# 2. 加载模型并提供交互
##########################################

def load_model():
    """
    全局加载一次模型，避免重复加载。
    """
    global model_loaded, device
    global bert_tokenizer, bert_model, idx2tag

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # 1)读取标签映射
    with open("/data/KGqa/Pokemon-KGQA/NER/tag2idx.npy", "rb") as f:
        tag2idx = pickle.load(f)
    idx2tag = list(tag2idx.keys())  # 或者 list(tag2idx)，取决于之前如何构建

    # 2)载入BERTTokenizer
    model_name = "/data/KGqa/Pokemon-KGQA/NER/chinese-roberta-wwm-ext"
    bert_tokenizer = BertTokenizer.from_pretrained(model_name)

    # 3)创建模型
    bert_model = Bert_Model(
        model_name=model_name,
        hidden_size=128,
        tag_num=len(tag2idx),
        bi=True
    )
    # 4)加载模型权重
    ckpt_path = "/data/KGqa/Pokemon-KGQA/NER/best_roberta.pt"
    bert_model.load_state_dict(torch.load(ckpt_path, map_location=device))

    bert_model.to(device)
    bert_model.eval()

    model_loaded = True


def ensure_model_loaded():
    """
    仅在需要时加载模型
    """
    global model_loaded
    if not model_loaded:
        load_model()
        model_loaded = True


##########################################
# 3. 主程序入口
##########################################
ensure_model_loaded()

if __name__ == "__main__":
    rule = rule_find()
    tfidf_r = tfidf_alignment()
    while True:
        sentence = input("请输入要识别的文本(输入 'exit' 退出)：\n> ")
        if sentence.lower() == "exit":
            break

        # 调用get_ner_result获取最终实体对齐结果
        final_entities = get_ner_result(
            sentence=sentence,
            rule=rule,
            tfidf_r=tfidf_r

        )
        # final_entities 是一个字典，形如：{"Business": "xx公司", "Dept": "xx部门"}
        print("实体识别对齐结果:", final_entities)
