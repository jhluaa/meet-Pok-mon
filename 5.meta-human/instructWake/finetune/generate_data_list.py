import json
import os


def generate_data_list(data_dir, data_list_path):
    with open(os.path.join(data_dir, 'text'), 'r', encoding='utf-8') as f:
        text_lines = f.readlines()
    with open(os.path.join(data_dir, 'wav.scp'), 'r', encoding='utf-8') as f:
        scp_lines = f.readlines()
    assert len(text_lines) == len(scp_lines), 'text and wav.scp should have same length'
    with open(data_list_path, 'w', encoding='utf-8') as f:
        for i in range(len(text_lines)):
            text = text_lines[i].strip().split(' ')[1:]
            text = ''.join(text)
            scp = scp_lines[i].strip()
            scp_split = scp.split(' ')
            utt_id = scp_split[0]
            wav_path = scp_split[1]
            f.write(json.dumps({'key': utt_id, 'source': wav_path, 'source_len': len(wav_path),
                                'target': text, 'target_len': len(text)}, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    generate_data_list('dataset/train/', 'dataset/train.jsonl')
    generate_data_list('dataset/validation/', 'dataset/validation.jsonl')