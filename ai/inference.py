from ai.model.classification_model import VGG19
# from ai.model.generation_model import Generator
import torch
import cv2


class Inference:
    def __init__(self, c_weight=None, g_weight=None, num_classes=37):
        self.classification_model = VGG19(num_classes=num_classes).cpu()
        self.classification_model.load_state_dict(torch.load(c_weight, map_location=torch.device('cpu')))
        # self.generation_model = Generator()
        # self.generation_model.load_state_dict(torch.load(g_weight))
        self.classes = {
            0: '얼레지',
            1: '노루귀',
            2: '애기똥풀',
            3: '제비꽃',
            4: '민들레',
            5: '붓꽃',
            6: '할미꽃',
            7: '깽깽이풀',
            8: '삼지구엽초',
            9: '현호색',
            10: '은방울꽃',
            11: '복수초',

            12: '비비추',
            13: '동자꽃',
            14: '곰취',
            15: '패랭이꽃',
            16: '약모밀',
            17: '닭의장풀',
            18: '수련',
            19: '맥문동',
            20: '물봉선',
            21: '엉겅퀴',
            22: '참나리',
            23: '노루오줌',

            24: '구절초',
            25: '꿩의비름',
            26: '투구꽃',
            27: '참취',
            28: '용담',
            29: '마타리',
            30: '국화',
            31: '쑥부쟁이',
            32: '초롱꽃',
            33: '과꽃',
            34: '상사화',

            35: '동백',
            36: '솜다리',
        }

    def classification(self, image_src):
        image = self.load_image(image_src)
        output = self.classification_model(image)
        output_class = int(output.argmax())
        return self.classes[output_class]

    def generation(self, image):
        output = self.generation_model(image)

    def load_image(self, path):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (256, 256))
        img = torch.Tensor(img).permute(2, 0, 1)
        return img.unsqueeze(dim=0)


c_weight_path = './ai/weight/classification_model.pt'
inference = Inference(c_weight=c_weight_path)


def classify(image_src):
    return inference.classification(image_src)

