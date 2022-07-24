import numpy as np
import cv2

import torch
import torch.nn.functional as F

from ai.model.mobilenetv3 import MobileNetV3
from ai.model.pix2pix import Generator


class Inference:
    def __init__(self, c_weight=None, g_weight=None, num_classes=28):

        if c_weight is not None:
            self.classification_model = MobileNetV3(num_classes=num_classes).cpu()
            self.classification_model.load_state_dict(torch.load(c_weight, map_location=torch.device('cpu')))
            self.classification_model.eval()

        if g_weight is not None:
            self.generation_model = Generator().cpu()
            self.generation_model.load_state_dict(torch.load(g_weight, map_location=torch.device('cpu')))
            self.generation_model.eval()

        self.classes = {
            0: '얼레지',
            1: '노루귀',
            2: '애기똥풀',
            3: '제비꽃',
            4: '민들레',
            5: '할미꽃',
            6: '은방울꽃',
            7: '비비추',
            8: '패랭이꽃',
            9: '수련',
            10: '맥문동',
            11: '엉겅퀴',
            12: '참나리',
            13: '초롱꽃',
            14: '상사화',
            15: '동백',
            16: '개망초',
            17: '장미',
            18: '해바라기',
            19: '무궁화',
            20: '진달래',
            21: '개나리',
            22: '수국',
            23: '연꽃',
            24: '나팔꽃',
            25: '목련',
            26: '벚꽃',
            27: '튤립',
        }

    @torch.no_grad()
    def classification(self, src):
        inputs, _ = self.load_image(src)
        output = self.classification_model(inputs)
        prob_with_idx = torch.sort(F.softmax(output))
        result = []
        total = prob_with_idx[0][0][-3:].sum().item()
        for i in range(1, 4):
            prob = prob_with_idx[0][0][-3:][-i].item()
            idx = prob_with_idx[1][0][-3:][-i].item()
            prob_100 = int((prob / total) * 100)
            output = {
                'probability': prob_100,
                'type': self.classes[idx]
            }
            result.append(output)
        return result

    @torch.no_grad()
    def generation(self, src):
        file_name = src.split('/')[-1]
        inputs, size = self.load_image(src)
        inputs = (inputs * 2) - 1
        output = self.generation_model(inputs)
        output = (output + 1) / 2
        output = np.transpose(output[0].detach().numpy(), (1, 2, 0))
        output = cv2.resize(output, (size[0], size[1]), interpolation=cv2.INTER_LINEAR)
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        return cv2.imwrite(f'./picture/{file_name}', (output * 255).astype(np.int32))

    def load_image(self, path):
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        original_size = img.shape
        img = cv2.resize(img, (256, 256))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = torch.Tensor(img / 255.).permute(2, 0, 1)
        return img.unsqueeze(dim=0), original_size


c_weight_path = './ai/weight/mobilenetv3_weight.pt'
c_inference = Inference(c_weight=c_weight_path)


def classify(image_src):
    return c_inference.classification(image_src)


g_weight_path = './ai/weight/generator_weight.pt'
g_inference = Inference(g_weight=g_weight_path)


def generate(image_src):
    return g_inference.generation(image_src)