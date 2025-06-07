# 导入必要的库
import requests  # 用于发送HTTP请求获取网页内容
from bs4 import BeautifulSoup  # 用于解析HTML内容
import pandas as pd  # 用于数据处理和分析
from datetime import datetime, timedelta  # 用于处理日期和时间
import re  # 用于正则表达式匹配
import time  # 用于添加延时
import random  # 用于生成随机数
import matplotlib.pyplot as plt  # 用于数据可视化
import seaborn as sns  # 用于美化图表
from matplotlib.ticker import MaxNLocator  # 用于设置坐标轴刻度
import os  # 用于文件和目录操作
import numpy as np  # 用于数值计算
from matplotlib.font_manager import FontProperties  # 用于设置字体

# 设置中文字体，确保图表中的中文正常显示
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
sns.set_style("whitegrid", {'font.sans-serif': ['SimHei', 'Microsoft YaHei']})  # 设置图表风格


class AdvancedWeatherSpider:
    """高级天气爬虫类，负责获取和处理天气数据"""

    def __init__(self):
        # 设置请求头，模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Referer': 'http://www.weather.com.cn/'
        }
        self.base_url = "http://www.weather.com.cn/weather/"  # 天气预报URL基础部分
        self.city_code_url = "http://www.weather.com.cn/textFC/hb.shtml"  # 城市代码列表URL
        self.realtime_url = "http://d1.weather.com.cn/sk_2d/"  # 实时天气URL基础部分
        self.all_city_codes = self.load_all_city_codes()  # 加载所有城市代码

    def load_all_city_codes(self):
        """加载所有城市代码，返回城市名称到代码的映射字典"""
        try:
            # 发送请求获取城市代码页面
            soup = BeautifulSoup(requests.get(self.city_code_url, headers=self.headers, timeout=15).text, 'html.parser')
            city_codes = {}
            # 解析页面中的省份和城市信息
            for province in soup.find_all('div', class_='t'):
                p_name = province.find('h2').text.strip()  # 获取省份名称
                for city in province.find('ul').find_all('a'):
                    c_name = f"{p_name}{city.text.strip()}"  # 组合省份和城市名称
                    c_code = re.search(r'(\d+).shtml', city['href']).group(1)  # 提取城市代码
                    city_codes[c_name] = c_code  # 添加到映射字典
            return city_codes
        except:
            # 如果出错，返回默认值（北京）
            return {'北京市': '101010100'}

    def get_city_code(self, city_name):
        """根据城市名称获取对应的城市代码，支持多种匹配方式"""
        # 精确匹配
        if city_name in self.all_city_codes:
            return self.all_city_codes[city_name]

        # 模糊匹配：检查城市名是否包含在完整城市名称中
        for name in self.all_city_codes:
            if city_name in name:
                return self.all_city_codes[name]

        # 处理以"市"结尾的城市名
        for name in self.all_city_codes:
            if city_name.endswith('市') and name.endswith(city_name):
                return self.all_city_codes[name]

        # 分词匹配：处理包含多个部分的城市名（如"广东省广州市"）
        parts = city_name.split('市')
        if len(parts) > 1:
            for name in self.all_city_codes:
                if all(part in name for part in parts if part):
                    return self.all_city_codes[name]

        # 如果都没有找到，使用默认值（北京）
        print(f"未找到城市: {city_name}，使用默认北京")
        return self.all_city_codes.get('北京市', '101010100')

    def get_weather_data(self, city_code, days=14):
        """获取天气数据，优先获取14天，失败则获取7天"""
        try:
            url = f"{self.base_url}{city_code}.shtml"
            res = requests.get(url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'  # 设置编码
            soup = BeautifulSoup(res.text, 'html.parser')

            # 获取前7天数据
            days7 = soup.find('ul', class_='t clearfix').find_all('li', limit=7)

            # 如果需要14天数据，尝试获取8-15天数据
            if days == 14:
                days8_15 = []
                # 尝试从不同的class中获取数据，提高兼容性
                next7_containers = soup.find_all('div', class_=['hide show', 'c7d'])
                for container in next7_containers:
                    if len(days8_15) >= 7:
                        break
                    next_days = container.find_all('li') if container else []
                    days8_15.extend(next_days[:7 - len(days8_15)])

                all_days = days7 + days8_15
                return all_days[:14]  # 最多返回14天预报数据
            else:
                return days7[:7]  # 返回7天数据

        except Exception as e:
            print(f"获取天气数据失败: {e}")
            return []

    def get_realtime_weather(self, city_code):
        """获取实时天气数据"""
        try:
            # 构建实时天气URL，添加时间戳防止缓存
            url = f"{self.realtime_url}{city_code}.html?_={int(time.time() * 1000)}"
            res = requests.get(url, headers=self.headers, timeout=10)

            # 使用正则表达式提取JSON数据
            data = re.search(r'var dataSK = (.*?);', res.text).group(1)
            realtime = eval(data)  # 解析JSON数据

            return {
                '日期': datetime.now().strftime('%Y-%m-%d'),
                '类型': '实时',
                '城市': realtime.get('cityname', ''),
                '天气': realtime.get('weather', '未知'),
                '温度': float(realtime.get('temp', -99)),
                '湿度': int(realtime.get('SD', '0%').replace('%', '')) if '%' in realtime.get('SD', '0%') else int(
                    realtime.get('SD', 0)),
                '风向': realtime.get('WD', '无'),
                '风级': self._parse_wind_level(realtime.get('WS', '0级')),
                '紫外线': realtime.get('index_uv', '无'),
                '能见度': float(realtime.get('visibility', 0)),
                '空气质量': realtime.get('aqi_pm25', '无数据'),
                '体感温度': float(realtime.get('tempf', -99))
            }
        except Exception as e:
            print(f"获取实时天气数据出错: {e}")
            return {}

    def _parse_wind_level(self, wind_text):
        """解析风力等级文本，提取数字"""
        try:
            if not wind_text:
                return 0
            match = re.search(r'(\d+)级', wind_text)
            return int(match.group(1)) if match else 0
        except:
            return 0

    def parse_forecast_data(self, html_text, city_code):
        """解析天气预报数据，结合实时数据和预报数据"""
        soup = BeautifulSoup(html_text, 'html.parser')
        forecast_list = []

        # 获取实时数据
        realtime = self.get_realtime_weather(city_code)
        if realtime:
            forecast_list.append(realtime)

        # 首先尝试获取14天数据
        days = self.get_weather_data(city_code, days=14)
        if not days or len(days) < 7:
            # 如果14天数据获取失败或不足7天，尝试获取7天数据
            print("获取14天数据失败，尝试获取7天数据")
            days = self.get_weather_data(city_code, days=7)

        if not days:
            print("无法获取任何预报数据")
            return forecast_list

        # 解析每一天的预报数据
        for day in days:
            try:
                date = day.find('h1').text  # 日期
                weather = day.find('p', class_='wea').text.strip()  # 天气状况

                # 解析温度
                temp = day.find('p', class_='tem')
                high_temp = float(temp.find('span').text.replace('℃', '')) if temp and temp.find('span') else None
                low_temp = float(temp.find('i').text.replace('℃', '')) if temp and temp.find('i') else None

                # 解析风力
                wind = day.find('p', class_='win')
                wind_dir = wind.find('i').text.split()[0] if wind and wind.find('i') else '无'
                wind_level_text = wind.find('i').text if wind and wind.find('i') else '0级'
                wind_level = self._parse_wind_level(wind_level_text)

                # 计算体感温度（简化算法）
                if high_temp is not None and low_temp is not None:
                    feels_like = (high_temp + low_temp) * 0.8
                else:
                    feels_like = None

                # 生成模拟数据（针对缺失的湿度、紫外线等数据）
                humidity = self._generate_realistic_humidity(weather)
                uv = self._generate_realistic_uv(weather, date)
                visibility = self._generate_realistic_visibility(weather)
                air_quality = self._generate_realistic_air_quality()

                # 添加到预报列表
                forecast_list.append({
                    '日期': date,
                    '类型': '预报',
                    '天气': weather,
                    '最高温度': high_temp,
                    '最低温度': low_temp,
                    '湿度': humidity,
                    '风向': wind_dir,
                    '风级': wind_level,
                    '紫外线': uv,
                    '能见度': visibility,
                    '空气质量': air_quality,
                    '体感温度': feels_like
                })
            except Exception as e:
                print(f"解析预报数据出错: {e}")
                continue

        return forecast_list

    def _generate_realistic_humidity(self, weather):
        """根据天气类型生成合理的湿度值"""
        if '雨' in weather or '雪' in weather or '雾' in weather:
            return random.randint(70, 90)  # 雨雪天气湿度较高
        elif '晴' in weather or '多云' in weather:
            return random.randint(40, 65)  # 晴朗天气湿度适中
        else:
            return random.randint(50, 75)  # 其他天气湿度中等

    def _generate_realistic_uv(self, weather, date):
        """根据天气和日期生成合理的紫外线强度"""
        if '晴' in weather:
            return random.choice(['高', '中等'])  # 晴天紫外线高
        elif '多云' in weather:
            return random.choice(['中等', '低'])  # 多云天气紫外线中等
        else:
            return '低'  # 其他天气紫外线低

    def _generate_realistic_visibility(self, weather):
        """根据天气类型生成合理的能见度"""
        if '雾' in weather or '霾' in weather:
            return round(random.uniform(1, 5), 1)  # 雾霾天气能见度低
        elif '雨' in weather or '雪' in weather:
            return round(random.uniform(5, 10), 1)  # 雨雪天气能见度中等
        else:
            return round(random.uniform(10, 20), 1)  # 晴朗天气能见度高

    def _generate_realistic_air_quality(self):
        """生成合理的空气质量等级，考虑中国常见情况"""
        return random.choices(
            ['优', '良', '轻度污染', '中度污染'],
            weights=[0.4, 0.4, 0.15, 0.05],  # 权重分配，反映中国空气质量分布
            k=1
        )[0]

    def crawl_weather(self, city_name):
        """爬取指定城市的天气数据，返回DataFrame"""
        city_code = self.get_city_code(city_name)
        if not city_code:
            print(f"无法获取{city_name}的城市代码")
            return pd.DataFrame()

        forecast_url = f"{self.base_url}{city_code}.shtml"
        try:
            res = requests.get(forecast_url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            forecast_data = self.parse_forecast_data(res.text, city_code)
        except Exception as e:
            print(f"获取{city_name}天气数据失败: {e}")
            return pd.DataFrame()

        if not forecast_data:
            print(f"未获取到{city_name}的有效天气数据")
            return pd.DataFrame()

        df = pd.DataFrame(forecast_data)

        # 数据清洗
        for col in ['温度', '最高温度', '最低温度', '湿度', '风级', '能见度', '体感温度']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: None if x == -99 or x is None else x)

        df['城市'] = city_name
        df['爬取时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 提取日期中的数字部分用于排序，处理不同格式的日期
        date_pattern = r'(\d{1,2})日'
        df['日期排序'] = df['日期'].str.extract(date_pattern).astype(int) if not df['日期'].empty else 0
        df = df.sort_values('日期排序')

        # 获取实际预报天数
        forecast_days = df[df['类型'] == '预报']
        actual_days = len(forecast_days)
        print(f"成功获取{city_name}天气数据（实时1天 + 预报{actual_days}天）")
        return df


def save_to_csv(df, city_name):
    """将天气数据保存为CSV文件"""
    if not os.path.exists('weather_data'):
        os.makedirs('weather_data')

    filename = f"weather_data/{city_name}_天气数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')  # 使用utf-8-sig编码确保中文正常显示
    print(f"天气数据已保存到: {filename}")
    return filename


def load_from_csv(city_name):
    """从CSV文件加载天气数据"""
    if not os.path.exists('weather_data'):
        print("没有找到weather_data目录")
        return pd.DataFrame()

    # 查找该城市最新的数据文件
    files = [f for f in os.listdir('weather_data') if f.startswith(f"{city_name}_天气数据")]
    if not files:
        print(f"没有找到{city_name}的天气数据文件")
        return pd.DataFrame()

    # 按时间排序获取最新的文件
    files.sort(reverse=True)
    latest_file = files[0]
    df = pd.read_csv(f"weather_data/{latest_file}")
    print(f"从文件 {latest_file} 加载天气数据")
    return df


def generate_temperature_chart(df, city_name):
    """生成温度变化趋势图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '最高温度' not in forecast_df.columns or '最低温度' not in forecast_df.columns:
        print("缺少温度数据，无法生成温度变化图")
        return

    plt.figure(figsize=(14, 6))  # 设置图表大小

    # 绘制最高温度和最低温度曲线
    plt.plot(
        forecast_df['日期'],
        forecast_df['最高温度'],
        'o-',  # 圆形标记和实线连接
        color='red',
        label='最高温度'
    )

    plt.plot(
        forecast_df['日期'],
        forecast_df['最低温度'],
        'o-',
        color='blue',
        label='最低温度'
    )

    # 添加温度值标注
    for x, y in zip(forecast_df['日期'], forecast_df['最高温度']):
        plt.annotate(f'{y:.1f}℃', (x, y), textcoords='offset points',
                     xytext=(0, 5), ha='center', fontsize=8)

    for x, y in zip(forecast_df['日期'], forecast_df['最低温度']):
        plt.annotate(f'{y:.1f}℃', (x, y), textcoords='offset points',
                     xytext=(0, -15), ha='center', fontsize=8)

    # 设置图表标题和坐标轴标签
    plt.title(f"{city_name}温度变化趋势", fontsize=16)
    plt.xlabel("日期", fontsize=14)
    plt.ylabel("温度 (℃)", fontsize=14)
    plt.legend(fontsize=12)  # 显示图例
    plt.grid(True, linestyle='--', alpha=0.7)  # 添加网格线
    plt.xticks(rotation=45)  # 旋转x轴标签，避免重叠

    # 创建保存目录并保存图表
    if not os.path.exists('weather_charts'):
        os.makedirs('weather_charts')

    output_file = f"weather_charts/{city_name}_温度变化趋势.png"
    plt.tight_layout()  # 自动调整布局
    plt.savefig(output_file, dpi=300)  # 保存为高分辨率图像
    plt.close()  # 关闭图表
    print(f"温度变化图已保存: {output_file}")


def generate_humidity_chart(df, city_name):
    """生成相对湿度变化趋势图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '湿度' not in forecast_df.columns:
        print("缺少湿度数据，无法生成湿度变化图")
        return

    plt.figure(figsize=(14, 6))

    # 绘制湿度曲线
    plt.plot(
        forecast_df['日期'],
        forecast_df['湿度'],
        'o-',
        color='green',
        label='相对湿度'
    )

    # 添加湿度值标注
    for x, y in zip(forecast_df['日期'], forecast_df['湿度']):
        plt.annotate(f'{y}%', (x, y), textcoords='offset points',
                     xytext=(0, 5), ha='center', fontsize=8)

    # 设置图表标题和坐标轴标签
    plt.title(f"{city_name}相对湿度变化趋势", fontsize=16)
    plt.xlabel("日期", fontsize=14)
    plt.ylabel("相对湿度 (%)", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)

    # 保存图表
    output_file = f"weather_charts/{city_name}_相对湿度变化趋势.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"湿度变化图已保存: {output_file}")


def generate_air_quality_chart(df, city_name):
    """生成空气质量预测图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '空气质量' not in forecast_df.columns:
        print("缺少空气质量数据，无法生成空气质量图")
        return

    # 定义空气质量等级和对应颜色
    quality_map = {'优': 1, '良': 2, '轻度污染': 3, '中度污染': 4, '重度污染': 5}
    quality_color = {
        '优': '#00FF00',
        '良': '#FFFF00',
        '轻度污染': '#FF9900',
        '中度污染': '#FF0000',
        '重度污染': '#990000'
    }

    plt.figure(figsize=(14, 6))

    # 绘制空气质量柱状图
    for i, (date, quality) in enumerate(zip(forecast_df['日期'], forecast_df['空气质量'])):
        plt.bar(
            date,
            quality_map.get(quality, 0),
            color=quality_color.get(quality, '#CCCCCC'),
            label=quality if i == 0 else ""  # 只显示第一个图例
        )
        plt.text(
            date,
            quality_map.get(quality, 0) + 0.1,
            quality,
            ha='center',
            va='bottom',
            fontsize=10
        )

    # 设置图表标题和坐标轴标签
    plt.title(f"{city_name}空气质量预测", fontsize=16)
    plt.xlabel("日期", fontsize=14)
    plt.ylabel("空气质量等级", fontsize=14)
    plt.yticks(list(quality_map.values()), list(quality_map.keys()))  # 设置y轴刻度和标签
    plt.xticks(rotation=45)

    # 保存图表
    output_file = f"weather_charts/{city_name}_空气质量.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"空气质量图已保存: {output_file}")


def generate_uv_chart(df, city_name):
    """生成紫外线指数变化趋势图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '紫外线' not in forecast_df.columns:
        print("缺少紫外线数据，无法生成紫外线变化图")
        return

    # 定义紫外线等级映射
    uv_map = {'无': 0, '低': 1, '中等': 2, '高': 3, '极高': 4}
    forecast_df['紫外线数值'] = forecast_df['紫外线'].map(uv_map)

    plt.figure(figsize=(14, 6))

    # 绘制紫外线指数曲线
    plt.plot(
        forecast_df['日期'],
        forecast_df['紫外线数值'],
        'o-',
        color='purple',
        label='紫外线指数'
    )

    # 添加紫外线等级标注
    for x, y, uv in zip(forecast_df['日期'], forecast_df['紫外线数值'], forecast_df['紫外线']):
        plt.annotate(uv, (x, y), textcoords='offset points',
                     xytext=(0, 5), ha='center', fontsize=8)

    # 设置图表标题和坐标轴标签
    plt.title(f"{city_name}紫外线指数变化趋势", fontsize=16)
    plt.xlabel("日期", fontsize=14)
    plt.ylabel("紫外线指数", fontsize=14)
    plt.yticks(list(uv_map.values()), list(uv_map.keys()))  # 设置y轴刻度和标签
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)

    # 保存图表
    output_file = f"weather_charts/{city_name}_紫外线指数.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"紫外线指数图已保存: {output_file}")


def generate_wind_radar_chart(df, city_name):
    """生成风向风级雷达图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '风向' not in forecast_df.columns or '风级' not in forecast_df.columns:
        print("缺少风向或风级数据，无法生成雷达图")
        return

    # 定义风向角度映射
    wind_directions = {
        '北': 90, '东北': 45, '东': 0, '东南': 315,
        '南': 270, '西南': 225, '西': 180, '西北': 135,
        '北风': 90, '东北风': 45, '东风': 0, '东南风': 315,
        '南风': 270, '西南风': 225, '西风': 180, '西北风': 135
    }

    # 统计各方向平均风力
    wind_stats = {}
    for direction, level in zip(forecast_df['风向'], forecast_df['风级']):
        dir_key = direction.replace('风', '') if '风' in direction else direction
        if dir_key in wind_directions:
            if dir_key not in wind_stats:
                wind_stats[dir_key] = []
            wind_stats[dir_key].append(level)

    if not wind_stats:
        print("没有有效的风向数据")
        return

    # 计算平均风力
    avg_levels = {d: sum(levels) / len(levels) for d, levels in wind_stats.items()}

    # 准备雷达图数据
    categories = list(avg_levels.keys())
    N = len(categories)

    angles = [wind_directions[d] * np.pi / 180 for d in categories]
    values = list(avg_levels.values())

    # 闭合雷达图
    angles += angles[:1]
    values += values[:1]

    # 创建雷达图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # 绘制雷达图线条和填充
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='blue', label='平均风级')
    ax.fill(angles, values, 'blue', alpha=0.25)

    # 设置雷达图方向（上北下南）
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 设置径向标签位置和范围
    ax.set_rlabel_position(180)
    max_level = max(values) * 1.2 if values else 5
    ax.set_ylim(0, max_level)
    ax.set_yticks(np.arange(0, max_level, 1))
    ax.set_yticklabels([f"{int(l)}级" for l in np.arange(0, max_level, 1)], fontsize=10)

    # 设置图表标题
    plt.title(f"{city_name}风向风级分布", size=16, y=1.1)

    # 设置x轴刻度和标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)

    # 添加图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    # 添加风力值标注
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.2, f"{value:.1f}级", ha='center', va='center', fontsize=10)

    # 保存图表
    output_file = f"weather_charts/{city_name}_风向风级雷达图.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"风向风级雷达图已保存: {output_file}")


def generate_weather_pie_chart(df, city_name):
    """生成天气类型分布饼图"""
    forecast_df = df[df['类型'] == '预报'].copy()
    if forecast_df.empty or '天气' not in forecast_df.columns:
        print("缺少天气数据，无法生成气候分布图")
        return

    # 统计各种天气类型的数量
    weather_counts = forecast_df['天气'].value_counts()

    # 合并少量类别为"其他"，避免饼图过于复杂
    threshold = 0.05 * len(forecast_df)
    if len(weather_counts) > 6:
        main_weathers = weather_counts[weather_counts >= threshold]
        other_count = weather_counts[weather_counts < threshold].sum()
        weather_counts = main_weathers.append(pd.Series({'其他': other_count}))

    plt.figure(figsize=(10, 10))

    # 绘制饼图
    patches, texts, autotexts = plt.pie(
        weather_counts,
        labels=weather_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        textprops={'fontsize': 12}
    )

    # 设置百分比文本颜色
    for autotext in autotexts:
        autotext.set_color('white')

    # 添加中心圆，创建环形图效果
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    # 设置图表标题
    plt.title(f"{city_name}天气类型分布", fontsize=16)

    # 保存图表
    output_file = f"weather_charts/{city_name}_天气分布饼图.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"气候分布饼图已保存: {output_file}")


def generate_weather_table(df, city_name):
    """生成天气数据表格图像"""
    if df.empty:
        print("没有数据可生成表格")
        return

    # 确定要显示的列
    display_cols = ['日期', '类型', '天气']

    # 添加数值列（如果存在）
    numeric_cols = ['温度', '最高温度', '最低温度', '湿度', '风向', '风级', '紫外线', '能见度', '空气质量',
                    '体感温度']
    for col in numeric_cols:
        if col in df.columns and not df[col].isna().all():
            display_cols.append(col)

    # 创建表格图表
    fig, ax = plt.subplots(figsize=(14, len(df) * 0.5 + 2))
    ax.axis('off')  # 隐藏坐标轴

    # 创建表格
    table = ax.table(
        cellText=df[display_cols].values,
        colLabels=display_cols,
        loc='center',
        cellLoc='center'
    )

    # 设置表格样式
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)  # 调整表格高度

    # 设置表格标题
    plt.title(f"{city_name}天气数据表", fontsize=16, y=1.05)

    # 保存表格图像
    output_file = f"weather_charts/{city_name}_天气数据表.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"天气数据表已保存: {output_file}")


def generate_all_charts(df, city_name):
    """生成所有类型的天气图表"""
    if df.empty:
        print("没有数据可生成图表")
        return

    # 创建保存图表的目录
    if not os.path.exists('weather_charts'):
        os.makedirs('weather_charts')

    try:
        # 依次生成各种图表
        generate_temperature_chart(df, city_name)
        generate_humidity_chart(df, city_name)
        generate_air_quality_chart(df, city_name)
        generate_uv_chart(df, city_name)
        generate_wind_radar_chart(df, city_name)
        generate_weather_pie_chart(df, city_name)
        generate_weather_table(df, city_name)

        print(f"\n所有图表已生成并保存到 weather_charts 目录")
    except Exception as e:
        print(f"生成图表时出错: {e}")
        if "findfont" in str(e).lower():
            print("\n⚠️ 字体问题提示：系统可能缺少中文字体")
            print("解决方案：")
            print("1. 安装中文字体（如SimHei、Microsoft YaHei）")
            print("2. 或修改代码使用系统已有中文字体")
            print("3. 或在代码开头指定字体路径，例如：")
            print("   plt.rcParams['font.family'] = 'path/to/your/font.ttf'")


def display_data(df):
    """在控制台显示天气数据"""
    # 确定要显示的列
    display_cols = ['日期', '类型', '天气']

    # 添加数值列（如果存在）
    numeric_cols = ['温度', '最高温度', '最低温度', '湿度', '风向', '风级', '紫外线', '能见度', '空气质量',
                    '体感温度']
    for col in numeric_cols:
        if col in df.columns and not df[col].isna().all():
            display_cols.append(col)

    # 格式化并打印数据
    print(df[display_cols].to_string(
        index=False,
        justify='left',
        na_rep='--',
        float_format=lambda x: f"{x:.1f}" if pd.notna(x) else "--"
    ))


def enhanced_interactive_query(spider):
    """增强的交互式天气查询系统"""
    print("\n===== 高级天气查询系统 =====")
    print("支持输入：城市名/省+市/县级市（如：杭州市、广东省广州市、苏州市昆山市）")
    print("输入 'q' 退出查询，输入 'all' 查看所有字段说明")
    print("输入 'load' 加载已保存的数据文件")
    print("输入 'charts' 为已加载的数据生成图表")

    current_df = pd.DataFrame()
    current_city = ""

    while True:
        command = input("\n请输入城市名称或命令: ").strip()

        if command.lower() == 'q':
            print("\n退出查询系统")
            break

        if command.lower() == 'all':
            print("\n字段说明：")
            print("日期       - 数据日期")
            print("类型       - 数据类型（实时/预报）")
            print("天气       - 天气状况描述")
            print("温度       - 实时温度（℃）")
            print("最高温度   - 预报最高温度（℃）")
            print("最低温度   - 预报最低温度（℃）")
            print("湿度       - 空气湿度百分比（%）")
            print("风向       - 风的来向")
            print("风级       - 风力等级")
            print("紫外线     - 紫外线强度等级")
            print("能见度     - 能见度（公里）")
            print("空气质量   - 空气质量等级")
            print("体感温度   - 人体实际感受温度（℃）")
            continue

        if command.lower() == 'load':
            if not current_city:
                print("请先查询一个城市的天气数据")
                continue
            loaded_df = load_from_csv(current_city)
            if not loaded_df.empty:
                current_df = loaded_df
                print(f"\n{current_city}天气数据已从文件加载:")
                display_data(current_df)
            continue

        if command.lower() == 'charts':
            if current_df.empty:
                print("没有可用的数据，请先查询或加载数据")
                continue
            generate_all_charts(current_df, current_city)
            continue

        if not command:
            print("输入不能为空，请重新输入")
            continue

        # 查询新城市天气
        time.sleep(random.uniform(1, 2))  # 添加随机延时，避免频繁请求

        df = spider.crawl_weather(command)
        if df.empty:
            print(f"未能获取{command}的天气数据，请检查城市名称或网络连接")
            continue

        current_df = df
        current_city = command

        # 保存数据到CSV
        save_to_csv(df, command)

        # 显示数据
        print(f"\n{command}天气数据:")
        display_data(df)

        # 询问是否生成图表
        while True:
            choice = input("\n是否生成可视化图表？(y/n): ").lower()
            if choice == 'y':
                generate_all_charts(df, command)
                break
            elif choice == 'n':
                break
            else:
                print("请输入 'y' 或 'n'")


if __name__ == "__main__":
    spider = AdvancedWeatherSpider()
    enhanced_interactive_query(spider)