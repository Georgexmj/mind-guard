from typing import List

from app.models.assessment import QuestionDomain, QuestionType
from app.question_bank_data import QuestionSeed, q


EXTRA_QUESTION_BANK: List[QuestionSeed] = []


def add_choice(
    domain: QuestionDomain,
    content: str,
    options: List[str],
    correct_answer: str,
    difficulty: float = 0.45,
    irt_a: float = 1.1,
    irt_b: float = -0.1,
) -> None:
    EXTRA_QUESTION_BANK.append(
        q(domain, QuestionType.choice, content, options, correct_answer, difficulty, irt_a, irt_b)
    )


def add_voice(
    domain: QuestionDomain,
    content: str,
    difficulty: float = 0.6,
    irt_a: float = 0.9,
    irt_b: float = 0.2,
) -> None:
    EXTRA_QUESTION_BANK.append(
        q(domain, QuestionType.voice, content, None, None, difficulty, irt_a, irt_b)
    )


def add_drawing(
    domain: QuestionDomain,
    content: str,
    difficulty: float = 0.65,
    irt_a: float = 0.9,
    irt_b: float = 0.3,
) -> None:
    EXTRA_QUESTION_BANK.append(
        q(domain, QuestionType.drawing, content, None, None, difficulty, irt_a, irt_b)
    )


def add_scale(
    domain: QuestionDomain,
    content: str,
    difficulty: float = 0.45,
    irt_a: float = 0.8,
    irt_b: float = -0.1,
) -> None:
    EXTRA_QUESTION_BANK.append(
        q(domain, QuestionType.scale, content, None, None, difficulty, irt_a, irt_b)
    )


# ---------------------------------------------------------------------------
# Memory (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.memory,
    "请记住三个词：茶杯、钥匙、雨伞。请问第二个词是什么？",
    ["钥匙", "茶杯", "雨伞", "报纸"],
    "钥匙",
    0.35,
    1.2,
    -0.6,
)
add_choice(
    QuestionDomain.memory,
    "以下哪个词没有出现在“茶杯、钥匙、雨伞”中？",
    ["茶杯", "雨伞", "钥匙", "报纸"],
    "报纸",
    0.45,
    1.1,
    -0.1,
)
add_choice(
    QuestionDomain.memory,
    "请记住三个词：香蕉、镜子、火车。请问第一个词是什么？",
    ["香蕉", "镜子", "火车", "风扇"],
    "香蕉",
    0.35,
    1.2,
    -0.6,
)
add_choice(
    QuestionDomain.memory,
    "以下哪个词没有出现在“香蕉、镜子、火车”中？",
    ["镜子", "火车", "香蕉", "月亮"],
    "月亮",
    0.45,
    1.1,
    -0.1,
)
add_choice(
    QuestionDomain.memory,
    "请记住数字串 4-9-1-7。第三个数字是什么？",
    ["1", "7", "9", "4"],
    "1",
    0.4,
    1.1,
    -0.2,
)
add_choice(
    QuestionDomain.memory,
    "请记住数字串 8-2-6-5。倒数第二个数字是什么？",
    ["2", "6", "5", "8"],
    "6",
    0.45,
    1.1,
    0.0,
)
add_choice(
    QuestionDomain.memory,
    "请记住地址“和平路26号”。请问门牌号是多少？",
    ["26号", "62号", "16号", "206号"],
    "26号",
    0.45,
    1.1,
    0.0,
)
add_choice(
    QuestionDomain.memory,
    "请记住联系人“王阿姨，电话尾号8621”。电话尾号是什么？",
    ["8621", "8261", "8612", "6821"],
    "8621",
    0.5,
    1.0,
    0.1,
)
add_choice(
    QuestionDomain.memory,
    "请记住顺序“春、夏、秋、冬”。第三个词是什么？",
    ["秋", "冬", "夏", "春"],
    "秋",
    0.35,
    1.2,
    -0.4,
)
add_choice(
    QuestionDomain.memory,
    "请记住购物清单“米、油、盐”。以下哪个不在清单中？",
    ["米", "油", "鸡蛋", "盐"],
    "鸡蛋",
    0.45,
    1.0,
    0.0,
)
add_choice(
    QuestionDomain.memory,
    "请记住颜色顺序“蓝、黄、绿、红”。第四个颜色是什么？",
    ["红", "黄", "绿", "蓝"],
    "红",
    0.4,
    1.1,
    -0.2,
)
add_choice(
    QuestionDomain.memory,
    "请记住“公交站在银行南侧”。银行在公交站的哪个方向？",
    ["北侧", "南侧", "东侧", "西侧"],
    "北侧",
    0.55,
    1.0,
    0.2,
)
add_voice(
    QuestionDomain.memory,
    "请在不看提示的情况下，说出刚才出现过的三个词。",
    0.65,
    0.9,
    0.3,
)
add_voice(
    QuestionDomain.memory,
    "请回忆并说出你今天早餐吃了什么（至少两样）。",
    0.6,
    0.8,
    0.2,
)
add_voice(
    QuestionDomain.memory,
    "请复述这句话：今天下午社区活动室有健康讲座。",
    0.55,
    0.9,
    0.1,
)
add_voice(
    QuestionDomain.memory,
    "请说出你昨天晚上最后做的一件事情。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.memory,
    "请听后立即复述这串数字：7-3-9-2-6。",
    0.7,
    0.9,
    0.4,
)
add_voice(
    QuestionDomain.memory,
    "请说出最近一周你忘记带东西的一次经历。",
    0.7,
    0.8,
    0.4,
)
add_scale(
    QuestionDomain.memory,
    "请评估最近一周你忘记约定或事项的频率（0=从不，10=总是）。",
    0.45,
    0.7,
    -0.2,
)
add_scale(
    QuestionDomain.memory,
    "请评估你出门忘带钥匙或手机的情况（0=从不，10=经常）。",
    0.45,
    0.7,
    -0.1,
)
add_choice(
    QuestionDomain.memory,
    "请记住药盒编号“A3B9”。最后一个字符是什么？",
    ["A", "3", "B", "9"],
    "9",
    0.45,
    1.1,
    0.0,
)


# ---------------------------------------------------------------------------
# Orientation (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.orientation,
    "一年通常有几个月？",
    ["12", "10", "11", "13"],
    "12",
    0.25,
    1.3,
    -1.0,
)
add_choice(
    QuestionDomain.orientation,
    "一周通常有几天？",
    ["5", "6", "7", "8"],
    "7",
    0.25,
    1.3,
    -1.0,
)
add_choice(
    QuestionDomain.orientation,
    "24小时制中，下午3点应写作？",
    ["13点", "15点", "17点", "18点"],
    "15点",
    0.35,
    1.2,
    -0.6,
)
add_choice(
    QuestionDomain.orientation,
    "元旦是几月几日？",
    ["1月1日", "5月1日", "10月1日", "12月31日"],
    "1月1日",
    0.3,
    1.2,
    -0.7,
)
add_choice(
    QuestionDomain.orientation,
    "中秋节通常在农历哪一天？",
    ["正月初一", "八月十五", "五月初五", "九月初九"],
    "八月十五",
    0.4,
    1.1,
    -0.2,
)
add_choice(
    QuestionDomain.orientation,
    "如果今天是周三，那么明天是？",
    ["周二", "周三", "周四", "周五"],
    "周四",
    0.35,
    1.2,
    -0.5,
)
add_choice(
    QuestionDomain.orientation,
    "如果今天是4月，下一月是？",
    ["3月", "5月", "6月", "7月"],
    "5月",
    0.3,
    1.2,
    -0.7,
)
add_choice(
    QuestionDomain.orientation,
    "中国使用的标准时区通常是？",
    ["UTC+6", "UTC+7", "UTC+8", "UTC+9"],
    "UTC+8",
    0.35,
    1.1,
    -0.5,
)
add_choice(
    QuestionDomain.orientation,
    "从一楼上到三楼，需要上几层楼？",
    ["1层", "2层", "3层", "4层"],
    "2层",
    0.4,
    1.1,
    -0.2,
)
add_choice(
    QuestionDomain.orientation,
    "公交车站通常属于以下哪类地点？",
    ["住宅卧室", "厨房区域", "公共场所", "私人仓库"],
    "公共场所",
    0.35,
    1.1,
    -0.4,
)
add_choice(
    QuestionDomain.orientation,
    "医院最主要提供的是哪类服务？",
    ["娱乐服务", "医疗服务", "物流服务", "维修服务"],
    "医疗服务",
    0.3,
    1.2,
    -0.6,
)
add_choice(
    QuestionDomain.orientation,
    "身份证最主要的用途是？",
    ["身份识别", "测量血压", "支付电费", "记录步数"],
    "身份识别",
    0.3,
    1.2,
    -0.6,
)
add_voice(
    QuestionDomain.orientation,
    "请说出你当前所在的省、市（或县区）。",
    0.5,
    0.9,
    0.0,
)
add_voice(
    QuestionDomain.orientation,
    "请说出现在是上午、下午还是晚上。",
    0.45,
    1.0,
    -0.1,
)
add_voice(
    QuestionDomain.orientation,
    "请说出你现在所在场所的名称（如家里、社区卫生服务站等）。",
    0.5,
    0.9,
    0.0,
)
add_voice(
    QuestionDomain.orientation,
    "请说出当前季节，并简单描述今天的天气。",
    0.55,
    0.9,
    0.1,
)
add_voice(
    QuestionDomain.orientation,
    "请说出从家到社区门口的大致路线（至少两步）。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.orientation,
    "请说出你所在社区（或小区）的名称。",
    0.5,
    0.9,
    0.0,
)
add_scale(
    QuestionDomain.orientation,
    "你对当前日期和时间的把握程度如何（0=完全不清楚，10=非常清楚）？",
    0.4,
    0.8,
    -0.2,
)
add_scale(
    QuestionDomain.orientation,
    "你外出时对方向和地点的把握程度如何（0=非常差，10=非常好）？",
    0.45,
    0.8,
    -0.1,
)


# ---------------------------------------------------------------------------
# Language (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.language,
    "“高兴”的近义词是哪个？",
    ["难过", "开心", "疲惫", "生气"],
    "开心",
    0.3,
    1.2,
    -0.7,
)
add_choice(
    QuestionDomain.language,
    "“迟到”的反义词是哪个？",
    ["拖延", "准时", "慌张", "拥挤"],
    "准时",
    0.35,
    1.2,
    -0.5,
)
add_choice(
    QuestionDomain.language,
    "成语填空：一心一__",
    ["德", "意", "路", "体"],
    "意",
    0.45,
    1.0,
    -0.1,
)
add_choice(
    QuestionDomain.language,
    "下面哪个词属于水果？",
    ["白菜", "梨", "土豆", "黄瓜"],
    "梨",
    0.3,
    1.2,
    -0.7,
)
add_choice(
    QuestionDomain.language,
    "“医生-医院”与下列哪组关系最相似？",
    ["教师-学校", "司机-车票", "农民-雨伞", "厨师-帽子"],
    "教师-学校",
    0.45,
    1.1,
    0.0,
)
add_choice(
    QuestionDomain.language,
    "“炎热”最常对应哪个季节？",
    ["春天", "夏天", "秋天", "冬天"],
    "夏天",
    0.35,
    1.2,
    -0.6,
)
add_choice(
    QuestionDomain.language,
    "下列哪个词与其他三个不属于同一类？",
    ["桌子", "椅子", "沙发", "苹果"],
    "苹果",
    0.45,
    1.0,
    -0.1,
)
add_choice(
    QuestionDomain.language,
    "句子“雨停了，太阳出来了”的正确先后顺序是？",
    ["先太阳出来，后雨停", "先雨停，后太阳出来", "同时发生", "无法判断"],
    "先雨停，后太阳出来",
    0.5,
    1.0,
    0.1,
)
add_choice(
    QuestionDomain.language,
    "“一__苹果”中最合适的量词是？",
    ["张", "个", "条", "件"],
    "个",
    0.35,
    1.1,
    -0.4,
)
add_choice(
    QuestionDomain.language,
    "“安静”的反义词是哪个？",
    ["平和", "温和", "喧闹", "冷静"],
    "喧闹",
    0.35,
    1.2,
    -0.5,
)
add_voice(
    QuestionDomain.language,
    "请复述这句话：今天下午我们一起去社区活动室做操。",
    0.55,
    0.9,
    0.1,
)
add_voice(
    QuestionDomain.language,
    "请用一句完整的话描述：一位老人正在公园散步。",
    0.55,
    0.8,
    0.2,
)
add_voice(
    QuestionDomain.language,
    "请在30秒内尽可能多地说出蔬菜名称。",
    0.75,
    0.9,
    0.5,
)
add_voice(
    QuestionDomain.language,
    "请按顺序复述这三步：先洗手、再吃饭、最后收拾桌面。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.language,
    "请说出“苹果”和“橙子”的两个共同点。",
    0.6,
    0.9,
    0.2,
)
add_voice(
    QuestionDomain.language,
    "请用“因为……所以……”说一句完整的话。",
    0.6,
    0.8,
    0.2,
)
add_voice(
    QuestionDomain.language,
    "请描述你熟悉的客厅场景，至少说出三样物品及位置。",
    0.7,
    0.8,
    0.4,
)
add_scale(
    QuestionDomain.language,
    "你觉得自己表达想法的清晰程度如何（0=非常困难，10=非常清晰）？",
    0.45,
    0.7,
    -0.2,
)
add_scale(
    QuestionDomain.language,
    "你理解他人讲话内容的难易程度如何（0=非常困难，10=非常容易）？",
    0.45,
    0.7,
    -0.2,
)
add_scale(
    QuestionDomain.language,
    "你最近找词（想说但说不出）的困难程度如何（0=没有困难，10=非常困难）？",
    0.5,
    0.8,
    0.0,
)


# ---------------------------------------------------------------------------
# Attention (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.attention,
    "请计算：100 - 7 = ?",
    ["93", "94", "92", "91"],
    "93",
    0.5,
    1.3,
    0.1,
)
add_choice(
    QuestionDomain.attention,
    "继续计算：93 - 7 = ?",
    ["86", "85", "84", "87"],
    "86",
    0.55,
    1.3,
    0.2,
)
add_choice(
    QuestionDomain.attention,
    "继续计算：86 - 7 = ?",
    ["79", "78", "80", "77"],
    "79",
    0.6,
    1.3,
    0.3,
)
add_choice(
    QuestionDomain.attention,
    "数列 2、4、6、8 的下一个数字是？",
    ["9", "10", "11", "12"],
    "10",
    0.45,
    1.1,
    -0.1,
)
add_choice(
    QuestionDomain.attention,
    "1到30之间有多少个3的倍数？",
    ["8", "9", "10", "11"],
    "10",
    0.55,
    1.1,
    0.1,
)
add_choice(
    QuestionDomain.attention,
    "按从大到小排序，9、2、5 的第一个数字是？",
    ["2", "5", "7", "9"],
    "9",
    0.45,
    1.0,
    -0.1,
)
add_choice(
    QuestionDomain.attention,
    "规则：奇数答“左”，偶数答“右”。数字 5 应答什么？",
    ["左", "右", "停", "中"],
    "左",
    0.55,
    1.1,
    0.1,
)
add_choice(
    QuestionDomain.attention,
    "规则：听到数字“4”拍手。序列“2、4、7、4、1”应拍手几次？",
    ["1次", "2次", "3次", "4次"],
    "2次",
    0.6,
    1.1,
    0.2,
)
add_choice(
    QuestionDomain.attention,
    "20以内的质数有几个？",
    ["7", "8", "9", "10"],
    "8",
    0.65,
    1.1,
    0.3,
)
add_choice(
    QuestionDomain.attention,
    "时钟每走一大格是5分钟。走3大格是几分钟？",
    ["10分钟", "15分钟", "20分钟", "25分钟"],
    "15分钟",
    0.45,
    1.1,
    -0.1,
)
add_voice(
    QuestionDomain.attention,
    "请从20开始倒数到1。",
    0.75,
    0.9,
    0.5,
)
add_voice(
    QuestionDomain.attention,
    "请把月份从12月倒着说到1月。",
    0.75,
    0.9,
    0.5,
)
add_voice(
    QuestionDomain.attention,
    "请把数字“6-1-8-3”倒着说出来。",
    0.65,
    0.9,
    0.3,
)
add_voice(
    QuestionDomain.attention,
    "请先从周一说到周日，再从周日倒着说回周一。",
    0.8,
    0.9,
    0.6,
)
add_voice(
    QuestionDomain.attention,
    "请连续执行三步口令：拍手一次、摸鼻子、说“完成”。",
    0.7,
    0.8,
    0.4,
)
add_voice(
    QuestionDomain.attention,
    "听到“开始”后，间隔3秒再回答“到”。",
    0.65,
    0.8,
    0.3,
)
add_scale(
    QuestionDomain.attention,
    "请评估最近一周你注意力集中的程度（0=完全无法集中，10=始终集中）。",
    0.45,
    0.7,
    -0.2,
)
add_scale(
    QuestionDomain.attention,
    "请评估你做事时容易被打断的程度（0=完全不会，10=非常容易）。",
    0.5,
    0.8,
    0.0,
)
add_scale(
    QuestionDomain.attention,
    "请评估你看电视或读报时走神的频率（0=从不，10=总是）。",
    0.45,
    0.7,
    -0.1,
)
add_scale(
    QuestionDomain.attention,
    "请评估你同时处理两件事时的困难程度（0=毫无困难，10=非常困难）。",
    0.55,
    0.8,
    0.1,
)
add_choice(
    QuestionDomain.attention,
    "请计算：52 + 19 = ?",
    ["69", "70", "71", "72"],
    "71",
    0.45,
    1.1,
    -0.1,
)


# ---------------------------------------------------------------------------
# Visuospatial (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.visuospatial,
    "如果你面朝北方，向右转90度后，面向哪个方向？",
    ["东方", "西方", "南方", "北方"],
    "东方",
    0.5,
    1.1,
    0.0,
)
add_choice(
    QuestionDomain.visuospatial,
    "如果你面朝东方，向左转90度后，面向哪个方向？",
    ["北方", "南方", "西方", "东方"],
    "北方",
    0.5,
    1.1,
    0.0,
)
add_choice(
    QuestionDomain.visuospatial,
    "“书在桌上，桌在地上”，那么“书在地上方”这句话是否正确？",
    ["正确", "错误", "不确定", "无法判断"],
    "正确",
    0.45,
    1.0,
    -0.1,
)
add_choice(
    QuestionDomain.visuospatial,
    "A在B左边，B在C左边，那么A在C的哪边？",
    ["左边", "右边", "上边", "下边"],
    "左边",
    0.55,
    1.1,
    0.1,
)
add_choice(
    QuestionDomain.visuospatial,
    "从家向东到公园，再向北到超市。超市在家的哪个方向？",
    ["东南", "东北", "西南", "西北"],
    "东北",
    0.6,
    1.1,
    0.2,
)
add_choice(
    QuestionDomain.visuospatial,
    "一个正方体有几个面？",
    ["4", "5", "6", "8"],
    "6",
    0.4,
    1.2,
    -0.2,
)
add_choice(
    QuestionDomain.visuospatial,
    "一个长方形有几条边？",
    ["3", "4", "5", "6"],
    "4",
    0.35,
    1.2,
    -0.5,
)
add_choice(
    QuestionDomain.visuospatial,
    "钟表指向3点时，分针通常指向哪个数字？",
    ["3", "6", "9", "12"],
    "12",
    0.4,
    1.1,
    -0.2,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请画一个时钟，并标出8点20分（需包含表盘、数字和指针）。",
    0.7,
    0.9,
    0.4,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请画一个时钟，并标出2点45分（需包含表盘、数字和指针）。",
    0.7,
    0.9,
    0.4,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请临摹两个相互交叉的三角形。",
    0.65,
    0.9,
    0.3,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请临摹一个立方体，尽量画出空间感。",
    0.7,
    0.9,
    0.4,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请按顺序连线：1-A-2-B-3-C-4-D。",
    0.6,
    1.0,
    0.2,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请画一个房子，至少包含屋顶、门和两扇窗。",
    0.6,
    0.9,
    0.2,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请画一个五角星，并在中心画一个小圆点。",
    0.65,
    0.9,
    0.3,
)
add_drawing(
    QuestionDomain.visuospatial,
    "请画一条从左上到右下的对角线，并在右上角画一个小圆。",
    0.6,
    0.9,
    0.2,
)
add_voice(
    QuestionDomain.visuospatial,
    "请回答：杯子在盘子左边，盘子在碗左边，那么杯子在碗的哪边？",
    0.6,
    0.8,
    0.2,
)
add_voice(
    QuestionDomain.visuospatial,
    "请描述你房间里三样物品的相对位置关系。",
    0.65,
    0.8,
    0.3,
)
add_scale(
    QuestionDomain.visuospatial,
    "请评估你识别方向的困难程度（0=无困难，10=非常困难）。",
    0.5,
    0.8,
    0.0,
)
add_scale(
    QuestionDomain.visuospatial,
    "请评估你想象物体位置关系的困难程度（0=无困难，10=非常困难）。",
    0.55,
    0.8,
    0.1,
)
add_choice(
    QuestionDomain.visuospatial,
    "一个正方形旋转90度后，形状会变成什么？",
    ["圆形", "三角形", "仍是正方形", "长方形"],
    "仍是正方形",
    0.45,
    1.1,
    -0.1,
)


# ---------------------------------------------------------------------------
# Executive (20)
# ---------------------------------------------------------------------------
add_choice(
    QuestionDomain.executive,
    "家里闻到燃气味，第一步最合适的是？",
    ["打开明火检查", "先睡一觉", "立即关阀并开窗通风", "继续做饭"],
    "立即关阀并开窗通风",
    0.4,
    1.3,
    -0.3,
)
add_choice(
    QuestionDomain.executive,
    "明天要去医院复诊，今晚最先应做的是？",
    ["先确认身份证和医保卡", "先看电视", "明天再想", "随便带点东西就行"],
    "先确认身份证和医保卡",
    0.4,
    1.2,
    -0.2,
)
add_choice(
    QuestionDomain.executive,
    "如果漏服了一次药，较稳妥的做法是？",
    ["一次补两倍药量", "参考医嘱或咨询医生", "以后不吃了", "随意补服"],
    "参考医嘱或咨询医生",
    0.5,
    1.1,
    0.1,
)
add_choice(
    QuestionDomain.executive,
    "买菜预算60元，青菜18元、鱼22元，还剩多少钱？",
    ["18元", "20元", "22元", "24元"],
    "20元",
    0.5,
    1.1,
    0.1,
)
add_choice(
    QuestionDomain.executive,
    "下雨天外出，最合理的准备是？",
    ["带雨伞或雨衣", "穿拖鞋跑步", "不看天气直接出门", "把钥匙留在家门外"],
    "带雨伞或雨衣",
    0.35,
    1.2,
    -0.5,
)
add_choice(
    QuestionDomain.executive,
    "收到陌生“转账链接”短信时，最安全做法是？",
    ["立即点击", "转发给朋友再点", "先核实来源，不随意点击", "删除手机应用"],
    "先核实来源，不随意点击",
    0.45,
    1.2,
    -0.1,
)
add_choice(
    QuestionDomain.executive,
    "做饭时油锅冒烟，优先应做什么？",
    ["继续加大火", "关小火并注意安全", "往锅里倒很多水", "离开厨房不管"],
    "关小火并注意安全",
    0.45,
    1.2,
    -0.1,
)
add_choice(
    QuestionDomain.executive,
    "第二天要早起办事，前一晚最有效的准备是？",
    ["设闹钟并准备材料", "熬夜看电视", "不做计划", "把手机关机"],
    "设闹钟并准备材料",
    0.35,
    1.2,
    -0.5,
)
add_choice(
    QuestionDomain.executive,
    "正在看电视时到了服药时间，优先应做什么？",
    ["先按时服药", "继续看完再说", "明天一起补服", "不再服药"],
    "先按时服药",
    0.4,
    1.2,
    -0.3,
)
add_choice(
    QuestionDomain.executive,
    "家里突然停电，较合理的第一步是？",
    ["大喊求助", "立刻出门", "检查电闸并联系物业", "点燃纸张照明"],
    "检查电闸并联系物业",
    0.5,
    1.1,
    0.1,
)
add_voice(
    QuestionDomain.executive,
    "请说出“明天去医院复诊”的三步计划。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.executive,
    "请描述你发现忘记关水龙头后会如何处理。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.executive,
    "如果公交车坐过站了，你会怎么做？",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.executive,
    "请说出你明天上午的时间安排（至少三项）。",
    0.7,
    0.8,
    0.4,
)
add_voice(
    QuestionDomain.executive,
    "请说明如何安排“买菜、做饭、吃药”三件事，避免冲突。",
    0.7,
    0.8,
    0.4,
)
add_voice(
    QuestionDomain.executive,
    "请描述遇到陌生人上门推销时，你会怎样应对。",
    0.65,
    0.8,
    0.3,
)
add_voice(
    QuestionDomain.executive,
    "请举例说明你理解的“先重要后紧急”。",
    0.75,
    0.8,
    0.5,
)
add_scale(
    QuestionDomain.executive,
    "请评估你独立规划一天事务的能力（0=完全不能，10=完全可以）。",
    0.5,
    0.8,
    0.0,
)
add_scale(
    QuestionDomain.executive,
    "请评估你处理突发情况的信心（0=完全没有，10=非常有信心）。",
    0.5,
    0.8,
    0.0,
)
add_scale(
    QuestionDomain.executive,
    "请评估你完成多步骤任务的困难程度（0=无困难，10=非常困难）。",
    0.55,
    0.8,
    0.1,
)
